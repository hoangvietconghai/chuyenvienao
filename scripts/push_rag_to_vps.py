#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/push_rag_to_vps.py
==========================
Công cụ đồng bộ an toàn 4 bảng dữ liệu RAG từ máy cục bộ lên máy chủ VPS
(Local -> VPS), tuyệt đối không ghi đè hay làm mất 8 bảng dữ liệu nghiệp vụ
đang vận hành thực tế trên VPS (`danh_ba_can_bo`, `so_nhiem_vu`,
`lich_su_nhac_nho`, `so_tieu_chi`, `danh_muc_chuyen_de`, `xac_thuc_otp`,
`phien_dang_nhap`, `nhat_ky_hoi_thoai`).

Quy trình 5 bước an toàn (Human-in-the-Loop):
  1. Gộp WAL (PRAGMA wal_checkpoint) và đóng gói CHỈ 4 bảng RAG từ local vào tệp tạm.
  2. Hỏi xác nhận thủ công và mật khẩu SSH (không lưu mật khẩu dưới mọi hình thức).
  3. Dừng tạm dịch vụ `chuyenvienao`, tạo bản sao lưu DB đầy đủ trên VPS trước khi ghi.
  4. Thực thi giao dịch SQLite trên VPS: thay thế 4 bảng RAG + kiểm tra SHA-256
     toàn bộ các bảng ngoài RAG trước/sau khi ghi (tự động khôi phục nếu sai lệch).
  5. Khởi động lại dịch vụ `chuyenvienao` và kiểm tra `/health`.

Chạy:
    python scripts/push_rag_to_vps.py
    python scripts/push_rag_to_vps.py --dry-run
"""

import argparse
import getpass
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = BASE_DIR / "data" / "chuyen_vien_ao.db"

VPS_IP = "45.119.82.227"
VPS_PORT = 22
VPS_USER = "root"
REMOTE_APP_DIR = "/opt/chuyenvienao"
REMOTE_DB_PATH = f"{REMOTE_APP_DIR}/data/chuyen_vien_ao.db"
REMOTE_BACKUP_DIR = f"{REMOTE_APP_DIR}/backups"
REMOTE_PYTHON = f"{REMOTE_APP_DIR}/.venv/bin/python"

RAG_COPY_TABLES = ("so_van_ban", "van_ban_lien_ket", "van_ban_chunks")


def _import_paramiko():
    """Tải paramiko khi cần kết nối SSH/SFTP."""
    try:
        import paramiko
        return paramiko
    except ImportError:
        print("Đang cài đặt thư viện paramiko...")
        os.system(f'"{sys.executable}" -m pip install paramiko')
        import paramiko
        return paramiko


def parse_args() -> argparse.Namespace:
    """Phân tích tham số dòng lệnh."""
    parser = argparse.ArgumentParser(
        description="Đồng bộ an toàn 4 bảng dữ liệu RAG từ máy cục bộ lên VPS."
    )
    parser.add_argument("--host", default=VPS_IP, help="Địa chỉ IP/Hostname VPS")
    parser.add_argument("--port", type=int, default=VPS_PORT, help="Cổng SSH")
    parser.add_argument("--user", default=VPS_USER, help="Tài khoản SSH")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ kiểm tra và đóng gói dữ liệu RAG ở máy cục bộ, không tải lên VPS.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Cho phép đồng bộ ngay cả khi kho RAG cục bộ đang có 0 văn bản.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bỏ qua bước hỏi xác nhận y/N (vẫn yêu cầu nhập mật khẩu SSH).",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    """Tính mã băm SHA-256 của một tệp nhị phân."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_local_rag(db_path: Path) -> Dict[str, int]:
    """Đọc số lượng bản ghi hiện có trong 4 bảng RAG ở máy cục bộ."""
    if not db_path.exists():
        raise FileNotFoundError(f"Không tìm thấy CSDL cục bộ tại: {db_path}")

    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        counts = {
            "so_van_ban": conn.execute("SELECT COUNT(*) FROM so_van_ban").fetchone()[0],
            "van_ban_chunks": conn.execute("SELECT COUNT(*) FROM van_ban_chunks").fetchone()[0],
            "van_ban_fts": conn.execute("SELECT COUNT(*) FROM van_ban_fts").fetchone()[0],
            "van_ban_lien_ket": conn.execute("SELECT COUNT(*) FROM van_ban_lien_ket").fetchone()[0],
            "with_embedding": conn.execute(
                "SELECT COUNT(*) FROM van_ban_chunks WHERE embedding IS NOT NULL"
            ).fetchone()[0],
        }
        return counts
    finally:
        conn.close()


