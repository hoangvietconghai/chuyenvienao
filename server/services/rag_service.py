# -*- coding: utf-8 -*-
"""
server/services/rag_service.py
==============================
Hệ thống Hybrid RAG Hành chính có kiểm soát (Controlled RAG Ingestion) cho Đảng bộ xã Công Hải.
Hỗ trợ:
1. Chốt chặn tài liệu MẬT (Secret Gatekeeper).
2. Quy trình nạp có kiểm duyệt (Human-in-the-Loop Preview & Review):
   - Preview & Bóc tách tự động: Số hiệu, Ngày tháng, Cơ quan, Thể loại, Vòng đời, Chunks.
   - Cho phép cán bộ xem trước, chỉnh sửa thông tin trước khi nạp vào hệ thống.
   - Nút nạp chính thức (Commit) sau khi cán bộ duyệt.
3. Quản trị kho RAG: Thống kê, Xoá sạch (Clear), Xoá từng văn bản, Liệt kê danh mục.
4. Chiến lược truy xuất "Giỏ Ngữ Cảnh 2 - 4 - 2" kết hợp SQLite FTS5 BM25 và Đồ thị liên kết.
"""

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.doc_reader import extract_document_text
from server.config import BASE_DIR
from server.logger import get_logger
from server.services import db_service

logger = get_logger("rag_service")


# ==============================================================================
# 1. QUẢN LÝ KHO & LÀM SẠCH DỮ LIỆU RAG
# ==============================================================================

def clear_rag_data() -> Dict[str, Any]:
    """Xoá sạch toàn bộ dữ liệu RAG trong SQLite DB để thực hiện lại từ đầu."""
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM van_ban_fts;")
        cursor.execute("DELETE FROM van_ban_chunks;")
        cursor.execute("DELETE FROM van_ban_lien_ket;")
        cursor.execute("DELETE FROM so_van_ban;")
        logger.info("Đã xoá sạch toàn bộ bảng dữ liệu RAG.")
    return {"success": True, "message": "Đã xoá sạch toàn bộ dữ liệu trong kho RAG."}


def append_outgoing_document_to_master(
    so_hieu: str,
    trich_yeu: str,
    the_loai: str,
    nguoi_ky: str = "",
    ngay_ban_hanh: str = "",
    file_name: str = ""
) -> bool:
    """
    Tự động ghi nối 1 dòng mới vào tệp Excel Master `data/danh_muc_van_ban_di_master.xlsx`.
    Đảm bảo STT luôn được tăng tiến tự động và cập nhật ngày chốt số liệu.
    """
    try:
        import openpyxl
        from server.config import DATA_DIR
        master_path = DATA_DIR / "danh_muc_van_ban_di_master.xlsx"
        if not master_path.exists():
            return False

        wb = openpyxl.load_workbook(master_path)
        ws = wb.active

        # Đọc STT dòng đầu tiên hiện tại (dòng 10)
        current_max_stt = 0
        try:
            val_stt = ws.cell(10, 1).value
            current_max_stt = int(val_stt) if val_stt else (ws.max_row - 9)
        except Exception:
            current_max_stt = ws.max_row - 9

        new_stt = current_max_stt + 1

        # Chèn 1 dòng mới ngay tại dòng 10 (đưa văn bản mới nhất lên đầu bảng)
        ws.insert_rows(10)

        # Định dạng ngày giờ dạng DD/MM/YYYY 00:00:00
        now_str = datetime.now().strftime("%d/%m/%Y 00:00:00")
        if ngay_ban_hanh and "-" in ngay_ban_hanh:
            parts = ngay_ban_hanh.split("-")
            if len(parts) == 3:
                now_str = f"{parts[2]}/{parts[1]}/{parts[0]} 00:00:00"

        # Ghi các cột: STT, ID, Trích yếu, Số ký hiệu, Độ mật, Độ khẩn, Sổ văn bản, Thể loại, Người ký, Ngày tạo, File
        ws.cell(10, 1, new_stt)
        ws.cell(10, 2, f"AUTO_{int(datetime.now().timestamp())}")
        ws.cell(10, 3, trich_yeu)
        ws.cell(10, 4, so_hieu)
        ws.cell(10, 5, "Thường")
        ws.cell(10, 6, "Thường")
        ws.cell(10, 7, "SỔ VĂN BẢN ĐI ĐẢNG ỦY NHIỆM KỲ 2025-2030")
        ws.cell(10, 8, the_loai)
        ws.cell(10, 9, nguoi_ky or "Vũ Thị Thuỳ Trang")
        ws.cell(10, 10, now_str)
        ws.cell(10, 11, file_name or f"{so_hieu}.pdf")

        # Cập nhật ngày chốt dữ liệu tại ô H7
        ws['H7'] = f"Ngày chốt dữ liệu báo cáo: {datetime.now().strftime('%d/%m/%Y')}"

        wb.save(master_path)
        logger.info(f"✓ Đã tự động chèn văn bản '{so_hieu}' vào tệp Excel Master (STT mới: {new_stt})")
        return True
    except Exception as ex:
        logger.warning(f"Lỗi khi nối văn bản vào Excel Master: {ex}")
        return False


def get_rag_stats() -> Dict[str, Any]:
    """Lấy số liệu thống kê tổng thể của kho RAG."""
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total_docs FROM so_van_ban;")
        total_docs = cursor.fetchone()["total_docs"]

        cursor.execute("SELECT COUNT(*) AS total_chunks FROM van_ban_chunks;")
        total_chunks = cursor.fetchone()["total_chunks"]

        cursor.execute("SELECT COUNT(*) AS core_docs FROM so_van_ban WHERE nhom_vong_doi = 'CORE_DIRECTIVE';")
        core_docs = cursor.fetchone()["core_docs"]

        cursor.execute("SELECT COUNT(*) AS thematic_docs FROM so_van_ban WHERE nhom_vong_doi = 'THEMATIC_CASE';")
        thematic_docs = cursor.fetchone()["thematic_docs"]

        cursor.execute("SELECT COUNT(*) AS links_count FROM van_ban_lien_ket;")
        links_count = cursor.fetchone()["links_count"]

    return {
        "total_documents": total_docs,
        "total_docs": total_docs,
        "total_chunks": total_chunks,
        "core_directives": core_docs,
        "core_docs": core_docs,
        "thematic_cases": thematic_docs,
        "thematic_docs": thematic_docs,
        "links_count": links_count,
    }


