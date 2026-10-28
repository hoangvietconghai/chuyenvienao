# -*- coding: utf-8 -*-
"""
server/services/db_service.py
=============================
Hệ quản trị CSDL SQLite hợp nhất (WAL Mode) cho Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải.
Quản lý 07 bảng nghiệp vụ:
  1. danh_ba_can_bo     : Danh bạ cán bộ, lãnh đạo, 08 thôn, 21 chi bộ
  2. so_nhiem_vu        : Quản lý công việc 5 Rõ, deadline, chống trùng khi trượt tháng
  3. lich_su_nhac_nho   : Nhật ký nhắc việc, chống spam Zalo
  4. so_tieu_chi        : 20 chỉ tiêu Đại hội Đảng bộ xã khoá I & 19 chỉ tiêu NQ57
  5. so_van_ban         : Kho văn bản hành chính phân tầng vòng đời & hiệu lực
  6. van_ban_lien_ket   : Đồ thị quan hệ căn cứ, thay thế, sửa đổi
  7. van_ban_chunks     : Vector BLOB + FTS5 BM25 phục vụ Hybrid RAG
"""

import json
import sqlite3
import hashlib
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from server.config import BASE_DIR, DATA_DIR
from server.logger import get_logger

logger = get_logger("db_service")

DB_FILE = DATA_DIR / "chuyen_vien_ao.db"


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager cung cấp kết nối SQLite với cấu hình chuẩn:
    - WAL Mode (Write-Ahead Logging) cho khả năng đọc/ghi đồng thời
    - Row factory sqlite3.Row để truy xuất dữ liệu theo tên cột
    - Bật Foreign Keys
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Lỗi giao dịch SQLite: {e}")
        raise
    finally:
        conn.close()