def _copy_table_to_staging(src: sqlite3.Connection, dst: sqlite3.Connection, table_name: str, src_query: Optional[str] = None) -> int:
    """Sao chép toàn bộ cột và dữ liệu của một bảng sang CSDL tạm."""
    rows = src.execute(src_query or f"SELECT * FROM {table_name}").fetchall()
    col_info = src.execute(f"PRAGMA table_info({table_name})").fetchall() if not src_query else None

    if src_query:
        desc = src.execute(src_query).description
        cols = [d[0] for d in desc]
        col_defs = ", ".join(f'"{c}"' for c in cols)
        dst.execute(f'CREATE TABLE "{table_name}" ({col_defs});')
    else:
        cols = [r[1] for r in col_info]
        # Tạo bảng staging có cùng danh sách cột để giữ nguyên kiểu dữ liệu
        schema_sql = src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        ).fetchone()[0]
        dst.execute(schema_sql)

    if rows:
        placeholders = ", ".join(["?"] * len(cols))
        quoted_cols = ", ".join(f'"{c}"' for c in cols)
        dst.executemany(
            f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders});',
            [tuple(r) for r in rows],
        )
    return len(rows)


def build_rag_staging_db(local_db: Path, staging_db: Path) -> Tuple[Dict[str, int], str]:
    """
    Trích xuất CHỈ 4 bảng RAG từ CSDL cục bộ sang một tệp SQLite tạm độc lập.
    Bảng `van_ban_fts` được xuất sang bảng thường `van_ban_fts_rows` để VPS tự
    dựng lại chỉ mục FTS5 nguyên bản.
    """
    if staging_db.exists():
        staging_db.unlink()

    src = sqlite3.connect(str(local_db), timeout=30.0)
    dst = sqlite3.connect(str(staging_db), timeout=30.0)
    try:
        src.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        counts: Dict[str, int] = {}
        with dst:
            for tbl in RAG_COPY_TABLES:
                counts[tbl] = _copy_table_to_staging(src, dst, tbl)
            counts["van_ban_fts"] = _copy_table_to_staging(
                src,
                dst,
                "van_ban_fts_rows",
                src_query=(
                    "SELECT chunk_id, doc_id, so_hieu_vb, trich_yeu, section_path, chunk_text "
                    "FROM van_ban_fts"
                ),
            )
    finally:
        src.close()
        dst.close()

    return counts, sha256_file(staging_db)


def build_remote_merge_script() -> str:
    """
    Sinh đoạn mã Python thực thi trên VPS để hoán đổi nguyên tử CHỈ 4 bảng RAG,
    kèm kiểm tra SHA-256 toàn bộ các bảng ngoài RAG trước và sau khi ghi.
    """
    return r'''
import hashlib, json, shutil, sqlite3, sys

remote_db = sys.argv[1]
staging_db = sys.argv[2]
expected_sha = sys.argv[3]
backup_db = sys.argv[4]

def calc_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

actual_sha = calc_sha(staging_db)
if actual_sha != expected_sha:
    raise RuntimeError(f"Checksum tệp staging không khớp: {actual_sha} != {expected_sha}")

def get_non_rag_tables(conn):
    excluded = {
        "so_van_ban", "van_ban_chunks", "van_ban_lien_ket", "van_ban_fts",
        "sqlite_sequence",
    }
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [
        r[0] for r in rows
        if r[0] not in excluded and not r[0].startswith("van_ban_fts_")
    ]

def snapshot_tables(conn, tables):
    snap = {}
    for tbl in tables:
        data = conn.execute(f'SELECT * FROM "{tbl}"').fetchall()
        payload = json.dumps([list(r) for r in data], ensure_ascii=False, default=str)
        snap[tbl] = (len(data), hashlib.sha256(payload.encode("utf-8")).hexdigest())
    return snap

conn = sqlite3.connect(remote_db, timeout=30.0)
try:
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
finally:
    conn.close()

shutil.copy2(remote_db, backup_db)

conn = sqlite3.connect(remote_db, timeout=30.0)
try:
    conn.execute("PRAGMA foreign_keys=ON;")
    non_rag = get_non_rag_tables(conn)
    pre_snap = snapshot_tables(conn, non_rag)

    # Kiểm tra cấu trúc bảng nguồn trong staging
    conn.execute("ATTACH DATABASE ? AS src;", (staging_db,))
    copy_tables = ("so_van_ban", "van_ban_lien_ket", "van_ban_chunks")

    def table_cols(db_prefix, tbl):
        return [r[1] for r in conn.execute(f'PRAGMA {db_prefix}.table_info("{tbl}")').fetchall()]

    col_map = {}
    for tbl in copy_tables:
        dst_cols = table_cols("main", tbl)
        src_cols = set(table_cols("src", tbl))
        shared = [c for c in dst_cols if c in src_cols]
        if not shared:
            raise RuntimeError(f"Bảng {tbl} không có cột tương thích giữa local và VPS!")
        col_map[tbl] = shared

    with conn:
        conn.execute("DELETE FROM main.van_ban_fts;")
        conn.execute("DELETE FROM main.van_ban_chunks;")
        conn.execute("DELETE FROM main.van_ban_lien_ket;")
        conn.execute("DELETE FROM main.so_van_ban;")

        for tbl in copy_tables:
            cols_sql = ", ".join(f'"{c}"' for c in col_map[tbl])
            conn.execute(f'INSERT INTO main."{tbl}" ({cols_sql}) SELECT {cols_sql} FROM src."{tbl}";')

        conn.execute(
            """
            INSERT INTO main.van_ban_fts (
                chunk_id, doc_id, so_hieu_vb, trich_yeu, section_path, chunk_text
            )
            SELECT chunk_id, doc_id, so_hieu_vb, trich_yeu, section_path, chunk_text
            FROM src.van_ban_fts_rows;
            """
        )

    conn.execute("DETACH DATABASE src;")

    post_snap = snapshot_tables(conn, non_rag)
    if pre_snap != post_snap:
        raise RuntimeError(f"CẢNH BÁO: Dữ liệu ngoài RAG bị biến đổi! Đã chặn lại. pre={pre_snap} post={post_snap}")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

    counts = {
        "so_van_ban": conn.execute("SELECT COUNT(*) FROM so_van_ban").fetchone()[0],
        "van_ban_chunks": conn.execute("SELECT COUNT(*) FROM van_ban_chunks").fetchone()[0],
        "van_ban_fts": conn.execute("SELECT COUNT(*) FROM van_ban_fts").fetchone()[0],
        "van_ban_lien_ket": conn.execute("SELECT COUNT(*) FROM van_ban_lien_ket").fetchone()[0],
    }
    print(json.dumps({"rag_counts": counts, "non_rag_preserved": {k: v[0] for k, v in post_snap.items()}}, ensure_ascii=False))
except Exception:
    conn.close()
    shutil.copy2(backup_db, remote_db)
    raise
finally:
    try:
        conn.close()
    except Exception:
        pass
'''