def list_rag_documents(limit: int = 100) -> List[Dict[str, Any]]:
    """Liệt kê danh sách các văn bản đã nạp chính thức trong kho RAG."""
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            vb.doc_id,
            vb.so_hieu_vb,
            vb.the_loai_vb,
            vb.co_quan_ban_hanh,
            vb.co_quan_ban_hanh_code,
            vb.ngay_ban_hanh,
            vb.nam_ban_hanh,
            vb.trich_yeu,
            vb.nhom_vong_doi,
            vb.ma_chuyen_de,
            COALESCE(cd.ten_chuyen_de, vb.ma_chuyen_de) AS ten_chuyen_de,
            vb.trang_thai_hieu_luc,
            vb.file_path,
            COUNT(c.chunk_id) AS chunk_count
        FROM so_van_ban vb
        LEFT JOIN danh_muc_chuyen_de cd ON vb.ma_chuyen_de = cd.ma_chuyen_de
        LEFT JOIN van_ban_chunks c ON vb.doc_id = c.doc_id
        GROUP BY vb.doc_id
        ORDER BY vb.ngay_ban_hanh DESC, vb.created_at DESC
        LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def delete_document_from_rag(doc_id: str) -> bool:
    """Xoá một văn bản và toàn bộ chunks/links của nó khỏi kho RAG."""
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM van_ban_fts WHERE doc_id = ?;", (doc_id,))
        cursor.execute("DELETE FROM van_ban_chunks WHERE doc_id = ?;", (doc_id,))
        cursor.execute("DELETE FROM van_ban_lien_ket WHERE vb_nguon_doc_id = ?;", (doc_id,))
        cursor.execute("DELETE FROM so_van_ban WHERE doc_id = ?;", (doc_id,))
        logger.info(f"Đã xoá văn bản {doc_id} khỏi kho RAG.")
        return cursor.rowcount > 0


def get_document_detail(doc_id: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin chi tiết đầy đủ của một văn bản trong kho RAG (kèm chunks và links)."""
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            vb.*,
            COALESCE(cd.ten_chuyen_de, vb.ma_chuyen_de) AS ten_chuyen_de
        FROM so_van_ban vb
        LEFT JOIN danh_muc_chuyen_de cd ON vb.ma_chuyen_de = cd.ma_chuyen_de
        WHERE vb.doc_id = ?;
        """, (doc_id,))
        doc_row = cursor.fetchone()
        if not doc_row:
            return None

        doc_dict = dict(doc_row)

        # Lấy toàn bộ chunks của văn bản
        cursor.execute("""
        SELECT chunk_id, sub_doc_owner, section_path, chunk_type, context_header, chunk_text
        FROM van_ban_chunks
        WHERE doc_id = ?
        ORDER BY chunk_id ASC;
        """, (doc_id,))
        doc_dict["chunks"] = [dict(r) for r in cursor.fetchall()]

        # Lấy liên kết căn cứ trích dẫn
        cursor.execute("""
        SELECT link_id, vb_dich_so_hieu, loai_quan_he, ghi_chu_quan_he
        FROM van_ban_lien_ket
        WHERE vb_nguon_doc_id = ?;
        """, (doc_id,))
        doc_dict["citations"] = [dict(r) for r in cursor.fetchall()]

        return doc_dict