def init_database() -> None:
    """Khởi tạo toàn bộ lược đồ CSDL chuẩn hóa 07 bảng nếu chưa tồn tại."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Bảng Danh bạ Cán bộ & Tổ chức
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS danh_ba_can_bo (
            can_bo_id TEXT PRIMARY KEY,
            ho_ten TEXT NOT NULL,
            chuc_vu TEXT NOT NULL,
            co_quan TEXT NOT NULL,
            co_quan_code TEXT NOT NULL,
            co_quan_loai TEXT NOT NULL,
            zalo_chat_id TEXT,
            zalo_user_id TEXT,
            so_dien_thoai TEXT,
            vai_tro TEXT DEFAULT 'chuyen_vien',
            is_active INTEGER DEFAULT 1,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Bảng Sổ Nhiệm vụ Cơ quan
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS so_nhiem_vu (
            task_id TEXT PRIMARY KEY,
            task_fingerprint TEXT UNIQUE,
            so_hieu_vb TEXT,
            doc_id TEXT,
            can_bo_id TEXT,
            co_quan_chu_tri TEXT NOT NULL,
            co_quan_chu_tri_code TEXT NOT NULL,
            co_quan_phoi_hop TEXT DEFAULT '[]',
            lanh_dao_chi_dao TEXT,
            cap_trinh TEXT,
            noi_dung_nhiem_vu TEXT NOT NULL,
            ngay_giao TEXT NOT NULL,
            deadline_date TEXT NOT NULL,
            deadline_time TEXT DEFAULT '17:00',
            deadline_type TEXT DEFAULT 'EXACT',
            che_do_bao_cao TEXT,
            trang_thai TEXT DEFAULT 'Chưa thực hiện',
            muc_do_uu_tien TEXT DEFAULT 'Bình thường',
            linh_vuc TEXT,
            ket_qua_bao_cao TEXT,
            created_from_wf TEXT DEFAULT 'manual',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (can_bo_id) REFERENCES danh_ba_can_bo(can_bo_id) ON DELETE SET NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON so_nhiem_vu(deadline_date, trang_thai);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_unit ON so_nhiem_vu(co_quan_chu_tri_code, trang_thai);")

        # 3. Bảng Lịch sử Nhắc việc
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lich_su_nhac_nho (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            remind_key TEXT UNIQUE NOT NULL,
            task_id TEXT,
            can_bo_id TEXT,
            loai_nhac TEXT NOT NULL,
            hinh_thuc TEXT DEFAULT 'zalo_1_1',
            noi_dung_nhac TEXT,
            thoi_gian_nhac TEXT DEFAULT CURRENT_TIMESTAMP,
            ket_qua TEXT DEFAULT 'pending'
        );
        """)

        # 4. Bảng Sổ Tiêu chí Nghị quyết Đại hội & NQ57
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS so_tieu_chi (
            kpi_id TEXT PRIMARY KEY,
            nguon_nghi_quyet TEXT NOT NULL,
            nhom_chi_tieu TEXT NOT NULL,
            ten_chi_tieu TEXT NOT NULL,
            don_vi_tinh TEXT NOT NULL,
            chi_tieu_nam_2026 REAL,
            chi_tieu_nhiem_ky_2030 REAL,
            gia_tri_hien_tai REAL DEFAULT 0,
            bieu_thuc_chi_tiet TEXT,
            ky_danh_gia TEXT DEFAULT 'Quy',
            co_quan_phu_trach TEXT,
            trang_thai_anh_sang TEXT DEFAULT 'XANH',
            ghi_chu_vuong_mac TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 5. Bảng Kho Văn bản Hành chính
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS so_van_ban (
            doc_id TEXT PRIMARY KEY,
            file_hash TEXT UNIQUE NOT NULL,
            ma_ho_so_eoffice TEXT,
            so_hieu_vb TEXT NOT NULL,
            loai_luong TEXT NOT NULL,
            the_loai_vb TEXT NOT NULL,
            cap_ban_hanh TEXT NOT NULL,
            co_quan_ban_hanh TEXT NOT NULL,
            co_quan_ban_hanh_code TEXT NOT NULL,
            ngay_ban_hanh TEXT NOT NULL,
            nam_ban_hanh INTEGER NOT NULL,
            giai_doan_lich_su TEXT DEFAULT 'SAU_SAP_NHAP',
            trich_yeu TEXT NOT NULL,
            nhom_vong_doi TEXT NOT NULL,
            trong_so_tham_quyen INTEGER DEFAULT 50,
            ma_chuyen_de TEXT,
            trang_thai_hieu_luc TEXT DEFAULT 'CON_HIEU_LUC',
            bi_thay_the_boi_so_hieu TEXT,
            nguoi_ky TEXT,
            file_path TEXT NOT NULL,
            gdrive_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vb_so_hieu ON so_van_ban(so_hieu_vb);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vb_filter ON so_van_ban(trang_thai_hieu_luc, nhom_vong_doi, ma_chuyen_de, ngay_ban_hanh DESC);")

        # 6. Bảng Đồ thị Liên kết Văn bản
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS van_ban_lien_ket (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vb_nguon_doc_id TEXT NOT NULL,
            vb_nguon_so_hieu TEXT NOT NULL,
            vb_dich_so_hieu TEXT NOT NULL,
            loai_quan_he TEXT NOT NULL,
            ghi_chu_quan_he TEXT,
            UNIQUE(vb_nguon_doc_id, vb_dich_so_hieu, loai_quan_he)
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_link_nguon ON van_ban_lien_ket(vb_nguon_so_hieu);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_link_dich ON van_ban_lien_ket(vb_dich_so_hieu);")

        # 7. Bảng Phân đoạn Văn bản (Chunks) & Bảng ảo FTS5
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS van_ban_chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            sub_doc_owner TEXT DEFAULT 'TAP_THE',
            section_path TEXT,
            chunk_type TEXT DEFAULT 'PROSE',
            context_header TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding BLOB,
            FOREIGN KEY (doc_id) REFERENCES so_van_ban(doc_id) ON DELETE CASCADE
        );
        """)

        # Bảng ảo FTS5 sử dụng unicode61 hỗ trợ tiếng Việt có dấu và ký hiệu văn bản "-/."
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS van_ban_fts USING fts5(
            chunk_id UNINDEXED,
            doc_id UNINDEXED,
            so_hieu_vb,
            trich_yeu,
            section_path,
            chunk_text,
            tokenize="unicode61 remove_diacritics 0 tokenchars '-/.'"
        );
        """)

        # 8. Bảng Danh mục Chuyên đề Quản lý
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS danh_muc_chuyen_de (
            ma_chuyen_de TEXT PRIMARY KEY,
            ten_chuyen_de TEXT NOT NULL,
            mo_ta TEXT,
            tu_khoa_nhan_dien TEXT,
            thu_tu INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Khởi tạo 08 chuyên đề công tác mặc định nếu bảng đang trống
        cursor.execute("SELECT COUNT(*) AS cnt FROM danh_muc_chuyen_de;")
        if cursor.fetchone()["cnt"] == 0:
            default_chuyen_de = [
                ("CDS_DEAN06", "Chuyển đổi số & Đề án 06", "Ban Chỉ đạo 57, chuyển đổi số, Đề án 06, CNTT, cải cách hành chính", "chuyển đổi số, đề án 06, nq57, số hoá, căn cước, dịch vụ công, ban chỉ đạo 57, phần mềm, trực tuyến", 1),
                ("XD_DANG_CAN_BO", "Xây dựng Đảng & Cán bộ", "Tổ chức cán bộ, phát triển đảng viên, bảo vệ chính trị nội bộ, sinh hoạt chi bộ", "xây dựng đảng, tổ chức, đảng viên, kết nạp, cán bộ, chi bộ, sinh hoạt, chính trị nội bộ, đào tạo, bồi dưỡng", 2),
                ("KT_GIAM_SAT", "Kiểm tra & Giám sát", "Ủy ban Kiểm tra, giám sát chuyên đề, thi hành kỷ luật Đảng, phòng chống tham nhũng", "kiểm tra, giám sát, kỷ luật, ubkt, ủy ban kiểm tra, khiếu nại, tố cáo, vi phạm, phòng chống tham nhũng", 3),
                ("KINH_TE_NGAN_SACH", "Kinh tế & Ngân sách", "Tài chính ngân sách xã, đầu tư công, phát triển kinh tế, nông thôn mới nâng cao", "kinh tế, ngân sách, thu chi, tài chính, đầu tư công, nông thôn mới, tăng trưởng, dự toán, quyết toán, thuế", 4),
                ("DAT_DAI_MOI_TRUONG", "Đất đai & Tài nguyên", "Quản lý đất đai, bồi thường giải phóng mặt bằng, tài nguyên khoáng sản, môi trường", "đất đai, tài nguyên, môi trường, khoáng sản, quy hoạch, gcn, bồi thường, tái định cư, trật tự xây dựng", 5),
                ("VAN_HOA_XA_HOI", "Văn hoá & Xã hội", "Văn hoá, giáo dục, y tế, an sinh xã hội, giảm nghèo, chính sách dân tộc Raglai", "văn hoá, giáo dục, y tế, an sinh, giảm nghèo, hộ nghèo, dân tộc, tôn giáo, raglai, chính sách xã hội, người có công", 6),
                ("QUOC_PHONG_AN_NINH", "Quốc phòng & An ninh", "Quốc phòng quân sự địa phương, an ninh trật tự, công an xã, tuyển quân, PCCC", "quốc phòng, an ninh, trật tự, quân sự, công an, tuyển quân, nghĩa vụ quân sự, pccc, phòng cháy, an toàn giao thông", 7),
                ("VAN_PHONG_THI_DUA", "Nội bộ Văn phòng & Quy chế", "Công tác văn phòng cấp uỷ, quy chế làm việc, thi đua khen thưởng, văn thư", "văn phòng, quy chế làm việc, thi đua, khen thưởng, văn thư, lưu trữ, nội bộ, phân công công tác, giao ban", 8),
            ]
            cursor.executemany("""
            INSERT INTO danh_muc_chuyen_de (ma_chuyen_de, ten_chuyen_de, mo_ta, tu_khoa_nhan_dien, thu_tu)
            VALUES (?, ?, ?, ?, ?);
            """, default_chuyen_de)

        logger.info(f"Đã khởi tạo và kết nối thành công CSDL SQLite WAL: {DB_FILE}")


# ==============================================================================
# 1. CÁC HÀM CRUD CHO DANH BẠ CÁN BỘ & ĐƠN VỊ (`danh_ba_can_bo`)
# ==============================================================================

def add_or_update_can_bo(can_bo: Dict[str, Any]) -> bool:
    """Thêm mới hoặc cập nhật thông tin cán bộ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO danh_ba_can_bo (
            can_bo_id, ho_ten, chuc_vu, co_quan, co_quan_code, co_quan_loai,
            zalo_chat_id, zalo_user_id, so_dien_thoai, vai_tro, is_active, updated_at
        ) VALUES (
            :can_bo_id, :ho_ten, :chuc_vu, :co_quan, :co_quan_code, :co_quan_loai,
            :zalo_chat_id, :zalo_user_id, :so_dien_thoai, :vai_tro, :is_active, CURRENT_TIMESTAMP
        )
        ON CONFLICT(can_bo_id) DO UPDATE SET
            ho_ten = excluded.ho_ten,
            chuc_vu = excluded.chuc_vu,
            co_quan = excluded.co_quan,
            co_quan_code = excluded.co_quan_code,
            co_quan_loai = excluded.co_quan_loai,
            zalo_chat_id = COALESCE(excluded.zalo_chat_id, danh_ba_can_bo.zalo_chat_id),
            zalo_user_id = COALESCE(excluded.zalo_user_id, danh_ba_can_bo.zalo_user_id),
            so_dien_thoai = COALESCE(excluded.so_dien_thoai, danh_ba_can_bo.so_dien_thoai),
            vai_tro = excluded.vai_tro,
            is_active = excluded.is_active,
            updated_at = CURRENT_TIMESTAMP;
        """, {
            "can_bo_id": can_bo["can_bo_id"],
            "ho_ten": can_bo["ho_ten"],
            "chuc_vu": can_bo["chuc_vu"],
            "co_quan": can_bo["co_quan"],
            "co_quan_code": can_bo["co_quan_code"],
            "co_quan_loai": can_bo.get("co_quan_loai", "chuyen_vien"),
            "zalo_chat_id": can_bo.get("zalo_chat_id"),
            "zalo_user_id": can_bo.get("zalo_user_id"),
            "so_dien_thoai": can_bo.get("so_dien_thoai"),
            "vai_tro": can_bo.get("vai_tro", "chuyen_vien"),
            "is_active": can_bo.get("is_active", 1),
        })
        return True


def get_all_can_bo(only_active: bool = True) -> List[Dict[str, Any]]:
    """Lấy danh sách cán bộ toàn hệ thống."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM danh_ba_can_bo"
        if only_active:
            query += " WHERE is_active = 1"
        query += " ORDER BY co_quan_loai, co_quan_code, can_bo_id"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def get_can_bo_by_id(can_bo_id: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin cán bộ theo ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM danh_ba_can_bo WHERE can_bo_id = ?", (can_bo_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_can_bo_by_unit(co_quan_code: str) -> List[Dict[str, Any]]:
    """Lấy danh sách cán bộ thuộc một cơ quan/đơn vị."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM danh_ba_can_bo WHERE co_quan_code = ? AND is_active = 1", (co_quan_code,))
        return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# 2. CÁC HÀM CRUD CHO SỔ TIÊU CHÍ (`so_tieu_chi`)
