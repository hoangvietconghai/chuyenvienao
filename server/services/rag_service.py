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


def generate_chunks_preview(
    so_hieu: str,
    trich_yeu: str,
    co_quan: str,
    ngay_iso: str,
    full_text: str
) -> List[Dict[str, Any]]:
    """Tạo trước danh sách các đoạn trích (chunks) để hiển thị đối soát."""
    lines = full_text.split("\n")
    chunks: List[Dict[str, Any]] = []

    current_owner = "TAP_THE"
    current_section = "Phần mở đầu"
    buffer: List[str] = []
    word_count = 0

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        ca_nhan_match = re.search(r'(?:B\.\s+ĐỐI\s+VỚI\s+CÁ\s+NHÂN|BÁO\s+CÁO\s+KIỂM\s+ĐIỂM\s+CÁ\s+NHÂN|Họ\s+và\s+tên\s*:\s*([A-Za-zÀ-Ỹà-ỹ\s]+))', line_strip, re.IGNORECASE)
        if ca_nhan_match:
            name = ca_nhan_match.group(1).strip() if ca_nhan_match.group(1) else "Cán bộ lãnh đạo"
            current_owner = f"CA_NHAN: {name}"
            current_section = f"Kiểm điểm cá nhân: {name}"

        heading_match = re.match(r'^(I|II|III|IV|V|VI|Phần\s+[A-Z]|Mục\s+[0-9]+)\.?\s+(.+)', line_strip)
        if heading_match:
            current_section = f"{heading_match.group(1)}. {heading_match.group(2)[:60]}"

        is_table = line_strip.startswith("|") or "[BẢNG BIỂU]" in line_strip
        buffer.append(line_strip)
        word_count += len(line_strip.split())

        if word_count >= 450:
            chunk_body = "\n".join(buffer)
            context_hdr = f"[Văn bản: {so_hieu} | {co_quan} | Ngày: {ngay_iso} | Chủ thể: {current_owner} | {current_section}]"
            chunks.append({
                "sub_doc_owner": current_owner,
                "section_path": current_section,
                "chunk_type": "TABLE_ROW" if is_table else "PROSE",
                "context_header": context_hdr,
                "chunk_text": f"{context_hdr}\n{chunk_body}"
            })
            buffer = []
            word_count = 0

    if buffer:
        chunk_body = "\n".join(buffer)
        context_hdr = f"[Văn bản: {so_hieu} | {co_quan} | Ngày: {ngay_iso} | Chủ thể: {current_owner} | {current_section}]"
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

        # Cắt chunks và đánh chỉ mục FTS5
        chunks = generate_chunks_preview(so_hieu, trich_yeu, co_quan_name, ngay_ban_hanh, full_text)
        saved_chunks = 0
        for ch in chunks:
            db_service.insert_chunk(
                doc_id=doc_id,
                so_hieu_vb=so_hieu,
                trich_yeu=trich_yeu,
                section_path=ch["section_path"],
                context_header=ch["context_header"],
                chunk_text=ch["chunk_text"],
                sub_doc_owner=ch["sub_doc_owner"],
                chunk_type=ch["chunk_type"],
                embedding_blob=None
            )
            saved_chunks += 1

        logger.info(f"Cán bộ đã duyệt và nạp văn bản chính thức: {so_hieu} (Doc ID: {doc_id}, {saved_chunks} chunks)")
        return True, f"Đã phê duyệt và nạp thành công văn bản {so_hieu} vào kho RAG ({saved_chunks} đoạn).", {
            "doc_id": doc_id,
            "so_hieu": so_hieu,
            "chunks": saved_chunks
        }

    except Exception as ex:
        logger.error(f"Lỗi khi phê duyệt văn bản: {ex}", exc_info=True)
        return False, f"Lỗi nạp văn bản: {str(ex)}", {}


# ==============================================================================
# 3. TRUY XUẤT GIỎ NGỮ CẢNH 2 - 4 - 2 (HYBRID RETRIEVAL)
# ==============================================================================

def retrieve_hybrid_context(
    query: str,
    workflow_type: Optional[str] = None,
    max_slots: int = 8
) -> Dict[str, Any]:
    """
    Chiến lược truy xuất "Giỏ Ngữ Cảnh 2 - 4 - 2":
    - Bước 1: FTS5 BM25 lọc nhanh Top 30-50 ứng viên.
    - Slot 1–2 (02 đoạn Nền tảng CORE_DIRECTIVE): Lấy từ Nghị quyết, Quy chế làm việc.
    - Slot 3–6 (04 đoạn Chuyên đề mới nhất THEMATIC_CASE): Lấy từ Kế hoạch, Báo cáo gần nhất.
    - Slot 7–8 (02 đoạn Kéo theo từ Đồ thị Căn cứ 1-Hop Citation): Lấy từ văn bản gốc được viện dẫn.
    """
    if not query.strip():
        return {"context_text": "", "citations": [], "total_slots": 0}

    candidates = db_service.search_fts_bm25(query=query, limit=40)
    if not candidates:
        return {"context_text": "", "citations": [], "total_slots": 0}

    slot_core: List[Dict[str, Any]] = []
    slot_thematic: List[Dict[str, Any]] = []
    selected_doc_ids = set()

    for cand in candidates:
        vong_doi = cand.get("nhom_vong_doi", "THEMATIC_CASE")
        doc_id = cand["doc_id"]

        if vong_doi == "CORE_DIRECTIVE" and len(slot_core) < 2:
            slot_core.append(cand)
            selected_doc_ids.add(doc_id)
        elif vong_doi == "THEMATIC_CASE" and len(slot_thematic) < 4:
            slot_thematic.append(cand)
            selected_doc_ids.add(doc_id)

        if len(slot_core) >= 2 and len(slot_thematic) >= 4:
            break

    for cand in candidates:
        if cand not in slot_core and cand not in slot_thematic:
            if len(slot_thematic) < 4:
                slot_thematic.append(cand)
                selected_doc_ids.add(cand["doc_id"])
            elif len(slot_core) < 2:
                slot_core.append(cand)
                selected_doc_ids.add(cand["doc_id"])

    # Slot 7–8: Kéo theo từ Đồ thị Căn cứ (1-Hop Citation Expansion)
    slot_citations: List[Dict[str, Any]] = []
    for item in (slot_thematic + slot_core)[:4]:
        so_hieu = item.get("so_hieu_vb")
        if so_hieu:
            links = db_service.get_linked_documents(so_hieu)
            for l in links:
                linked_so = l["vb_dich_so_hieu"]
                linked_chunks = db_service.search_fts_bm25(query=linked_so, limit=2)
                for lc in linked_chunks:
                    if lc["doc_id"] not in selected_doc_ids and len(slot_citations) < 2:
                        slot_citations.append(lc)
                        selected_doc_ids.add(lc["doc_id"])
                        break
        if len(slot_citations) >= 2:
            break

    final_slots = slot_core[:2] + slot_thematic[:4] + slot_citations[:2]

    context_lines = ["=== KHO TRI THỨC VÀ CĂN CỨ VĂN BẢN ĐÃ ĐỐI SOÁT (HYBRID RAG) ==="]
    citations = []

    for idx, slot in enumerate(final_slots, 1):
        tier_label = "NỀN TẢNG" if slot in slot_core else ("CHUYÊN ĐỀ" if slot in slot_thematic else "VĂN BẢN GỐC LIÊN QUAN")
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
            "core_directive": len(slot_core[:2]),
            "thematic_case": len(slot_thematic[:4]),
            "citation_linked": len(slot_citations[:2])
        }
    }
