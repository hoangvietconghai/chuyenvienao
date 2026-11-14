#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
log_guinhan.py
==============
Công cụ Giám sát & Tra cứu Nhật ký Gửi - Nhận giữa Cán bộ và Chuyên viên ảo AI.
Hỗ trợ xem trực tiếp CSDL Local và máy chủ VPS 45.119.82.227.

Cách dùng:
    python log_guinhan.py                # Xem 10 lượt gửi - nhận gần nhất
    python log_guinhan.py -n 20           # Xem 20 lượt gần nhất
    python log_guinhan.py -d 15           # Xem chi tiết toàn văn lượt số 15
    python log_guinhan.py -s "nq 11"      # Tìm kiếm theo từ khoá
    python log_guinhan.py -f              # Theo dõi trực tiếp thời gian thực (Live Tail)
    python log_guinhan.py --vps           # Xem nhật ký trực tiếp từ máy chủ VPS
    python log_guinhan.py --channel zalo  # Lọc riêng các tin nhắn qua Bot Zalo
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Cấu hình UTF-8 cho Windows Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = BASE_DIR / "data" / "chuyen_vien_ao.db"

VPS_IP = "45.119.82.227"
VPS_PORT = 22
VPS_USER = "root"
REMOTE_DB_PATH = "/opt/chuyenvienao/data/chuyen_vien_ao.db"