# ==============================================================================

def add_or_update_kpi(kpi: Dict[str, Any]) -> bool:
    """Thêm mới hoặc cập nhật một chỉ tiêu KPI."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        def _to_float(v: Any) -> Optional[float]:
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, (list, tuple)) and v:
                try:
                    return float(v[0])
                except (ValueError, TypeError):
                    return None
            try:
                return float(str(v).strip().replace("%", ""))
            except (ValueError, TypeError):
                return None

        cursor.execute("""
        INSERT INTO so_tieu_chi (
            kpi_id, nguon_nghi_quyet, nhom_chi_tieu, ten_chi_tieu, don_vi_tinh,
            chi_tieu_nam_2026, chi_tieu_nhiem_ky_2030, gia_tri_hien_tai,
            bieu_thuc_chi_tiet, ky_danh_gia, co_quan_phu_trach,
            trang_thai_anh_sang, ghi_chu_vuong_mac, updated_at
        ) VALUES (
            :kpi_id, :nguon_nghi_quyet, :nhom_chi_tieu, :ten_chi_tieu, :don_vi_tinh,
            :chi_tieu_nam_2026, :chi_tieu_nhiem_ky_2030, :gia_tri_hien_tai,
            :bieu_thuc_chi_tiet, :ky_danh_gia, :co_quan_phu_trach,
            :trang_thai_anh_sang, :ghi_chu_vuong_mac, CURRENT_TIMESTAMP
        )
        ON CONFLICT(kpi_id) DO UPDATE SET
            nguon_nghi_quyet = excluded.nguon_nghi_quyet,
            nhom_chi_tieu = excluded.nhom_chi_tieu,
            ten_chi_tieu = excluded.ten_chi_tieu,
            don_vi_tinh = excluded.don_vi_tinh,
            chi_tieu_nam_2026 = excluded.chi_tieu_nam_2026,
            chi_tieu_nhiem_ky_2030 = excluded.chi_tieu_nhiem_ky_2030,
            gia_tri_hien_tai = excluded.gia_tri_hien_tai,
            bieu_thuc_chi_tiet = excluded.bieu_thuc_chi_tiet,
            ky_danh_gia = excluded.ky_danh_gia,
            co_quan_phu_trach = excluded.co_quan_phu_trach,
            trang_thai_anh_sang = excluded.trang_thai_anh_sang,
            ghi_chu_vuong_mac = excluded.ghi_chu_vuong_mac,
            updated_at = CURRENT_TIMESTAMP;
        """, {
            "kpi_id": kpi["kpi_id"],
            "nguon_nghi_quyet": kpi.get("nguon_nghi_quyet", "NQ_DAI_HOI_I"),
            "nhom_chi_tieu": kpi.get("nhom_chi_tieu", "Kinh tế - Xã hội"),
            "ten_chi_tieu": kpi["ten_chi_tieu"],
            "don_vi_tinh": kpi.get("don_vi_tinh", "%"),
            "chi_tieu_nam_2026": _to_float(kpi.get("chi_tieu_nam_2026")),
            "chi_tieu_nhiem_ky_2030": _to_float(kpi.get("chi_tieu_nhiem_ky_2030")),
            "gia_tri_hien_tai": _to_float(kpi.get("gia_tri_hien_tai")) or 0.0,
            "bieu_thuc_chi_tiet": kpi.get("bieu_thuc_chi_tiet", ""),
            "ky_danh_gia": kpi.get("ky_danh_gia", "Quy"),
            "co_quan_phu_trach": kpi.get("co_quan_phu_trach", "UBND xã"),
            "trang_thai_anh_sang": kpi.get("trang_thai_anh_sang", "XANH"),
            "ghi_chu_vuong_mac": kpi.get("ghi_chu_vuong_mac", ""),
        })
        return True


def get_all_kpis(nguon_nghi_quyet: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lấy danh sách tất cả chỉ tiêu KPI."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if nguon_nghi_quyet:
            cursor.execute("SELECT * FROM so_tieu_chi WHERE nguon_nghi_quyet = ? ORDER BY kpi_id", (nguon_nghi_quyet,))
        else:
            cursor.execute("SELECT * FROM so_tieu_chi ORDER BY nguon_nghi_quyet, kpi_id")
        return [dict(row) for row in cursor.fetchall()]


def update_kpi_progress(kpi_id: str, gia_tri: float, bieu_thuc: str = "", trang_thai: str = "XANH") -> bool:
    """Cập nhật tiến độ số liệu thực hiện cho một chỉ tiêu KPI."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE so_tieu_chi
        SET gia_tri_hien_tai = ?,
            bieu_thuc_chi_tiet = CASE WHEN ? != '' THEN ? ELSE bieu_thuc_chi_tiet END,
            trang_thai_anh_sang = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE kpi_id = ?;
        """, (gia_tri, bieu_thuc, bieu_thuc, trang_thai, kpi_id))
        return cursor.rowcount > 0


# ==============================================================================
# 3. CÁC HÀM CRUD CHO SỔ NHIỆM VỤ CƠ QUAN (`so_nhiem_vu`)
# ==============================================================================

def generate_task_fingerprint(co_quan_code: str, noi_dung: str) -> str:
    """Tạo mã băm chuẩn hoá để chống tạo nhiệm vụ trùng lặp khi trượt tiến độ qua các tháng."""
    norm = "".join(noi_dung.lower().split())
    raw = f"{co_quan_code.upper()}::{norm[:120]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def add_or_update_task(task: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Thêm mới hoặc cập nhật nhiệm vụ.
    Hỗ trợ khử trùng lặp (Deduplication) khi nhiệm vụ trượt qua các tháng.
    Trả về: (thành_công, task_id, hành_động: 'created' | 'rescheduled' | 'updated')
    """
    co_quan_code = task.get("co_quan_chu_tri_code", "UBND")
    noi_dung = task.get("noi_dung_nhiem_vu", "").strip()
    fingerprint = task.get("task_fingerprint") or generate_task_fingerprint(co_quan_code, noi_dung)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Kiểm tra fingerprint trùng lặp
        cursor.execute("SELECT task_id, deadline_date, trang_thai FROM so_nhiem_vu WHERE task_fingerprint = ?", (fingerprint,))
        existing = cursor.fetchone()

        if existing:
            # Nhiệm vụ đã tồn tại -> cập nhật lùi hạn (Rescheduled)
            old_task_id = existing["task_id"]
            new_deadline = task.get("deadline_date", existing["deadline_date"])
            cursor.execute("""
            UPDATE so_nhiem_vu
            SET deadline_date = ?,
                cap_trinh = COALESCE(?, cap_trinh),
                so_hieu_vb = COALESCE(?, so_hieu_vb),
                trang_thai = CASE WHEN trang_thai = 'Hoàn thành' THEN 'Hoàn thành' ELSE 'Chuyển tiếp tháng sau' END
            WHERE task_id = ?;
            """, (new_deadline, task.get("cap_trinh"), task.get("so_hieu_vb"), old_task_id))
            return True, old_task_id, "rescheduled"

        # Nếu chưa tồn tại -> tạo mới
        task_id = task.get("task_id")
        if not task_id:
            cursor.execute("SELECT COUNT(*) AS total FROM so_nhiem_vu")
            cnt = cursor.fetchone()["total"] + 1
            task_id = f"NV-2026-{cnt:04d}"

        co_quan_phoi_hop = task.get("co_quan_phoi_hop", "[]")
        if isinstance(co_quan_phoi_hop, (list, tuple)):
            co_quan_phoi_hop = json.dumps(co_quan_phoi_hop, ensure_ascii=False)

        cursor.execute("""
        INSERT INTO so_nhiem_vu (
            task_id, task_fingerprint, so_hieu_vb, doc_id, can_bo_id,
            co_quan_chu_tri, co_quan_chu_tri_code, co_quan_phoi_hop,
            lanh_dao_chi_dao, cap_trinh, noi_dung_nhiem_vu, ngay_giao,
            deadline_date, deadline_time, deadline_type, che_do_bao_cao,
            trang_thai, muc_do_uu_tien, linh_vuc, ket_qua_bao_cao,
            created_from_wf, created_at
        ) VALUES (
            :task_id, :task_fingerprint, :so_hieu_vb, :doc_id, :can_bo_id,
            :co_quan_chu_tri, :co_quan_chu_tri_code, :co_quan_phoi_hop,
            :lanh_dao_chi_dao, :cap_trinh, :noi_dung_nhiem_vu, :ngay_giao,
            :deadline_date, :deadline_time, :deadline_type, :che_do_bao_cao,
            :trang_thai, :muc_do_uu_tien, :linh_vuc, :ket_qua_bao_cao,
            :created_from_wf, CURRENT_TIMESTAMP
        );
        """, {
            "task_id": task_id,
            "task_fingerprint": fingerprint,
            "so_hieu_vb": task.get("so_hieu_vb"),
            "doc_id": task.get("doc_id"),
            "can_bo_id": task.get("can_bo_id"),
            "co_quan_chu_tri": task.get("co_quan_chu_tri", "UBND xã"),
            "co_quan_chu_tri_code": co_quan_code,
            "co_quan_phoi_hop": co_quan_phoi_hop,
            "lanh_dao_chi_dao": task.get("lanh_dao_chi_dao"),
            "cap_trinh": task.get("cap_trinh"),
            "noi_dung_nhiem_vu": noi_dung,
            "ngay_giao": task.get("ngay_giao", datetime.now().strftime("%Y-%m-%d")),
            "deadline_date": task.get("deadline_date", datetime.now().strftime("%Y-%m-%d")),
            "deadline_time": task.get("deadline_time", "17:00"),
            "deadline_type": task.get("deadline_type", "EXACT"),
            "che_do_bao_cao": task.get("che_do_bao_cao"),
            "trang_thai": task.get("trang_thai", "Chưa thực hiện"),
            "muc_do_uu_tien": task.get("muc_do_uu_tien", "Bình thường"),
            "linh_vuc": task.get("linh_vuc", "Chung"),
            "ket_qua_bao_cao": task.get("ket_qua_bao_cao"),
            "created_from_wf": task.get("created_from_wf", "manual"),
        })
        return True, task_id, "created"


