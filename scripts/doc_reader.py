#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/doc_reader.py
=====================
Bộ trích xuất và phân tích văn bản đa định dạng (PDF, DOCX, DOC, TXT).
Hỗ trợ bóc tách nội dung, trích lọc siêu dữ liệu (Số hiệu, Trích yếu, 
Cơ quan ban hành, Ngày tháng) và gợi ý phân luồng workflow.
"""

import os
import re
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Đảm bảo UTF-8 output cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def clean_extracted_text(text: str) -> str:
    """Chuẩn hóa ký tự đặc biệt hay gặp trong file PDF/Word hành chính."""
    if not text:
        return ""
    # Chuyển non-breaking space sang khoảng trắng thường
    text = text.replace('\xa0', ' ')
    text = text.replace('\xad', '-')
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Xoá khoảng trắng thừa đầu và cuối dòng
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(lines)


def read_pdf(file_path: str) -> Dict[str, Any]:
    """Trích xuất text từ tệp PDF bằng PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("Thiếu thư viện PyMuPDF. Hãy cài đặt: pip install pymupdf")

    doc = fitz.open(file_path)
    full_text = []
    pages_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        cleaned_page = clean_extracted_text(text)
        pages_text.append(cleaned_page)
        full_text.append(cleaned_page)

    doc.close()
    combined_text = "\n\n".join(full_text).strip()
    return {
        "text": combined_text,
        "page_count": len(pages_text),
        "pages": pages_text,
        "format": "pdf"
    }


def read_docx(file_path: str) -> Dict[str, Any]:
    """Trích xuất text từ tệp DOCX bằng python-docx (paragraphs + tables)."""
    try:
        import docx
    except ImportError:
        raise ImportError("Thiếu thư viện python-docx. Hãy cài đặt: pip install python-docx")

    doc = docx.Document(file_path)
    text_parts: List[str] = []

    # 1. Đọc paragraphs
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            text_parts.append(t)

    # 2. Đọc tables (chuyển sang dạng text có cấu trúc)
    table_texts: List[str] = []
    for table in doc.tables:
        rows_data = []
        for row in table.rows:
            row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            # Loại bỏ các cột trùng lặp do merge
            dedup_cells = []
            for c in row_cells:
                if not dedup_cells or c != dedup_cells[-1]:
                    dedup_cells.append(c)
            if any(dedup_cells):
                rows_data.append(" | ".join(dedup_cells))
        if rows_data:
            table_str = "\n[BẢNG BIỂU]:\n" + "\n".join(rows_data)
            table_texts.append(table_str)

    combined_text = "\n\n".join(text_parts)
    if table_texts:
        combined_text += "\n\n" + "\n\n".join(table_texts)

    return {
        "text": combined_text.strip(),
        "page_count": 1,  # DOCX flow-based, page count is approximated
        "format": "docx"
    }


def read_doc_legacy(file_path: str) -> Dict[str, Any]:
    """
    Trích xuất text từ tệp .doc nhị phân cổ điển (Word 97-2003).
    Sử dụng Word COM trên Windows nếu có, hoặc bóc tách stream Ole/ASCII an toàn.
    """
    # Thử qua pywin32 COM trước nếu trên Windows
    if sys.platform == "win32":
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            abs_path = os.path.abspath(file_path)
            doc = word.Documents.Open(abs_path, ReadOnly=True)
            text = doc.Content.Text
            doc.Close(False)
            word.Quit()
            return {
                "text": text.strip(),
                "page_count": 1,
                "format": "doc"
            }
        except Exception:
            pass  # Fallback phương án dự phòng

    # Dự phòng: đọc stream nhị phân hoặc OLE text
    try:
        import olefile
        if olefile.isOleFile(file_path):
            ole = olefile.OleFileIO(file_path)
            if ole.exists('WordDocument'):
                stream = ole.openstream('WordDocument').read()
                # Trích xuất chuỗi Unicode UTF-16LE hoặc ASCII có thể đọc được
                raw_text = stream.decode('latin-1', errors='ignore')
                # Lọc các đoạn text tiếng Việt / ASCII
                clean_lines = []
                for chunk in re.findall(r'[\w\s,.\-/:;()"\']{4,}', raw_text):
                    if len(chunk.strip()) > 3:
                        clean_lines.append(chunk.strip())
                return {
                    "text": "\n".join(clean_lines[:500]),
                    "page_count": 1,
                    "format": "doc"
                }
    except Exception:
        pass

    # Đọc raw text fallback
    with open(file_path, "rb") as f:
        content = f.read().decode('latin-1', errors='ignore')
        ascii_text = " ".join(re.findall(r'[A-Za-z0-9À-Ỹà-ỹ\s,.\-/:;()]{5,}', content))
        return {
            "text": ascii_text.strip(),
            "page_count": 1,
            "format": "doc"
        }