# Màu ANSI terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def get_local_connection() -> sqlite3.Connection:
    if not LOCAL_DB_PATH.exists():
        print(f"{RED}Không tìm thấy CSDL tại {LOCAL_DB_PATH}{RESET}")
        sys.exit(1)
    conn = sqlite3.connect(str(LOCAL_DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def format_rag_sources(raw_sources: str) -> str:
    """Định dạng danh sách văn bản RAG đã nạp vào ngữ cảnh."""
    if not raw_sources or not raw_sources.strip():
        return f"{DIM}(Không dùng RAG / Trò chuyện tự do hoặc nghiệp vụ xuất Word){RESET}"
    try:
        data = json.loads(raw_sources)
        if isinstance(data, list) and data:
            lines = []
            for idx, item in enumerate(data, 1):
                so = item.get("so_hieu", "")
                tier = item.get("tier", "NỀN TẢNG")
                trich_yeu = item.get("trich_yeu", "")
                badge_color = GREEN if "NỀN" in tier else (YELLOW if "CHUYÊN" in tier else BLUE)
                lines.append(f"     {idx}. {BOLD}{so}{RESET} [{badge_color}{tier}{RESET}]: {trich_yeu[:90]}{'...' if len(trich_yeu) > 90 else ''}")
            return "\n".join(lines)
    except Exception:
        pass
    return f"     {raw_sources[:150]}"


def render_record(r: Dict[str, Any], detail: bool = False):
    """Hiển thị 1 bản ghi gửi - nhận theo khung giao diện chuẩn."""
    rec_id = r.get("id")
    created_at = r.get("created_at", "")
    ho_ten = r.get("ho_ten") or "Khách"
    vai_tro = r.get("vai_tro") or "can_bo"
    co_quan = r.get("co_quan") or ""
    channel = (r.get("channel") or "web").upper()
    model = r.get("model_used") or "gemini-3.5-flash-lite"
    latency = r.get("latency_ms") or 0
    msg = r.get("message_text") or ""
    reply = r.get("bot_reply") or ""
    rag = r.get("rag_sources") or ""

    channel_color = GREEN if channel == "WEB" else BLUE
    role_color = MAGENTA if "admin" in vai_tro.lower() else YELLOW

    print(f"\n{BOLD}{'═' * 80}{RESET}")
    print(
        f"{BOLD}[ID: {rec_id:04d}]{RESET} 🕒 {CYAN}{created_at}{RESET} │ "
        f"👤 {BOLD}{ho_ten}{RESET} ({role_color}{vai_tro}{RESET}{f' - {co_quan}' if co_quan else ''}) │ "
        f"🌐 Kênh: {channel_color}{channel}{RESET}"
    )
    print(
        f"⚡ Thời gian phản hồi: {GREEN}{latency:,}ms{RESET} │ "
        f"🤖 Động cơ: {BOLD}{model}{RESET}"
    )
    print(f"{DIM}{'─' * 80}{RESET}")

    # Phần 1: Câu hỏi của cán bộ (Gửi đi)
    print(f"{YELLOW}{BOLD}❓ GỬI ĐI (CÂU HỎI CỦA CÁN BỘ):{RESET}")
    if detail:
        print(f"   {msg.strip()}")
    else:
        preview_msg = msg.strip()[:300]
        suffix = " ... [Gõ -d {0} để xem toàn văn]".format(rec_id) if len(msg.strip()) > 300 else ""
        print(f"   {preview_msg}{suffix}")

    # Phần 2: Dữ liệu thực chứng RAG nạp vào
    print(f"\n{CYAN}{BOLD}📚 DỮ LIỆU THỰC CHỨNG RAG ĐÃ NẠP VÀO NGỮ CẢNH:{RESET}")
    print(format_rag_sources(rag))

    # Phần 3: Phản hồi của AI (Nhận về)
    print(f"\n{GREEN}{BOLD}💬 PHẢN HỒI CỦA CHUYÊN VIÊN ẢO (AI TRẢ LỜI):{RESET}")
    if detail:
        print(f"   {reply.strip()}")
    else:
        preview_reply = reply.strip()[:400]
        suffix = f" ... {DIM}[Còn tiếp, gõ -d {rec_id} để xem trọn vẹn]{RESET}" if len(reply.strip()) > 400 else ""
        print(f"   {preview_reply}{suffix}")

    print(f"{BOLD}{'═' * 80}{RESET}")


def fetch_local_logs(limit: int = 10, search: Optional[str] = None, channel: Optional[str] = None, record_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_local_connection()
    cursor = conn.cursor()

    # Tự động đảm bảo cột rag_sources tồn tại
    cursor.execute("PRAGMA table_info(nhat_ky_hoi_thoai);")
    cols = {r["name"] for r in cursor.fetchall()}
    rag_col_expr = "rag_sources" if "rag_sources" in cols else "'' AS rag_sources"

    conditions = []
    params: List[Any] = []

    if record_id is not None:
        conditions.append("id = ?")
        params.append(record_id)
    else:
        if channel:
            conditions.append("LOWER(channel) = ?")
            params.append(channel.lower().strip())
        if search:
            kw = f"%{search.strip().lower()}%"
            conditions.append("(LOWER(message_text) LIKE ? OR LOWER(bot_reply) LIKE ? OR LOWER(ho_ten) LIKE ?)")
            params.extend([kw, kw, kw])

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT 
            id, session_id, channel, can_bo_id, so_dien_thoai, ho_ten, co_quan, vai_tro,
            message_text, attachment_names, bot_reply, model_used, latency_ms, created_at,
            {rag_col_expr}
        FROM nhat_ky_hoi_thoai
        {where_sql}
        ORDER BY id DESC
        LIMIT ?;
    """
    params.append(limit)
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_vps_logs(limit: int = 10, search: Optional[str] = None, channel: Optional[str] = None, record_id: Optional[int] = None):
    """Kết nối SSH lên VPS 45.119.82.227 để đọc trực tiếp nhật ký gửi nhận."""
    try:
        import paramiko
    except ImportError:
        print(f"{RED}Chưa cài đặt thư viện paramiko. Chạy: pip install paramiko{RESET}")
        return

    import getpass
    print(f"{CYAN}Đang chuẩn bị kết nối tới VPS: {VPS_USER}@{VPS_IP}:{VPS_PORT}...{RESET}")
    ssh_key_path = Path.home() / ".ssh" / "id_rsa"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connected = False
    if ssh_key_path.exists():
        try:
            ssh.connect(VPS_IP, port=VPS_PORT, username=VPS_USER, key_filename=str(ssh_key_path), timeout=5.0)
            connected = True
            print(f"{GREEN}✓ Đã xác thực thành công qua SSH Key!{RESET}")
        except Exception:
            pass

    if not connected:
        try:
            pwd = getpass.getpass(f"Nhập mật khẩu SSH của {VPS_USER}@{VPS_IP}: ")
            ssh.connect(VPS_IP, port=VPS_PORT, username=VPS_USER, password=pwd, timeout=10.0)
            connected = True
            print(f"{GREEN}✓ Đã đăng nhập SSH thành công!{RESET}")
        except Exception as e:
            print(f"{RED}Không thể kết nối SSH tới VPS: {e}{RESET}")
            return

    # Lệnh Python chạy trên VPS để trích xuất JSON
    remote_script = f"""
import sqlite3, json, sys
conn = sqlite3.connect('{REMOTE_DB_PATH}')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(nhat_ky_hoi_thoai);")
cols = [r[1] for r in cursor.fetchall()]
rag_col = "rag_sources" if "rag_sources" in cols else "'' AS rag_sources"

sql = f"SELECT id, session_id, channel, can_bo_id, so_dien_thoai, ho_ten, co_quan, vai_tro, message_text, attachment_names, bot_reply, model_used, latency_ms, created_at, {{rag_col}} FROM nhat_ky_hoi_thoai ORDER BY id DESC LIMIT {limit};"
cursor.execute(sql)
rows = [dict(r) for r in cursor.fetchall()]
print(json.dumps(rows, ensure_ascii=False))
"""
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{remote_script}\"")
    output = stdout.read().decode("utf-8")
    err = stderr.read().decode("utf-8")
    ssh.close()

    if err and not output:
        print(f"{RED}Lỗi truy vấn trên VPS: {err}{RESET}")
        return

    try:
        rows = json.loads(output)
        if not rows:
            print(f"{YELLOW}Không có bản ghi nhật ký nào trên VPS.{RESET}")
            return
        print(f"\n{GREEN}{BOLD}ĐÃ LẤY ĐƯỢC {len(rows)} BẢN GHI TỪ MÁY CHỦ VPS ({VPS_IP}):{RESET}")
        for r in reversed(rows):
            render_record(r, detail=(record_id is not None))
    except Exception as ex:
        print(f"{RED}Lỗi phân tích dữ liệu từ VPS: {ex}\nOutput thô: {output[:300]}{RESET}")


def run_continuous_follow(channel: Optional[str] = None):
    """Chế độ Live Tail: tự động theo dõi tin nhắn mới mỗi 2 giây."""
    print(f"{CYAN}{BOLD}BẮT ĐẦU CHẾ ĐỘ THEO DÕI TRỰC TIẾP (LIVE TAIL)...{RESET}")
    print(f"{DIM}Nhấn Ctrl + C để thoát.{RESET}\n")
    seen_ids = set()

    # Nạp các ID hiện tại để không in lại tin cũ
    init_rows = fetch_local_logs(limit=20, channel=channel)
    for r in init_rows:
        seen_ids.add(r["id"])

    if init_rows:
        print(f"{GREEN}✓ Đã đồng bộ trạng thái ban đầu ({len(seen_ids)} tin nhắn). Đang lắng nghe tin nhắn mới...{RESET}")
    else:
        print(f"{GREEN}✓ Chưa có tin nhắn nào. Đang lắng nghe...{RESET}")

    try:
        while True:
            time.sleep(2.0)
            rows = fetch_local_logs(limit=10, channel=channel)
            new_records = [r for r in rows if r["id"] not in seen_ids]
            if new_records:
                for r in reversed(new_records):
                    seen_ids.add(r["id"])
                    print(f"\a")  # Beep nhẹ báo hiệu tin nhắn mới
                    render_record(r, detail=False)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Đã dừng chế độ theo dõi.{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Công cụ Giám sát Nhật ký Gửi - Nhận Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải."
    )
    parser.add_argument("-n", "--limit", type=int, default=10, help="Số lượng lượt gửi nhận cần xem (mặc định: 10)")
    parser.add_argument("-d", "--detail", type=int, default=None, help="Xem chi tiết toàn văn lượt gửi nhận theo ID")
    parser.add_argument("-s", "--search", type=str, default=None, help="Tìm kiếm theo từ khoá (câu hỏi, câu trả lời, tên cán bộ)")
    parser.add_argument("-c", "--channel", type=str, default=None, choices=["web", "zalo"], help="Lọc riêng theo kênh: web hoặc zalo")
    parser.add_argument("-f", "--follow", action="store_true", help="Chế độ theo dõi trực tiếp thời gian thực (Live Tail)")
    parser.add_argument("--vps", action="store_true", help="Xem nhật ký trực tiếp từ máy chủ VPS (45.119.82.227)")

    args = parser.parse_args()

    # 1. Chế độ xem VPS
    if args.vps:
        fetch_vps_logs(limit=args.limit, search=args.search, channel=args.channel, record_id=args.detail)
        return

    # 2. Chế độ Live Tail
    if args.follow:
        run_continuous_follow(channel=args.channel)
        return

    # 3. Chế độ xem chi tiết 1 bản ghi
    if args.detail is not None:
        rows = fetch_local_logs(limit=1, record_id=args.detail)
        if not rows:
            print(f"{RED}Không tìm thấy bản ghi có ID = {args.detail}{RESET}")
            return
        render_record(rows[0], detail=True)
        return

    # 4. Chế độ xem danh sách
    rows = fetch_local_logs(limit=args.limit, search=args.search, channel=args.channel)
    if not rows:
        print(f"{YELLOW}Chưa có bản ghi nhật ký hội thoại nào phù hợp.{RESET}")
        return

    print(f"\n{GREEN}{BOLD}HIỂN THỊ {len(rows)} LƯỢT GỬI - NHẬN GẦN NHẤT (CSDL LOCAL):{RESET}")
    print(f"{DIM}Mẹo: Gõ 'python log_guinhan.py -d <ID>' để xem toàn văn chi tiết của một lượt cụ thể.{RESET}")

    for r in reversed(rows):
        render_record(r, detail=False)


if __name__ == "__main__":
    main()