def get_tasks(
    trang_thai: Optional[str] = None,
    co_quan_code: Optional[str] = None,
    cap_trinh: Optional[str] = None,
    tu_ngay: Optional[str] = None,
    den_ngay: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Truy vấn danh sách nhiệm vụ theo nhiều tiêu chí lọc."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        clauses = []
        params = []

        if trang_thai:
            clauses.append("trang_thai = ?")
            params.append(trang_thai)
        if co_quan_code:
            clauses.append("co_quan_chu_tri_code = ?")
            params.append(co_quan_code)
        if cap_trinh:
            clauses.append("cap_trinh LIKE ?")
            params.append(f"%{cap_trinh}%")
        if tu_ngay:
            clauses.append("deadline_date >= ?")
            params.append(tu_ngay)
        if den_ngay:
            clauses.append("deadline_date <= ?")
            params.append(den_ngay)

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM so_nhiem_vu{where_sql} ORDER BY deadline_date ASC, muc_do_uu_tien DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, tuple(params))
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            try:
                d["co_quan_phoi_hop"] = json.loads(d["co_quan_phoi_hop"])
            except Exception:
                pass
            results.append(d)
        return results


def update_task_status(task_id: str, trang_thai: str, ket_qua: str = "") -> bool:
    """Cập nhật trạng thái nhiệm vụ (Hoàn thành / Đang thực hiện / v.v.)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        completed_at = datetime.now().isoformat() if trang_thai == "Hoàn thành" else None
        cursor.execute("""
        UPDATE so_nhiem_vu
        SET trang_thai = ?,
            ket_qua_bao_cao = CASE WHEN ? != '' THEN ? ELSE ket_qua_bao_cao END,
            completed_at = COALESCE(?, completed_at)
        WHERE task_id = ?;
        """, (trang_thai, ket_qua, ket_qua, completed_at, task_id))
        return cursor.rowcount > 0


def delete_task(task_id: str) -> bool:
    """Xoá một nhiệm vụ theo ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM so_nhiem_vu WHERE task_id = ?", (task_id,))
        return cursor.rowcount > 0