def update_document_metadata(doc_id: str, updates: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Cập nhật siêu dữ liệu của văn bản đã có trong kho RAG (Update).
    Đồng bộ cập nhật sang bảng tìm kiếm toàn văn FTS5.
    """
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM so_van_ban WHERE doc_id = ?;", (doc_id,))
        existing = cursor.fetchone()
        if not existing:
            return False, f"Không tìm thấy văn bản {doc_id} để cập nhật.", {}

        so_hieu = updates.get("so_hieu_vb", existing["so_hieu_vb"]).strip()
        ngay = updates.get("ngay_ban_hanh", existing["ngay_ban_hanh"])
        co_quan = updates.get("co_quan_ban_hanh", existing["co_quan_ban_hanh"])
        co_quan_code = updates.get("co_quan_ban_hanh_code", existing["co_quan_ban_hanh_code"])
        the_loai = updates.get("the_loai_vb", existing["the_loai_vb"])
        nhom_vong_doi = updates.get("nhom_vong_doi", existing["nhom_vong_doi"])
        ma_chuyen_de = updates.get("ma_chuyen_de", existing["ma_chuyen_de"])
        trich_yeu = updates.get("trich_yeu", existing["trich_yeu"]).strip()
        trang_thai = updates.get("trang_thai_hieu_luc", existing["trang_thai_hieu_luc"])
        thay_the_boi = updates.get("bi_thay_the_boi_so_hieu", existing["bi_thay_the_boi_so_hieu"])

        cursor.execute("""
        UPDATE so_van_ban
        SET so_hieu_vb = ?,
            ngay_ban_hanh = ?,
            co_quan_ban_hanh = ?,
            co_quan_ban_hanh_code = ?,
            the_loai_vb = ?,
            nhom_vong_doi = ?,
            ma_chuyen_de = ?,
            trich_yeu = ?,
            trang_thai_hieu_luc = ?,
            bi_thay_the_boi_so_hieu = ?
        WHERE doc_id = ?;
        """, (so_hieu, ngay, co_quan, co_quan_code, the_loai, nhom_vong_doi, ma_chuyen_de, trich_yeu, trang_thai, thay_the_boi, doc_id))

        # Đồng bộ sang bảng FTS5
        cursor.execute("""
        UPDATE van_ban_fts
        SET so_hieu_vb = ?,
            trich_yeu = ?
        WHERE doc_id = ?;
        """, (so_hieu, trich_yeu, doc_id))

        logger.info(f"Đã cập nhật siêu dữ liệu văn bản: {doc_id} - {so_hieu}")

    updated_detail = get_document_detail(doc_id)
    return True, f"Cập nhật thông tin văn bản '{so_hieu}' thành công!", updated_detail or {}


# ==============================================================================
# 2. QUY TRÌNH NẠP CÓ KIỂM SOÁT (HUMAN-IN-THE-LOOP INGESTION)
# ==============================================================================

def classify_thematic_domain(trich_yeu: str, full_text: str = "") -> str:
    """
    Tự động xác định chuyên đề công tác của văn bản.
    Quét qua danh mục chuyên đề trong CSDL để tính điểm khớp tốt nhất.
    """
    categories = db_service.get_all_chuyen_de()
    if not categories:
        return "VAN_PHONG_THI_DUA"

    trich_yeu_lower = trich_yeu.lower()
    text_to_scan = f"{trich_yeu_lower} {full_text[:3500].lower()}"

    best_code = "VAN_PHONG_THI_DUA"
    max_score = 0

    for cat in categories:
        score = 0
        ten = cat["ten_chuyen_de"].lower()
        if ten in trich_yeu_lower:
            score += 25

        raw_kw = (cat.get("tu_khoa_nhan_dien") or "").split(",")
        keywords = [k.strip().lower() for k in raw_kw if k.strip()]

        for kw in keywords:
            if not kw:
                continue
            if kw in trich_yeu_lower:
                score += 15 if len(kw.split()) > 1 else 6
            elif kw in text_to_scan:
                score += 4 if len(kw.split()) > 1 else 2

        if score > max_score:
            max_score = score
            best_code = cat["ma_chuyen_de"]

    return best_code


def sync_outgoing_catalog_to_rag(catalog_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Đồng bộ toàn bộ danh mục văn bản đi từ tệp Excel Master vào kho CSDL SQLite RAG
    (bảng `so_van_ban`, `van_ban_chunks` và bảng ảo `van_ban_fts`).
    Cho phép hệ thống tra cứu FTS5 BM25 tức thì 2.021+ văn bản đi từ 2025 đến nay.
    """
    try:
        import openpyxl
        from server.config import DATA_DIR

        target_path = Path(catalog_path) if catalog_path else (DATA_DIR / "danh_muc_van_ban_di_master.xlsx")
        if not target_path.exists():
            fallback = BASE_DIR / "references" / "Danh mục vị trí việc làm" / "Danh mục văn bản đi Đảng uỷ xã Công Hải (Toàn bộ 2025 - 11-11-2026).xlsx"
            if fallback.exists():
                target_path = fallback
            else:
                return {"success": False, "message": f"Không tìm thấy tệp danh mục: {target_path}", "total_synced": 0}

        wb = openpyxl.load_workbook(target_path, read_only=True)
        ws = wb.active

        map_the_loai = {
            'Công văn': 'CV', 'Báo cáo': 'BC', 'Kế hoạch': 'KH', 'Thông báo': 'TB',
            'Quyết định': 'QĐ', 'Chương trình': 'CTr', 'Tờ trình': 'TTr', 'Hướng dẫn': 'HD',
            'Nghị quyết': 'NQ', 'Kết luận': 'KL', 'Quy định': 'QĐi', 'Quy chế': 'QC',
            'Giấy mời': 'GM', 'Đề án': 'ĐA', 'Chỉ thị': 'CT', 'Bản sao': 'BS',
            'Giấy giới thiệu': 'GGT', 'Phương án': 'PA', 'Giấy nghỉ phép': 'GNP'
        }

        total_scanned = 0
        total_synced = 0

        with db_service.get_db_connection() as conn:
            cursor = conn.cursor()

            for r in ws.iter_rows(min_row=10, values_only=True):
                if not r or not any(r):
                    continue

                stt = r[0] if len(r) > 0 and r[0] is not None else (total_scanned + 1)
                id_eoffice = str(r[1] or '').strip() if len(r) > 1 else ''
                trich_yeu = str(r[2] or '').strip() if len(r) > 2 else ''
                so_hieu = str(r[3] or '').strip() if len(r) > 3 else ''
                so_van_ban_col = str(r[6] or 'SỔ VĂN BẢN ĐI ĐẢNG ỦY NHIỆM KỲ 2025-2030').strip() if len(r) > 6 else ''
                ten_the_loai = str(r[7] or 'Công văn').strip() if len(r) > 7 else 'Công văn'
                nguoi_ky = str(r[8] or '').strip() if len(r) > 8 else ''
                ngay_tao_raw = str(r[9] or '').strip() if len(r) > 9 else ''
                file_van_ban = str(r[10] or '').strip() if len(r) > 10 else ''

                if not so_hieu or not trich_yeu:
                    continue

                total_scanned += 1

                iso_date = "2026-01-01"
                nam_ban_hanh = 2026
                if ngay_tao_raw:
                    date_part = ngay_tao_raw.split()[0]
                    if '/' in date_part:
                        parts = date_part.split('/')
                        if len(parts) == 3:
                            try:
                                iso_date = f"{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"
                                nam_ban_hanh = int(parts[2])
                            except Exception:
                                pass
                    elif '-' in date_part:
                        parts = date_part.split('-')
                        if len(parts) == 3:
                            try:
                                iso_date = date_part
                                nam_ban_hanh = int(parts[0])
                            except Exception:
                                pass

                the_loai_code = map_the_loai.get(ten_the_loai, 'CV')

                if the_loai_code in ['NQ', 'QC', 'QĐi']:
                    trong_so = 100
                elif the_loai_code in ['CT', 'CTr', 'KH', 'KL', 'QĐ']:
                    trong_so = 80
                elif the_loai_code in ['BC', 'TTr', 'HD']:
                    trong_so = 60
                elif the_loai_code in ['CV', 'TB', 'GM']:
                    trong_so = 40
                else:
                    trong_so = 30

                if 'BCĐ' in so_hieu or '57' in so_hieu:
                    co_quan_ban_hanh = "Ban Chỉ đạo 57 Đảng uỷ xã Công Hải"
                    co_quan_code = "BCD57"
                else:
                    co_quan_ban_hanh = "Đảng uỷ xã Công Hải"
                    co_quan_code = "DU"

                if the_loai_code in ['NQ', 'QC', 'QĐi']:
                    nhom_vong_doi = "LONG_TERM_DIRECTIVE"
                elif 'kiểm điểm' in trich_yeu.lower():
                    nhom_vong_doi = "ANNUAL_ASSESSMENT"
                else:
                    nhom_vong_doi = "THEMATIC_CASE"

                ma_chuyen_de = classify_thematic_domain(trich_yeu)

                doc_id = f"VB-DI-{id_eoffice}" if id_eoffice else f"VB-DI-{stt}"
                file_hash = hashlib.sha256(f"CATALOG_{id_eoffice}_{so_hieu}_{stt}".encode('utf-8')).hexdigest()
                file_path = f"master_catalog:row_{stt}:{file_van_ban[:200]}"

                cursor.execute("""
                INSERT INTO so_van_ban (
                    doc_id, file_hash, ma_ho_so_eoffice, so_hieu_vb, loai_luong,
                    the_loai_vb, cap_ban_hanh, co_quan_ban_hanh, co_quan_ban_hanh_code,
                    ngay_ban_hanh, nam_ban_hanh, giai_doan_lich_su, trich_yeu,
                    nhom_vong_doi, trong_so_tham_quyen, ma_chuyen_de, trang_thai_hieu_luc,
                    nguoi_ky, file_path, created_at
                ) VALUES (?, ?, ?, ?, 'VAN_BAN_DI', ?, 'XA_CONG_HAI', ?, ?, ?, ?, 'SAU_SAP_NHAP', ?, ?, ?, ?, 'CON_HIEU_LUC', ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(doc_id) DO UPDATE SET
                    so_hieu_vb=excluded.so_hieu_vb,
                    trich_yeu=excluded.trich_yeu,
                    the_loai_vb=excluded.the_loai_vb,
                    ngay_ban_hanh=excluded.ngay_ban_hanh,
                    nam_ban_hanh=excluded.nam_ban_hanh,
                    nguoi_ky=excluded.nguoi_ky,
                    ma_chuyen_de=excluded.ma_chuyen_de;
                """, (
                    doc_id, file_hash, id_eoffice, so_hieu, the_loai_code,
                    co_quan_ban_hanh, co_quan_code, iso_date, nam_ban_hanh,
                    trich_yeu, nhom_vong_doi, trong_so, ma_chuyen_de,
                    nguoi_ky, file_path
                ))

                cursor.execute("DELETE FROM van_ban_chunks WHERE doc_id = ?;", (doc_id,))
                cursor.execute("DELETE FROM van_ban_fts WHERE doc_id = ?;", (doc_id,))

                context_hdr = f"[Văn bản đi: {so_hieu} | {co_quan_ban_hanh} | Ngày: {iso_date} | Thể loại: {ten_the_loai} | Người ký: {nguoi_ky}]"
                chunk_text = (
                    f"{context_hdr}\n"
                    f"- Số ký hiệu: {so_hieu}\n"
                    f"- Thể loại văn bản: {ten_the_loai} ({the_loai_code})\n"
                    f"- Ngày ban hành: {iso_date}\n"
                    f"- Người ký: {nguoi_ky}\n"
                    f"- Cơ quan ban hành: {co_quan_ban_hanh}\n"
                    f"- Sổ văn bản: {so_van_ban_col}\n"
                    f"- Trích yếu nội dung: {trich_yeu}\n"
                    f"- Danh mục tệp đính kèm: {file_van_ban}\n"
                    f"- Mã lưu trữ eOffice: {id_eoffice}"
                )

                cursor.execute("""
                INSERT INTO van_ban_chunks (
                    doc_id, sub_doc_owner, section_path, chunk_type, context_header, chunk_text
                ) VALUES (?, 'TAP_THE', 'Thông tin định danh & Trích yếu', 'PROSE', ?, ?);
                """, (doc_id, context_hdr, chunk_text))
                chunk_id = cursor.lastrowid

                cursor.execute("""
                INSERT INTO van_ban_fts (
                    chunk_id, doc_id, so_hieu_vb, trich_yeu, section_path, chunk_text
                ) VALUES (?, ?, ?, ?, 'Thông tin định danh & Trích yếu', ?);
                """, (chunk_id, doc_id, so_hieu, trich_yeu, chunk_text))

                total_synced += 1

        logger.info(f"Đã đồng bộ {total_synced}/{total_scanned} văn bản đi từ Master Excel vào kho RAG.")
        return {
            "success": True,
            "message": f"Đã đồng bộ thành công {total_synced} văn bản đi vào kho RAG và chỉ mục FTS5.",
            "total_synced": total_synced,
            "file_source": str(target_path.name)
        }
    except Exception as ex:
        logger.error(f"Lỗi khi đồng bộ danh mục văn bản đi vào RAG: {ex}", exc_info=True)
        return {"success": False, "message": f"Lỗi đồng bộ: {str(ex)}", "total_synced": 0}


def preview_document_for_review(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Bước 1 của quy trình có kiểm soát:
    Đọc tệp, trích xuất siêu dữ liệu, sinh thử các chunks và citations
    nhưng CHƯA LƯU VÀO CSDL để cán bộ kiểm tra và chỉnh sửa.
    """
    abs_path = Path(file_path).resolve()
    if not abs_path.exists():
        return False, f"Không tìm thấy tệp: {file_path}", {}

    try:
        # 1. Đọc văn bản
        doc_data = extract_document_text(str(abs_path))

        # 2. Chốt chặn độ MẬT (Secret Gatekeeper)
        if doc_data.get("is_secret"):
            logger.warning(f"Chốt chặn độ mật phát hiện: {abs_path.name}")
            return False, doc_data.get("secret_warning", "Tài liệu đóng dấu MẬT không được nạp vào hệ thống."), {}

        full_text = doc_data.get("text", "")
        if not full_text.strip():
            return False, "Văn bản không có nội dung chữ (có thể là file scan ảnh hoặc mờ).", {}

        # 3. Trích xuất siêu dữ liệu sơ bộ
        meta = doc_data.get("metadata", {})
        fn_meta = doc_data.get("filename_metadata", {})

        so_hieu = meta.get("so_hieu") or fn_meta.get("so_hieu") or f"-{fn_meta.get('the_loai', 'VB')}/DU"
        so_hieu = re.sub(r'\s+', '', so_hieu)

        raw_date = meta.get("ngay_thang", "")
        iso_date = datetime.now().strftime("%Y-%m-%d")
        if raw_date:
            parts = raw_date.split("/")
            if len(parts) == 3:
                iso_date = f"{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"

        co_quan_code = fn_meta.get("co_quan_code") or ("DU" if "ĐU" in so_hieu else ("UBND" if "UBND" in so_hieu else "TU"))
        co_quan_name = meta.get("co_quan_ban_hanh") or ("Đảng uỷ xã Công Hải" if co_quan_code == "DU" else "Uỷ ban nhân dân xã")
        the_loai = fn_meta.get("the_loai") or ("NQ" if "NQ" in so_hieu else ("KH" if "KH" in so_hieu else ("BC" if "BC" in so_hieu else "CV")))
        trich_yeu = fn_meta.get("trich_yeu") or meta.get("trich_yeu") or abs_path.stem

        nhom_vong_doi = "THEMATIC_CASE"
        if the_loai in ["NQ", "QC", "CTr"]:
            nhom_vong_doi = "CORE_DIRECTIVE"
        elif the_loai in ["GM", "BS"]:
            nhom_vong_doi = "EPHEMERAL_EVENT"

        # 4. Tự động nhận diện chuyên đề công tác (Thematic Domain)
        detected_chuyen_de = classify_thematic_domain(trich_yeu, full_text)
        all_categories = db_service.get_all_chuyen_de()

        # Bóc tách thử các căn cứ liên kết
        citations = []
        can_cu_matches = re.findall(
            r'(?:Căn\s+cứ|Thực\s+hiện)\s+([^\n\r;]+?(?:số\s+)?([0-9]+[A-Za-z0-9\-\/]*(?:NQ|KH|QĐ|TB|KL|CT|CTr|CV)[A-Za-z0-9\-\/]*)[^\n\r;]*)',
            full_text[:4000], re.IGNORECASE
        )
        for full_phrase, matched_so in can_cu_matches:
            matched_so = matched_so.strip()
            if matched_so and matched_so != so_hieu:
                citations.append({
                    "vb_dich_so_hieu": matched_so,
                    "loai_quan_he": "THUC_HIEN_CHI_DAO" if "thực hiện" in full_phrase.lower() else "CAN_CU_PHAP_LY",
                    "ghi_chu": full_phrase[:150]
                })

        # Bóc tách thử các đoạn chunks
        preview_chunks = generate_chunks_preview(so_hieu, trich_yeu, co_quan_name, iso_date, full_text)

        preview_payload = {
            "file_path": str(abs_path),
            "file_name": abs_path.name,
            "file_size_kb": round(abs_path.stat().st_size / 1024, 1),
            "so_hieu_vb": so_hieu,
            "ngay_ban_hanh": iso_date,
            "co_quan_ban_hanh": co_quan_name,
            "co_quan_ban_hanh_code": co_quan_code,
            "the_loai_vb": the_loai,
            "nhom_vong_doi": nhom_vong_doi,
            "ma_chuyen_de": detected_chuyen_de,
            "thematic_categories": all_categories,
            "trich_yeu": trich_yeu,
            "thay_the_so_hieu": "",
            "estimated_chunks": len(preview_chunks),
            "preview_chunks": preview_chunks[:3],  # Trả về 3 chunk đầu để cán bộ đối soát
            "citations": citations,
            "full_text": full_text
        }

        # Kiểm tra nếu văn bản có cụm thay thế
        thay_the_match = re.search(r'(?:thay\s+thế|bãi\s+bỏ)\s+(?:quyết\s+định|thông\s+báo|kế\s+hoạch)?\s*số\s*([0-9A-Za-z\-\/]+)', full_text[:3000], re.IGNORECASE)
        if thay_the_match:
            preview_payload["thay_the_so_hieu"] = thay_the_match.group(1).strip()

        return True, "Trích xuất xem trước thành công. Chờ cán bộ kiểm duyệt.", preview_payload

    except Exception as ex:
        logger.error(f"Lỗi xem trước văn bản: {ex}", exc_info=True)
        return False, f"Lỗi phân tích văn bản: {str(ex)}", {}


CHUNK_WORD_LIMIT = 400
CHUNK_OVERLAP_WORDS = 80


def generate_chunks_preview(
    so_hieu: str,
    trich_yeu: str,
    co_quan: str,
    ngay_iso: str,
    full_text: str
) -> List[Dict[str, Any]]:
    """
    Tạo danh sách các đoạn trích (chunks) theo cửa sổ trượt (Sliding Window Overlap 80 từ)
    và bảo toàn ngữ cảnh bảng biểu, chủ thể cá nhân, phân cấp đề mục.
    """
    lines = full_text.split("\n")
    chunks: List[Dict[str, Any]] = []

    current_owner = "TAP_THE"
    current_section = "Phần mở đầu"
    buffer: List[str] = []
    word_count = 0
    table_header_context = ""

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        # Nhận diện chủ thể kiểm điểm cá nhân
        ca_nhan_match = re.search(r'(?:B\.\s+ĐỐI\s+VỚI\s+CÁ\s+NHÂN|BÁO\s+CÁO\s+KIỂM\s+ĐIỂM\s+CÁ\s+NHÂN|Họ\s+và\s+tên\s*:\s*([A-Za-zÀ-Ỹà-ỹ\s]+))', line_strip, re.IGNORECASE)
        if ca_nhan_match:
            name = ca_nhan_match.group(1).strip() if ca_nhan_match.group(1) else "Cán bộ lãnh đạo"
            current_owner = f"CA_NHAN: {name}"
            current_section = f"Kiểm điểm cá nhân: {name}"

        # Nhận diện đề mục văn bản La Mã
        heading_match = re.match(r'^(I|II|III|IV|V|VI|Phần\s+[A-Z]|Mục\s+[0-9]+)\.?\s+(.+)', line_strip)
        if heading_match:
            current_section = f"{heading_match.group(1)}. {heading_match.group(2)[:60]}"

        # Nhận diện và lưu tiêu đề bảng biểu
        is_table = line_strip.startswith("|") or "[BẢNG BIỂU]" in line_strip
        if is_table and not table_header_context and ("STT" in line_strip or "Nội dung" in line_strip or "Chỉ tiêu" in line_strip):
            table_header_context = line_strip[:120]

        buffer.append(line_strip)
        word_count += len(line_strip.split())

        # Khi vượt quá ngưỡng 400 từ -> flush chunk kèm 80 từ gối đầu
        if word_count >= CHUNK_WORD_LIMIT:
            chunk_body = "\n".join(buffer)
            table_extra = f" | Tiêu đề bảng: {table_header_context}" if is_table and table_header_context else ""
            context_hdr = f"[Văn bản: {so_hieu} | {co_quan} | Ngày: {ngay_iso} | Chủ thể: {current_owner} | {current_section}{table_extra}]"
            
            chunks.append({
                "sub_doc_owner": current_owner,
                "section_path": current_section,
                "chunk_type": "TABLE_ROW" if is_table else "PROSE",
                "context_header": context_hdr,
                "chunk_text": f"{context_hdr}\n{chunk_body}"
            })

            # Cơ chế cửa sổ trượt (Sliding Window Overlap): Giữ lại 80 từ cuối cho đoạn tiếp theo
            all_words = chunk_body.split()
            overlap_words = all_words[-CHUNK_OVERLAP_WORDS:] if len(all_words) > CHUNK_OVERLAP_WORDS else []
            buffer = [" ".join(overlap_words)] if overlap_words else []
            word_count = len(overlap_words)

    if buffer:
        chunk_body = "\n".join(buffer)
        table_extra = f" | Tiêu đề bảng: {table_header_context}" if table_header_context else ""
        context_hdr = f"[Văn bản: {so_hieu} | {co_quan} | Ngày: {ngay_iso} | Chủ thể: {current_owner} | {current_section}{table_extra}]"
        chunks.append({
            "sub_doc_owner": current_owner,
            "section_path": current_section,
            "chunk_type": "PROSE",
            "context_header": context_hdr,
            "chunk_text": f"{context_hdr}\n{chunk_body}"
        })

    return chunks


def commit_reviewed_document(reviewed: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Bước 2 của quy trình có kiểm soát:
    Nhận dữ liệu đã được cán bộ kiểm tra và phê duyệt/chỉnh sửa -> Ghi chính thức vào CSDL.
    """
    try:
        file_path = reviewed.get("file_path", "")
        so_hieu = reviewed.get("so_hieu_vb", "").strip()
        ngay_ban_hanh = reviewed.get("ngay_ban_hanh", datetime.now().strftime("%Y-%m-%d"))
        co_quan_code = reviewed.get("co_quan_ban_hanh_code", "DU")
        co_quan_name = reviewed.get("co_quan_ban_hanh", "Đảng uỷ xã Công Hải")
        the_loai = reviewed.get("the_loai_vb", "CV")
        nhom_vong_doi = reviewed.get("nhom_vong_doi", "THEMATIC_CASE")
        trich_yeu = reviewed.get("trich_yeu", "").strip()
        full_text = reviewed.get("full_text", "")
        if not full_text and file_path and Path(file_path).exists():
            doc_data = extract_document_text(str(file_path))
            full_text = doc_data.get("text", "")
        thay_the_so_hieu = reviewed.get("thay_the_so_hieu", "").strip()

        if not so_hieu or not trich_yeu:
            return False, "Thiếu số hiệu văn bản hoặc trích yếu nội dung.", {}

        # Tính toán trọng số thẩm quyền
        trong_so = 60
        if the_loai in ["NQ", "QC"]:
            trong_so = 100
        elif the_loai in ["CTr", "KH", "KL"]:
            trong_so = 80
        elif the_loai == "CV":
            trong_so = 40

        # Tạo file hash
        file_hash = None
        if file_path and Path(file_path).exists():
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        else:
            file_hash = hashlib.sha256(f"{so_hieu}_{ngay_ban_hanh}_{datetime.now()}".encode("utf-8")).hexdigest()

        ma_chuyen_de = reviewed.get("ma_chuyen_de") or "VAN_PHONG_THI_DUA"

        # Lưu văn bản vào so_van_ban
        doc_record = {
            "file_path": file_path,
            "file_hash": file_hash,
            "so_hieu_vb": so_hieu,
            "loai_luong": "VAN_BAN_DEN" if "van_ban_den" in file_path else "VAN_BAN_DI",
            "the_loai_vb": the_loai,
            "cap_ban_hanh": "XA_CONG_HAI" if co_quan_code in ["DU", "UBND"] else "TINH_KHANH_HOA",
            "co_quan_ban_hanh": co_quan_name,
            "co_quan_ban_hanh_code": co_quan_code,
            "ngay_ban_hanh": ngay_ban_hanh,
            "trich_yeu": trich_yeu,
            "nhom_vong_doi": nhom_vong_doi,
            "trong_so_tham_quyen": trong_so,
            "ma_chuyen_de": ma_chuyen_de,
            "thay_the_so_hieu": thay_the_so_hieu,
        }
        doc_id = db_service.add_or_update_document(doc_record)

        # Lưu liên kết căn cứ đã duyệt
        citations = reviewed.get("citations", [])
        for c in citations:
            matched_so = c.get("vb_dich_so_hieu", "").strip()
            if matched_so and matched_so != so_hieu:
                db_service.add_document_link(
                    doc_id, so_hieu, matched_so,
                    c.get("loai_quan_he", "CAN_CU_PHAP_LY"),
                    c.get("ghi_chu", "")
                )

        # Cắt chunks và đánh chỉ mục FTS5 kèm Vector Embedding
        from server.services import embedding_service
        chunks = generate_chunks_preview(so_hieu, trich_yeu, co_quan_name, ngay_ban_hanh, full_text)
        saved_chunks = 0
        for ch in chunks:
            # Tự động sinh vector embedding nhị phân qua Ollama (nếu sẵn sàng)
            emb_blob = embedding_service.get_embedding(ch["chunk_text"], timeout=3.0)
            db_service.insert_chunk(
                doc_id=doc_id,
                so_hieu_vb=so_hieu,
                trich_yeu=trich_yeu,
                section_path=ch["section_path"],
                context_header=ch["context_header"],
                chunk_text=ch["chunk_text"],
                sub_doc_owner=ch["sub_doc_owner"],
                chunk_type=ch["chunk_type"],
                embedding_blob=emb_blob
            )
            saved_chunks += 1

        logger.info(f"Cán bộ đã duyệt và nạp văn bản chính thức: {so_hieu} (Doc ID: {doc_id}, {saved_chunks} chunks)")

        # TỰ ĐỘNG NỐI DÒNG VÀO FILE EXCEL MASTER NẾU LÀ VĂN BẢN ĐI
        if "VAN_BAN_DI" in doc_record.get("loai_luong", "") or "ĐU" in so_hieu:
            try:
                append_outgoing_document_to_master(
                    so_hieu=so_hieu,
                    trich_yeu=trich_yeu,
                    the_loai=the_loai,
                    nguoi_ky=reviewed.get("nguoi_ky") or "",
                    ngay_ban_hanh=ngay_ban_hanh,
                    file_name=Path(file_path).name if file_path else ""
                )
            except Exception as ex_excel:
                logger.warning(f"Lỗi khi nối vào file Excel Master: {ex_excel}")

        return True, f"Đã phê duyệt và nạp thành công văn bản {so_hieu} vào kho RAG ({saved_chunks} đoạn).", {
            "doc_id": doc_id,
            "so_hieu": so_hieu,
            "chunks": saved_chunks
        }

    except Exception as ex:
        logger.error(f"Lỗi khi phê duyệt văn bản: {ex}", exc_info=True)
        return False, f"Lỗi nạp văn bản: {str(ex)}", {}


# ==============================================================================
# 3. TRUY XUẤT ĐÍCH DANH & GIỎ NGỮ CẢNH HYBRID RAG
# ==============================================================================

def retrieve_direct_hit(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tra cứu đích danh văn bản theo thực thể số hiệu đã phân tích từ query_analyzer.
    Không qua FTS5, không qua BM25, truy vấn trực tiếp CSDL SQLite.
    Đảm bảo 100% độ chính xác cho các câu hỏi đích danh (NQ 11, Kế hoạch 69...).
    """
    if not entities:
        return {
            "context_text": "",
            "citations": [],
            "total_slots": 0,
            "not_found": []
        }

    all_patterns = []
    canonical_names = []
    for ent in entities:
        all_patterns.extend(ent.get("search_patterns", []))
        canonical_names.append(ent.get("canonical", ""))

    matched_chunks = db_service.lookup_by_so_hieu_patterns(all_patterns, limit=4)

    if not matched_chunks:
        logger.info(f"Tra cứu đích danh không tìm thấy văn bản trong kho: {canonical_names}")
        return {
            "context_text": "",
            "citations": [],
            "total_slots": 0,
            "not_found": canonical_names
        }

    context_lines = [
        "=== KHO TRI THỨC VĂN BẢN — TRA CỨU ĐÍCH DANH (DIRECT HIT) ===",
        "[LƯU Ý: Đây là văn bản đích danh được truy xuất trực tiếp từ CSDL lưu trữ chính thức của Đảng uỷ xã Công Hải.]"
    ]
    citations = []

    for idx, doc in enumerate(matched_chunks, 1):
        so = doc.get("so_hieu_vb", "")
        trich_yeu = doc.get("trich_yeu", "")
        vong_doi = doc.get("nhom_vong_doi", "CORE_DIRECTIVE")
        tier_label = "NỀN TẢNG" if vong_doi == "CORE_DIRECTIVE" else "CHUYÊN ĐỀ"
        body = doc.get("chunk_text", "")
        header = doc.get("context_header", "")

        context_lines.append(f"\n[VĂN BẢN ĐÍCH DANH {idx} - {so} - TẦNG {tier_label}]:\n{body}")
        citations.append({
            "slot_index": idx,
            "so_hieu": so,
            "trich_yeu": trich_yeu,
            "tier": tier_label,
            "header": header
        })

    return {
        "context_text": "\n".join(context_lines),
        "citations": citations,
        "total_slots": len(matched_chunks),
        "not_found": []
    }


def retrieve_hybrid_context(
    query: str,
    workflow_type: Optional[str] = None,
    max_slots: int = 6
) -> Dict[str, Any]:
    """
    Chiến lược truy xuất True Hybrid RAG:
    - Bước 1: FTS5 BM25 weighted lọc Top 40 ứng viên.
    - Bước 2: Reranking bằng RRF (Reciprocal Rank Fusion) kết hợp Gemini Vector Embedding.
    - Bước 3: Phân bổ Slot Thích ứng (Score-First) kết hợp Sàn Đa dạng (Diversity Floor).
    - Bước 4: 1-Hop Citation Expansion kéo theo văn bản căn cứ liên kết.
    """
    empty_resp = {
        "context_text": "",
        "citations": [],
        "total_slots": 0,
        "slot_breakdown": {"core_directive": 0, "thematic_case": 0, "citation_linked": 0}
    }
    if not query.strip():
        return empty_resp

    candidates = db_service.search_fts_bm25(query=query, limit=40)
    if not candidates:
        return empty_resp

    # BƯỚC 2: RERANKING BẰNG RRF (RECIPROCAL RANK FUSION) VỚI GEMINI VECTOR EMBEDDING
    from server.services import embedding_service
    query_emb_blob = embedding_service.get_embedding(query, timeout=6.0)
    query_vec = embedding_service.unpack_embedding(query_emb_blob) if query_emb_blob else []

    bm25_ranks = {c["chunk_id"]: idx + 1 for idx, c in enumerate(candidates)}
    vector_ranks = {}

    if query_vec:
        scored_vecs = []
        for c in candidates:
            c_blob = c.get("embedding")
            c_vec = embedding_service.unpack_embedding(c_blob) if c_blob else []
            sim = embedding_service.cosine_similarity(query_vec, c_vec) if c_vec else 0.0
            scored_vecs.append((c["chunk_id"], sim))

        scored_vecs.sort(key=lambda x: x[1], reverse=True)
        vector_ranks = {cid: idx + 1 for idx, (cid, sim) in enumerate(scored_vecs)}

    for c in candidates:
        cid = c["chunk_id"]
        r_bm25 = bm25_ranks.get(cid, 60)
        r_vec = vector_ranks.get(cid, 60) if vector_ranks else r_bm25
        c["rrf_score"] = (1.0 / (60.0 + r_bm25)) + (1.0 / (60.0 + r_vec))

    # Tái sắp xếp ứng viên theo RRF score giảm dần
    candidates.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

    # BƯỚC 3: PHÂN BỔ SLOT THÍCH ỨNG THEO ĐIỂM (SCORE-FIRST) + SÀN ĐA DẠNG (DIVERSITY FLOOR)
    selected_slots: List[Dict[str, Any]] = []
    selected_doc_ids = set()

    for cand in candidates:
        if cand["doc_id"] not in selected_doc_ids and len(selected_slots) < max_slots:
            selected_slots.append(cand)
            selected_doc_ids.add(cand["doc_id"])

    # Diversity Floor: Nếu không có văn bản CORE_DIRECTIVE nào trong các slot đã chọn,
    # nhưng có ứng viên CORE_DIRECTIVE trong top candidates với điểm tương đối tốt (>= 30% top score),
    # thay thế slot cuối cùng bằng văn bản nền tảng này để đảm bảo định hướng chính trị tổng thể.
    has_core = any(s.get("nhom_vong_doi") == "CORE_DIRECTIVE" for s in selected_slots)
    if not has_core and len(selected_slots) >= 2:
        top_score = selected_slots[0].get("rrf_score", 0.0)
        best_core = next(
            (c for c in candidates if c.get("nhom_vong_doi") == "CORE_DIRECTIVE" and c["doc_id"] not in selected_doc_ids),
            None
        )
        if best_core and best_core.get("rrf_score", 0.0) >= top_score * 0.3:
            selected_slots[-1] = best_core
            selected_doc_ids.add(best_core["doc_id"])

    # Kéo theo từ Đồ thị Căn cứ (1-Hop Citation Expansion) nếu còn chỗ
    citation_limit = 1 if max_slots >= 4 else 0
    slot_citations: List[Dict[str, Any]] = []
    if citation_limit > 0:
        for item in selected_slots[:3]:
            so_hieu = item.get("so_hieu_vb")
            if so_hieu:
                links = db_service.get_linked_documents(so_hieu)
                for l in links:
                    linked_so = l["vb_dich_so_hieu"]
                    linked_chunks = db_service.search_fts_bm25(query=linked_so, limit=1)
                    for lc in linked_chunks:
                        if lc["doc_id"] not in selected_doc_ids and len(slot_citations) < citation_limit:
                            slot_citations.append(lc)
                            selected_doc_ids.add(lc["doc_id"])
                            break
            if len(slot_citations) >= citation_limit:
                break

    if slot_citations:
        final_slots = (selected_slots[:max_slots - len(slot_citations)] + slot_citations)[:max_slots]
    else:
        final_slots = selected_slots[:max_slots]

    context_lines = [
        "=== KHO TRI THỨC VÀ CĂN CỨ VĂN BẢN ĐÃ ĐỐI SOÁT (HYBRID RAG) ===",
        "[LƯU Ý QUAN TRỌNG: Kho CSDL văn bản Đảng uỷ xã hiện lưu trữ các văn bản đi nhiệm kỳ 2025-2030. Các đoạn trích dưới đây là các đoạn trích nội dung liên quan nhất được trích xuất phục vụ câu hỏi hiện tại.]"
    ]
    citations = []

    core_count = 0
    thematic_count = 0
    for idx, slot in enumerate(final_slots, 1):
        is_cit = slot in slot_citations
        vong_doi = slot.get("nhom_vong_doi", "THEMATIC_CASE")
        if is_cit:
            tier_label = "VĂN BẢN GỐC LIÊN QUAN"
        elif vong_doi == "CORE_DIRECTIVE":
            tier_label = "NỀN TẢNG"
            core_count += 1
        else:
            tier_label = "CHUYÊN ĐỀ"
            thematic_count += 1

        header = slot.get("context_header", "")
        body = slot.get("chunk_text", "")
        so = slot.get("so_hieu_vb", "")
        trich_yeu = slot.get("trich_yeu", "")

        context_lines.append(f"\n[TRÍCH DẪN {idx} - TẦNG {tier_label}]:\n{body}")
        citations.append({
            "slot_index": idx,
            "so_hieu": so,
            "trich_yeu": trich_yeu,
            "tier": tier_label,
            "header": header
        })

    return {
        "context_text": "\n".join(context_lines),
        "citations": citations,
        "total_slots": len(final_slots),
        "slot_breakdown": {
            "core_directive": core_count,
            "thematic_case": thematic_count,
            "citation_linked": len(slot_citations)
        }
    }


# ==============================================================================
# 4. TRUY VẤN THỐNG KÊ & TỔNG HỢP VĂN BẢN (AGGREGATE STATS QUERY)
# ==============================================================================

DOC_TYPE_NAMES = {
    'CV': 'Công văn', 'BS': 'Bản sao', 'BC': 'Báo cáo', 'KH': 'Kế hoạch',
    'TB': 'Thông báo', 'QĐ': 'Quyết định', 'CTr': 'Chương trình', 'TTr': 'Tờ trình',
    'HD': 'Hướng dẫn', 'NQ': 'Nghị quyết', 'KL': 'Kết luận', 'QĐi': 'Quy định',
    'QC': 'Quy chế', 'GM': 'Giấy mời', 'ĐA': 'Đề án', 'CT': 'Chỉ thị',
    'GGT': 'Giấy giới thiệu', 'PA': 'Phương án', 'GNP': 'Giấy nghỉ phép'
}

MAP_KEYWORDS_THE_LOAI = {
    'quyết định': ('QĐ', 'Quyết định'),
    'công văn': ('CV', 'Công văn'),
    'kế hoạch': ('KH', 'Kế hoạch'),
    'nghị quyết': ('NQ', 'Nghị quyết'),
    'báo cáo': ('BC', 'Báo cáo'),
    'thông báo': ('TB', 'Thông báo'),
    'chương trình': ('CTr', 'Chương trình'),
    'tờ trình': ('TTr', 'Tờ trình'),
    'hướng dẫn': ('HD', 'Hướng dẫn'),
    'kết luận': ('KL', 'Kết luận'),
    'quy định': ('QĐi', 'Quy định'),
    'quy chế': ('QC', 'Quy chế'),
    'đề án': ('ĐA', 'Đề án'),
    'giấy mời': ('GM', 'Giấy mời'),
    'chỉ thị': ('CT', 'Chỉ thị'),
}


def check_and_get_aggregate_stats(query: str) -> Optional[Dict[str, Any]]:
    """
    Nhận diện câu hỏi thống kê / đếm số lượng văn bản trong kho (Aggregation / Stats Query)
    và truy vấn trực tiếp CSDL SQLite để trả về số liệu tổng thể chính xác 100%.
    """
    if not query:
        return None

    # Nhận diện ý định hỏi về số lượng / thống kê văn bản
    has_stat_intent = bool(re.search(
        r'(số\s+lượng|bao\s+nhiêu|tổng\s+số|thống\s+kê|danh\s+sách\s+tổng|tổng\s+hợp\s+số\s+lượng|đã\s+ban\s+hành\s+bao\s+nhiêu|có\s+bao\s+nhiêu|được\s+bao\s+nhiêu|toàn\s+bộ\s+văn\s+bản)',
        query,
        re.IGNORECASE
    ))
    has_doc_term = bool(re.search(
        r'(văn\s+bản|công\s+văn|quyết\s+định|kế\s+hoạch|nghị\s+quyết|thông\s+báo|báo\s+cáo|tờ\s+trình|hướng\s+dẫn|kết\s+luận|chương\s+trình|đề\s+án|quy\s+chế|quy\s+định|giấy\s+mời|hồ\s+sơ)',
        query,
        re.IGNORECASE
    ))

    if not (has_stat_intent and has_doc_term):
        return None

    try:
        with db_service.get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Tổng số văn bản
            cursor.execute("SELECT COUNT(*) AS total FROM so_van_ban;")
            total_docs = cursor.fetchone()["total"]

            if total_docs == 0:
                return None

            # 2. Khoảng thời gian
            cursor.execute("SELECT MIN(ngay_ban_hanh) AS d_min, MAX(ngay_ban_hanh) AS d_max FROM so_van_ban WHERE ngay_ban_hanh != '';")
            row_date = cursor.fetchone()
            d_min = row_date["d_min"] if row_date else "04/08/2025"
            d_max = row_date["d_max"] if row_date else "11/11/2026"

            def fmt_date(d_str: str) -> str:
                if d_str and '-' in d_str:
                    p = d_str.split('-')
                    if len(p) == 3:
                        return f"{p[2]}/{p[1]}/{p[0]}"
                return d_str

            d_min_fmt = fmt_date(d_min)
            d_max_fmt = fmt_date(d_max)

            # 3. Phân bổ theo năm
            cursor.execute("SELECT nam_ban_hanh, COUNT(*) AS cnt FROM so_van_ban GROUP BY nam_ban_hanh ORDER BY nam_ban_hanh ASC;")
            by_year = [(r["nam_ban_hanh"], r["cnt"]) for r in cursor.fetchall()]

            # 4. Phân bổ theo thể loại
            cursor.execute("SELECT the_loai_vb, COUNT(*) AS cnt FROM so_van_ban GROUP BY the_loai_vb ORDER BY cnt DESC;")
            by_type = [(r["the_loai_vb"], r["cnt"]) for r in cursor.fetchall()]

            # 5. Phân bổ theo người ký
            cursor.execute("SELECT nguoi_ky, COUNT(*) AS cnt FROM so_van_ban WHERE nguoi_ky IS NOT NULL AND nguoi_ky != '' GROUP BY nguoi_ky ORDER BY cnt DESC LIMIT 5;")
            by_signer = [(r["nguoi_ky"], r["cnt"]) for r in cursor.fetchall()]

            # Kiểm tra nếu hỏi cụ thể 1 thể loại (VD: "bao nhiêu quyết định")
            target_the_loai = None
            q_lower = query.lower()
            for kw, (code, name) in MAP_KEYWORDS_THE_LOAI.items():
                if kw in q_lower and "văn bản" not in kw:
                    target_the_loai = (code, name)
                    break

            lines = [
                "=== THỐNG KÊ THỰC CHỨNG CHÍNH THỨC TỪ KHO CSDL VĂN BẢN ĐẢNG UỶ (SQLITE WAL) ===",
                f"- Tổng số lượng văn bản đi của Đảng uỷ xã Công Hải nhiệm kỳ 2025-2030 đã ban hành và lưu trữ trong CSDL: {total_docs:,} văn bản.",
                f"- Giai đoạn ban hành: Từ ngày {d_min_fmt} đến ngày {d_max_fmt} (sau khi thực hiện mô hình chính quyền địa phương 02 cấp).",
                f"- Phân bổ theo năm: " + ", ".join([f"Năm {y}: {cnt:,} văn bản" for y, cnt in by_year]),
                "- Cơ cấu phân bổ chi tiết theo thể loại văn bản:"
            ]

            for code, cnt in by_type:
                tname = DOC_TYPE_NAMES.get(code, code)
                lines.append(f"  + {tname}: {cnt:,} văn bản")

            if by_signer:
                lines.append("- Một số cán bộ/lãnh đạo ký văn bản chủ yếu:")
                for sname, cnt in by_signer:
                    lines.append(f"  + Đ/c {sname}: {cnt:,} văn bản")

            # Nếu hỏi thể loại cụ thể
            if target_the_loai:
                code, name = target_the_loai
                cursor.execute("SELECT COUNT(*) AS cnt FROM so_van_ban WHERE the_loai_vb = ?;", (code,))
                tcnt = cursor.fetchone()["cnt"]
                cursor.execute("SELECT so_hieu_vb, trich_yeu, ngay_ban_hanh, nguoi_ky FROM so_van_ban WHERE the_loai_vb = ? ORDER BY ngay_ban_hanh DESC LIMIT 5;", (code,))
                samples = cursor.fetchall()
                lines.append(f"\n[SỐ LIỆU RIÊNG CHO THỂ LOẠI '{name.upper()}']:")
                lines.append(f"- Tổng số {name.lower()} đã ban hành: {tcnt:,} văn bản.")
                lines.append(f"- Một số {name.lower()} tiêu biểu gần đây:")
                for row in samples:
                    lines.append(f"  • {row['so_hieu_vb']} ({fmt_date(row['ngay_ban_hanh'])}): {row['trich_yeu']}")

            lines.append(
                f"\n[CHỈ DẪN NGHIỆP VỤ BẮT BUỘC DÀNH CHO TRỢ LÝ AI]:\n"
                f"1. Cán bộ đang hỏi về số lượng/thống kê văn bản đã ban hành.\n"
                f"2. BẮT BUỘC sử dụng con số TỔNG CỘNG CHÍNH THỨC LÀ {total_docs:,} VĂN BẢN (và bảng cơ cấu thể loại ở trên) để trả lời cán bộ rõ ràng, đầy đủ, chia nhóm số liệu khoa học.\n"
                f"3. TUYỆT ĐỐI KHÔNG được trả lời số lượng chỉ là 5 hay 6 văn bản (con số 5 hay 6 đó chỉ là số mẩu trích dẫn ví dụ trích xuất trên màn hình, không phải toàn bộ kho văn bản)."
            )

            return {
                "stats_text": "\n".join(lines),
                "total_docs": total_docs,
                "is_stats_query": True
            }

    except Exception as ex:
        logger.warning(f"Lỗi khi truy vấn thống kê văn bản: {ex}")
        return None