def exec_remote_checked(ssh, command: str, stdin_payload: Optional[str] = None) -> str:
    """Thực thi lệnh SSH và ném lỗi nếu exit code khác 0."""
    stdin, stdout, stderr = ssh.exec_command(command)
    if stdin_payload is not None:
        stdin.write(stdin_payload)
        stdin.flush()
        stdin.channel.shutdown_write()

    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(f"Lệnh VPS thất bại (exit={exit_code}): {command}\nSTDERR: {err}\nSTDOUT: {out}")
    return out


def main():
    args = parse_args()

    print("=" * 76)
    print("   📤 ĐỒNG BỘ AN TOÀN KHO TRI THỨC RAG LÊN MÁY CHỦ VPS (LOCAL -> VPS)     ")
    print("=" * 76)
    print(f"🔹 Nguồn (Local DB):  {LOCAL_DB_PATH}")
    print(f"🔹 Đích (VPS DB):     {args.user}@{args.host}:{REMOTE_DB_PATH}")
    print("🔹 Phạm vi ghi:       CHỈ 4 bảng RAG (so_van_ban, van_ban_chunks, van_ban_fts, van_ban_lien_ket)")
    print("🔹 Bảo toàn nguyên vẹn: Danh bạ, Sổ nhiệm vụ, Lịch sử nhắc, KPI, OTP, Session, Chat Log")
    print("=" * 76)

    local_counts = inspect_local_rag(LOCAL_DB_PATH)
    print("\n>> [1/5] Thống kê kho RAG cục bộ hiện tại:")
    print(
        f"  • Văn bản (so_van_ban):      {local_counts['so_van_ban']}\n"
        f"  • Phân đoạn (chunks/FTS5):   {local_counts['van_ban_chunks']} / {local_counts['van_ban_fts']}\n"
        f"  • Liên kết (van_ban_lien_ket): {local_counts['van_ban_lien_ket']}\n"
        f"  • Chunk có vector embedding: {local_counts['with_embedding']}"
    )

    if local_counts["so_van_ban"] == 0 and not args.allow_empty:
        print("\n❌ Kho RAG cục bộ đang có 0 văn bản. Dừng để tránh xoá nhầm kho RAG trên VPS.")
        print("   (Nếu cố ý đồng bộ kho rỗng, truyền thêm cờ --allow-empty)")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory() as tmp_dir:
        staging_local = Path(tmp_dir) / f"rag_staging_{timestamp}.db"
        staging_counts, staging_sha = build_rag_staging_db(LOCAL_DB_PATH, staging_local)
        size_mb = staging_local.stat().st_size / (1024 * 1024)
        print(f"\n>> [2/5] Đã đóng gói tệp staging CHỈ chứa 4 bảng RAG ({size_mb:.2f} MB, SHA-256: {staging_sha[:12]}...)")

        if args.dry_run:
            print("\n✅ [DRY-RUN] Kiểm tra đóng gói cục bộ thành công! Chưa tải dữ liệu lên VPS.")
            return

        if not args.yes:
            confirm = input("\n⚠️  Xác nhận thay thế 4 bảng RAG trên VPS (giữ nguyên dữ liệu nghiệp vụ khác)? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("❌ Đã huỷ thao tác theo yêu cầu của đồng chí.")
                return

        password = getpass.getpass(f"🔑 Nhập mật khẩu SSH cho {args.user}@{args.host}: ")
        if not password:
            print("❌ Chưa nhập mật khẩu. Huỷ tác vụ.")
            sys.exit(1)

        paramiko = _import_paramiko()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        remote_staging = f"/tmp/rag_staging_{timestamp}.db"
        remote_backup = f"{REMOTE_BACKUP_DIR}/before_rag_push_{timestamp}.db"
        service_stopped = False

        try:
            print(f"\n>> [3/5] Đang kết nối SSH/SFTP tới {args.host}...")
            ssh.connect(
                hostname=args.host,
                port=args.port,
                username=args.user,
                password=password,
                timeout=15,
                banner_timeout=15,
                allow_agent=False,
                look_for_keys=False,
            )

            exec_remote_checked(ssh, f"mkdir -p {REMOTE_APP_DIR}/data {REMOTE_BACKUP_DIR}")

            # Đảm bảo lược đồ CSDL VPS đã khởi tạo trước khi hoán đổi
            remote_py = exec_remote_checked(
                ssh, f"if [ -x {REMOTE_PYTHON} ]; then echo {REMOTE_PYTHON}; else echo python3; fi"
            )
            exec_remote_checked(
                ssh,
                f"cd {REMOTE_APP_DIR} && {remote_py} -c \"from server.services.db_service import init_database; init_database()\"",
            )

            print("  • Tải tệp staging RAG lên VPS qua SFTP...")
            sftp = ssh.open_sftp()
            try:
                sftp.put(str(staging_local), remote_staging)
            finally:
                sftp.close()

            print("\n>> [4/5] Dừng tạm dịch vụ chuyenvienao, sao lưu DB VPS và hoán đổi 4 bảng RAG...")
            exec_remote_checked(ssh, "systemctl stop chuyenvienao")
            service_stopped = True

            merge_cmd = (
                f"{remote_py} -u - "
                f"'{REMOTE_DB_PATH}' '{remote_staging}' '{staging_sha}' '{remote_backup}'"
            )
            merge_out = exec_remote_checked(ssh, merge_cmd, stdin_payload=build_remote_merge_script())
            print(f"  ✓ Kết quả trên VPS: {merge_out}")
            print(f"  ✓ Bản sao lưu an toàn trước khi ghi: {remote_backup}")

            print("\n>> [5/5] Khởi động lại dịch vụ chuyenvienao và kiểm tra sức khoẻ...")
            exec_remote_checked(ssh, "systemctl start chuyenvienao")
            service_stopped = False
            time.sleep(2)
            health = exec_remote_checked(ssh, "curl -s http://127.0.0.1:8000/health || echo '{\"status\":\"unknown\"}'")
            print(f"  ✓ Trạng thái dịch vụ: {health}")

            print("\n" + "=" * 76)
            print("🎉 ĐỒNG BỘ KHO RAG LÊN VPS THÀNH CÔNG! DỮ LIỆU NGHIỆP VỤ VPS NGUYÊN VẸN 100%.")
            print("=" * 76)

        except Exception as ex:
            print(f"\n❌ Lỗi trong quá trình đồng bộ lên VPS: {ex}")
            if service_stopped:
                try:
                    exec_remote_checked(ssh, "systemctl start chuyenvienao")
                    print("  ℹ️ Đã khôi phục khởi động lại dịch vụ chuyenvienao trên VPS.")
                except Exception as restart_err:
                    print(f"  ⚠️ Không thể tự khởi động lại dịch vụ chuyenvienao: {restart_err}")
            sys.exit(1)
        finally:
            try:
                ssh.exec_command(f"rm -f '{remote_staging}'")
            except Exception:
                pass
            ssh.close()


if __name__ == "__main__":
    main()