# ==============================================================================
# 4. CÁC HÀM QUẢN LÝ KHO VĂN BẢN & ĐỒ THỊ LIÊN KẾT (`so_van_ban`, `van_ban_lien_ket`)
# ==============================================================================

def make_canonical_doc_key(so_hieu: str, ngay_iso: str, co_quan_code: str) -> str:
    """Tạo canonical key chuẩn chống trùng số hiệu: {so_hieu}_{ngay_ISO}_{co_quan}."""
    norm_so = "".join(so_hieu.upper().split())
    norm_ngay = ngay_iso.strip()
    norm_cq = co_quan_code.upper().strip()
    return f"{norm_so}_{norm_ngay}_{norm_cq}"


def add_or_update_document(doc: Dict[str, Any]) -> str:
    """
    Thêm mới hoặc cập nhật văn bản vào so_van_ban.
    Đồng thời tự động xử lý quan hệ thay thế/sửa đổi văn bản cũ.
    """
    doc_id = doc.get("doc_id")
    so_hieu = doc["so_hieu_vb"].strip()
    ngay_ban_hanh = doc.get("ngay_ban_hanh", datetime.now().strftime("%Y-%m-%d"))
    co_quan_code = doc.get("co_quan_ban_hanh_code", "DU")
    
    if not doc_id:
        doc_id = make_canonical_doc_key(so_hieu, ngay_ban_hanh, co_quan_code)

    file_path = doc.get("file_path", "")
    file_hash = doc.get("file_hash")
    if not file_hash and file_path and Path(file_path).exists():
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
    elif not file_hash:
        file_hash = hashlib.sha256(f"{doc_id}_{datetime.now()}".encode("utf-8")).hexdigest()

    nam_ban_hanh = int(ngay_ban_hanh.split("-")[0]) if "-" in ngay_ban_hanh else 2026
    giai_doan = "TRUOC_SAP_NHAP" if ngay_ban_hanh < "2025-07-01" else "SAU_SAP_NHAP"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO so_van_ban (
            doc_id, file_hash, ma_ho_so_eoffice, so_hieu_vb, loai_luong,
            the_loai_vb, cap_ban_hanh, co_quan_ban_hanh, co_quan_ban_hanh_code,
            ngay_ban_hanh, nam_ban_hanh, giai_doan_lich_su, trich_yeu,
            nhom_vong_doi, trong_so_tham_quyen, ma_chuyen_de,
            trang_thai_hieu_luc, bi_thay_the_boi_so_hieu, nguoi_ky,
            file_path, gdrive_url, created_at
        ) VALUES (
            :doc_id, :file_hash, :ma_ho_so_eoffice, :so_hieu_vb, :loai_luong,
            :the_loai_vb, :cap_ban_hanh, :co_quan_ban_hanh, :co_quan_ban_hanh_code,
            :ngay_ban_hanh, :nam_ban_hanh, :giai_doan_lich_su, :trich_yeu,
            :nhom_vong_doi, :trong_so_tham_quyen, :ma_chuyen_de,
            :trang_thai_hieu_luc, :bi_thay_the_boi_so_hieu, :nguoi_ky,
            :file_path, :gdrive_url, CURRENT_TIMESTAMP
        )
        ON CONFLICT(doc_id) DO UPDATE SET
            so_hieu_vb = excluded.so_hieu_vb,
            trich_yeu = excluded.trich_yeu,
            nhom_vong_doi = excluded.nhom_vong_doi,
            trong_so_tham_quyen = excluded.trong_so_tham_quyen,
            ma_chuyen_de = excluded.ma_chuyen_de,
            trang_thai_hieu_luc = excluded.trang_thai_hieu_luc,
            bi_thay_the_boi_so_hieu = excluded.bi_thay_the_boi_so_hieu,
            file_path = excluded.file_path,
            gdrive_url = excluded.gdrive_url;
        """, {
            "doc_id": doc_id,
            "file_hash": file_hash,
            "ma_ho_so_eoffice": doc.get("ma_ho_so_eoffice"),
            "so_hieu_vb": so_hieu,
            "loai_luong": doc.get("loai_luong", "VAN_BAN_DI"),
            "the_loai_vb": doc.get("the_loai_vb", "CV"),
            "cap_ban_hanh": doc.get("cap_ban_hanh", "XA_CONG_HAI"),
            "co_quan_ban_hanh": doc.get("co_quan_ban_hanh", "Đảng uỷ xã Công Hải"),
            "co_quan_ban_hanh_code": co_quan_code,
            "ngay_ban_hanh": ngay_ban_hanh,
            "nam_ban_hanh": nam_ban_hanh,
            "giai_doan_lich_su": giai_doan,
            "trich_yeu": doc.get("trich_yeu", ""),
            "nhom_vong_doi": doc.get("nhom_vong_doi", "THEMATIC_CASE"),
            "trong_so_tham_quyen": doc.get("trong_so_tham_quyen", 50),
            "ma_chuyen_de": doc.get("ma_chuyen_de"),
            "trang_thai_hieu_luc": doc.get("trang_thai_hieu_luc", "CON_HIEU_LUC"),
            "bi_thay_the_boi_so_hieu": doc.get("bi_thay_the_boi_so_hieu"),
            "nguoi_ky": doc.get("nguoi_ky"),
            "file_path": file_path,
            "gdrive_url": doc.get("gdrive_url"),
        })

        # Nếu văn bản mới thay thế văn bản cũ -> cập nhật trạng thái văn bản cũ
        bi_thay_the = doc.get("thay_the_so_hieu")
        if bi_thay_the:
            cursor.execute("""
            UPDATE so_van_ban
            SET trang_thai_hieu_luc = 'BI_THAY_THE',
                bi_thay_the_boi_so_hieu = ?
            WHERE so_hieu_vb = ?;
            """, (so_hieu, bi_thay_the))

            # Ghi vào bảng đồ thị liên kết
            cursor.execute("""
            INSERT OR IGNORE INTO van_ban_lien_ket (vb_nguon_doc_id, vb_nguon_so_hieu, vb_dich_so_hieu, loai_quan_he)
            VALUES (?, ?, ?, 'THAY_THE');
            """, (doc_id, so_hieu, bi_thay_the))

        return doc_id


def add_document_link(doc_id: str, vb_nguon_so: str, vb_dich_so: str, loai_quan_he: str, ghi_chu: str = "") -> bool:
    """Thêm quan hệ giữa 2 văn bản (Căn cứ, Thực hiện, Thay thế, Báo cáo cho)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO van_ban_lien_ket (
            vb_nguon_doc_id, vb_nguon_so_hieu, vb_dich_so_hieu, loai_quan_he, ghi_chu_quan_he
        ) VALUES (?, ?, ?, ?, ?);
        """, (doc_id, vb_nguon_so, vb_dich_so, loai_quan_he, ghi_chu))
        return True


def get_linked_documents(so_hieu: str) -> List[Dict[str, Any]]:
    """Lấy danh sách các văn bản có liên kết trực tiếp (1-hop) với số hiệu văn bản này."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM van_ban_lien_ket
        WHERE vb_nguon_so_hieu = ? OR vb_dich_so_hieu = ?;
        """, (so_hieu, so_hieu))
        return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# 5. CÁC HÀM CHO HYBRID RAG (CHUNKS & FTS5 BM25 SEARCH)
# ==============================================================================

def insert_chunk(
    doc_id: str,
    so_hieu_vb: str,
    trich_yeu: str,
    section_path: str,
    context_header: str,
    chunk_text: str,
    sub_doc_owner: str = "TAP_THE",
    chunk_type: str = "PROSE",
    embedding_blob: Optional[bytes] = None
) -> int:
    """Thêm một đoạn văn bản (chunk) vào bảng chunks và bảng ảo FTS5."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO van_ban_chunks (
            doc_id, sub_doc_owner, section_path, chunk_type, context_header, chunk_text, embedding
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (doc_id, sub_doc_owner, section_path, chunk_type, context_header, chunk_text, embedding_blob))
        chunk_id = cursor.lastrowid

        # Ghi vào bảng FTS5
        cursor.execute("""
        INSERT INTO van_ban_fts (
            chunk_id, doc_id, so_hieu_vb, trich_yeu, section_path, chunk_text
        ) VALUES (?, ?, ?, ?, ?, ?);
        """, (chunk_id, doc_id, so_hieu_vb, trich_yeu, section_path, chunk_text))

        return chunk_id