def read_text(file_path: str) -> Dict[str, Any]:
    """Trích xuất text từ tệp .txt / .md."""
    encodings = ["utf-8", "utf-8-sig", "cp1258", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return {
                    "text": f.read().strip(),
                    "page_count": 1,
                    "format": "txt"
                }
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Không thể giải mã tệp văn bản: {file_path}")


def extract_document_text(file_path: str) -> Dict[str, Any]:
    """
    Hàm tổng quát tự động nhận diện phần mở rộng và trích xuất text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy tệp: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        result = read_pdf(file_path)
    elif ext == ".docx":
        result = read_docx(file_path)
    elif ext == ".doc":
        result = read_doc_legacy(file_path)
    elif ext in [".txt", ".md", ".json"]:
        result = read_text(file_path)
    else:
        raise ValueError(f"Định dạng tệp không được hỗ trợ: {ext}. Chỉ hỗ trợ .pdf, .docx, .doc, .txt, .md")

    # Bổ sung thông tin tệp
    result["file_name"] = os.path.basename(file_path)
    result["file_path"] = os.path.abspath(file_path)
    result["file_size"] = os.path.getsize(file_path)

    # Trích xuất siêu dữ liệu thông minh
    meta = extract_metadata_heuristics(result["text"])
    result["metadata"] = meta
    return result


def extract_metadata_heuristics(text: str) -> Dict[str, Any]:
    """
    Sử dụng Regex & Heuristics bóc tách nhanh các thành phần chuẩn của văn bản hành chính Đảng/Nhà nước.
    """
    first_chunk = text[:3000]  # Thường nằm ở 3000 ký tự đầu

    # 1. Số hiệu (ví dụ: Số 83-KH/TU, Số 12-BC/UBND, Số 05/TB-UBND)
    so_hieu_match = re.search(
        r'Số\s*[:\s]*([0-9]+[A-Za-z0-9\-\/]*(?:KH|NQ|QD|QĐ|TB|KL|BC|TTr|CT|CV|HD|HĐ|QC)[A-Za-z0-9\-\/]*)',
        first_chunk, re.IGNORECASE
    )
    so_hieu = so_hieu_match.group(1).strip() if so_hieu_match else ""

    # 2. Ngày tháng năm
    ngay_thang_match = re.search(
        r'(?:ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})|(\d{1,2}\/\d{1,2}\/\d{4}))',
        first_chunk, re.IGNORECASE
    )
    ngay_thang = ""
    if ngay_thang_match:
        if ngay_thang_match.group(1):
            d, m, y = ngay_thang_match.group(1), ngay_thang_match.group(2), ngay_thang_match.group(3)
            ngay_thang = f"{int(d):02d}/{int(m):02d}/{y}"
        elif ngay_thang_match.group(4):
            ngay_thang = ngay_thang_match.group(4)

    # 3. Cơ quan ban hành
    co_quan = ""
    if re.search(r'TỈNH UỶ KHÁNH HOÀ|BAN THƯỜNG VỤ TỈNH UỶ|THƯỜNG TRỰC TỈNH UỶ', first_chunk, re.IGNORECASE):
        co_quan = "Ban Thường vụ Tỉnh uỷ Khánh Hoà"
    elif re.search(r'UỶ BAN NHÂN DÂN TỈNH|UBND TỈNH', first_chunk, re.IGNORECASE):
        co_quan = "Uỷ ban nhân dân tỉnh Khánh Hoà"
    elif re.search(r'UỶ BAN NHÂN DÂN XÃ CÔNG HẢI|UBND XÃ CÔNG HẢI', first_chunk, re.IGNORECASE):
        co_quan = "Uỷ ban nhân dân xã Công Hải"
    elif re.search(r'BAN XÂY DỰNG ĐẢNG', first_chunk, re.IGNORECASE):
        co_quan = "Ban Xây dựng Đảng"
    elif re.search(r'UỶ BAN KIỂM TRA', first_chunk, re.IGNORECASE):
        co_quan = "Uỷ ban Kiểm tra Đảng uỷ"
    elif re.search(r'MẶT TRẬN TỔ QUỐC|UBMTTQ', first_chunk, re.IGNORECASE):
        co_quan = "Cơ quan Uỷ ban MTTQVN xã"
    elif re.search(r'VĂN PHÒNG ĐẢNG UỶ', first_chunk, re.IGNORECASE):
        co_quan = "Văn phòng Đảng uỷ"

    # 4. Trích yếu / Tên loại
    trich_yeu = ""
    # Nếu có V/v
    vv_match = re.search(r'V\/v\s+([^\n\r]+)', first_chunk, re.IGNORECASE)
    if vv_match:
        trich_yeu = vv_match.group(1).strip()
    else:
        # Nếu có Tiêu đề dạng KẾ HOẠCH, BÁO CÁO, THÔNG BÁO...
        heading_match = re.search(
            r'(KẾ HOẠCH|NGHỊ QUYẾT|QUYẾT ĐỊNH|BÁO CÁO|THÔNG BÁO|KẾT LUẬN|TỜ TRÌNH|CHỈ THỊ)\s*[\r\n]+([^\n\r]+)',
            first_chunk
        )
        if heading_match:
            trich_yeu = f"{heading_match.group(1)} {heading_match.group(2).strip()}"

    # 5. Phân loại luồng văn bản (Router Suggestion)
    suggested_type = "chua_xac_dinh"
    suggested_wf = "wf3_giao_viec"

    # Nhận diện cấp trên (Tỉnh uỷ / UBND tỉnh)
    if "Tỉnh uỷ" in co_quan or "tỉnh" in co_quan.lower() or "TU" in so_hieu or "UBND-TH" in so_hieu:
        suggested_type = "cap_tren"
        suggested_wf = "wf3_giao_viec"
    # Nhận diện Báo cáo tuần / tháng
    elif re.search(r'báo cáo\s+(tuần|tình hình tuần|tháng|công tác tháng)', first_chunk, re.IGNORECASE):
        suggested_type = "bao_cao_co_so"
        suggested_wf = "wf1_tong_hop_bao_cao"
    # Nhận diện Biên bản cuộc họp
    elif re.search(r'biên bản|kết luận cuộc họp|ghi chép cuộc họp', first_chunk, re.IGNORECASE):
        suggested_type = "bien_ban_hop"
        suggested_wf = "wf2_thong_bao_ket_luan"
    # Nhận diện Dự thảo của các cơ quan xã trình Đảng uỷ
    elif "dự thảo" in first_chunk.lower() or "trình ban thường vụ" in first_chunk.lower() or any(k in co_quan for k in ["UBND xã", "Ban Xây dựng Đảng", "Uỷ ban Kiểm tra", "MTTQ"]):
        suggested_type = "du_thao_co_quan"
        suggested_wf = "wf4_tham_dinh"

    return {
        "so_hieu": so_hieu,
        "ngay_thang": ngay_thang,
        "co_quan_ban_hanh": co_quan,
        "trich_yeu": trich_yeu,
        "suggested_type": suggested_type,
        "suggested_wf": suggested_wf
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Đọc và phân tích văn bản PDF, DOCX, TXT.")
    parser.add_argument("file_path", help="Đường dẫn tới tệp cần đọc")
    args = parser.parse_args()

    doc_data = extract_document_text(args.file_path)
    print("=== KẾT QUẢ ĐỌC VĂN BẢN ===")
    print(f"Tệp: {doc_data['file_name']} ({doc_data['format']})")
    print(f"Độ dài: {len(doc_data['text'])} ký tự, Số trang: {doc_data['page_count']}")
    print("=== SIÊU DỮ LIỆU NHẬN DIỆN ===")
    for k, v in doc_data["metadata"].items():
        print(f" - {k}: {v}")
    print("\n=== ĐOẠN ĐẦU VĂN BẢN ===")
    print(doc_data["text"][:500] + "...")