def search_fts_bm25(query: str, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Tìm kiếm văn bản toàn văn bằng SQLite FTS5 BM25.
    Hỗ trợ tiếng Việt có dấu, tìm theo số hiệu hoặc nội dung.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Chuẩn hoá query FTS5: nếu có ký tự đặc biệt, bọc trong ngoặc kép
        safe_q = query.replace('"', '""').strip()
        if not safe_q:
            return []

        # Thử tìm khớp nguyên cụm hoặc từng từ
        words = [w for w in safe_q.split() if len(w) > 1]
        fts_query = f'"{safe_q}"' if len(words) <= 3 else " OR ".join(f'"{w}"' for w in words)

        try:
            cursor.execute("""
            SELECT 
                fts.chunk_id,
                fts.doc_id,
                fts.so_hieu_vb,
                fts.trich_yeu,
                fts.section_path,
                fts.chunk_text,
                bm25(van_ban_fts) AS bm25_rank,
                c.context_header,
                c.sub_doc_owner,
                c.chunk_type,
                vb.nhom_vong_doi,
                vb.trang_thai_hieu_luc,
                vb.ngay_ban_hanh,
                vb.trong_so_tham_quyen
            FROM van_ban_fts fts
            JOIN van_ban_chunks c ON fts.chunk_id = c.chunk_id
            JOIN so_van_ban vb ON fts.doc_id = vb.doc_id
            WHERE van_ban_fts MATCH ?
              AND vb.trang_thai_hieu_luc != 'BI_THAY_THE'
            ORDER BY bm25(van_ban_fts) ASC, vb.trong_so_tham_quyen DESC
            LIMIT ?;
            """, (fts_query, limit))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Lỗi FTS5 MATCH với query '{fts_query}': {e}. Thử fallback LIKE...")
            cursor.execute("""
            SELECT 
                c.chunk_id, c.doc_id, vb.so_hieu_vb, vb.trich_yeu,
                c.section_path, c.chunk_text, 0.0 AS bm25_rank,
                c.context_header, c.sub_doc_owner, c.chunk_type,
                vb.nhom_vong_doi, vb.trang_thai_hieu_luc, vb.ngay_ban_hanh, vb.trong_so_tham_quyen
            FROM van_ban_chunks c
            JOIN so_van_ban vb ON c.doc_id = vb.doc_id
            WHERE (c.chunk_text LIKE ? OR vb.trich_yeu LIKE ? OR vb.so_hieu_vb LIKE ?)
              AND vb.trang_thai_hieu_luc != 'BI_THAY_THE'
            ORDER BY vb.trong_so_tham_quyen DESC
            LIMIT ?;
            """, (f"%{safe_q}%", f"%{safe_q}%", f"%{safe_q}%", limit))
            return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# 6. KHÓA CHỐNG GỬI LẶP THÔNG BÁO / ZALO (`lich_su_nhac_nho`)
# ==============================================================================

def acquire_remind_lock(remind_key: str, task_id: Optional[str], can_bo_id: Optional[str], loai_nhac: str) -> bool:
    """
    Cố gắng giành khóa gửi nhắc việc.
    Nếu remind_key đã tồn tại trong ngày -> trả về False (chống gửi trùng tin nhắn).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO lich_su_nhac_nho (remind_key, task_id, can_bo_id, loai_nhac, ket_qua)
            VALUES (?, ?, ?, ?, 'pending');
            """, (remind_key, task_id, can_bo_id, loai_nhac))
            return True
        except sqlite3.IntegrityError:
            # Khóa đã tồn tại
            return False


def update_remind_result(remind_key: str, ket_qua: str, noi_dung: str = "") -> None:
    """Cập nhật kết quả gửi thông báo nhắc việc (success | failed)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE lich_su_nhac_nho
        SET ket_qua = ?,
            noi_dung_nhac = CASE WHEN ? != '' THEN ? ELSE noi_dung_nhac END,
            thoi_gian_nhac = CURRENT_TIMESTAMP
        WHERE remind_key = ?;
        """, (ket_qua, noi_dung, noi_dung, remind_key))


# ==============================================================================
# 6. QUẢN LÝ DANH MỤC CHUYÊN ĐỀ ĐỘNG
# ==============================================================================

def get_all_chuyen_de(only_active: bool = True) -> List[Dict[str, Any]]:
    """Lấy danh mục các chuyên đề công tác hiện có."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM danh_muc_chuyen_de"
        if only_active:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY thu_tu ASC, created_at ASC;"
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]


def add_chuyen_de(ten_chuyen_de: str, ma_chuyen_de: Optional[str] = None, mo_ta: str = "", tu_khoa: str = "") -> Dict[str, Any]:
    """
    Thêm mới một chuyên đề công tác vào hệ thống.
    Nếu cán bộ không nhập mã, hệ thống tự động sinh mã dạng CD_TEN_RUT_GON.
    """
    import re
    import unicodedata

    ten_clean = ten_chuyen_de.strip()
    if not ma_chuyen_de or not ma_chuyen_de.strip():
        # Bỏ dấu tiếng Việt để tạo mã slug ngắn gọn
        nfkd = unicodedata.normalize('NFKD', ten_clean)
        no_diacritics = "".join([c for c in nfkd if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D')
        slug = re.sub(r'[^A-Z0-9]+', '_', no_diacritics.upper()).strip('_')
        ma_code = f"CD_{slug[:25]}"
    else:
        ma_code = ma_chuyen_de.strip().upper()

    # Tự động sinh danh sách từ khoá nhận diện phong phú nếu không truyền
    if not tu_khoa or not tu_khoa.strip():
        kw_list = [ten_clean.lower()]
        # Tách theo các liên từ &, và, +, phẩy, gạch chéo
        sub_phrases = re.split(r'[\&\,\+\/\-]|\bvà\b', ten_clean.lower())
        for sp in sub_phrases:
            sp_clean = sp.strip()
            if len(sp_clean) >= 3 and sp_clean not in kw_list:
                kw_list.append(sp_clean)
            # Tách các từ con có nghĩa
            words = sp_clean.split()
            if len(words) >= 2:
                for w in words:
                    if len(w) >= 4 and w not in ["công", "tác", "việc", "đảng", "phòng"]:
                        kw_list.append(w)
        tu_khoa_val = ", ".join(kw_list)
    else:
        tu_khoa_val = tu_khoa.strip().lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO danh_muc_chuyen_de (ma_chuyen_de, ten_chuyen_de, mo_ta, tu_khoa_nhan_dien, thu_tu)
        VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(thu_tu), 0) + 1 FROM danh_muc_chuyen_de))
        ON CONFLICT(ma_chuyen_de) DO UPDATE SET
            ten_chuyen_de = excluded.ten_chuyen_de,
            tu_khoa_nhan_dien = excluded.tu_khoa_nhan_dien,
            mo_ta = CASE WHEN excluded.mo_ta != '' THEN excluded.mo_ta ELSE danh_muc_chuyen_de.mo_ta END,
            is_active = 1;
        """, (ma_code, ten_clean, mo_ta, tu_khoa_val))

    logger.info(f"Đã lưu chuyên đề mới: {ma_code} - {ten_clean} (Từ khoá: {tu_khoa_val})")
    return {"ma_chuyen_de": ma_code, "ten_chuyen_de": ten_clean, "mo_ta": mo_ta}


# Khởi tạo bảng ngay khi import module
init_database()
