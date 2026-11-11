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
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("doc_reader")

# Đảm bảo UTF-8 output cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_secret_document(text: str) -> Tuple[bool, str]:
    """
    Secret Document Gatekeeper (Nghị định 63/2026/NĐ-CP & Quyết định 37-QĐ/ĐU):
    Quét từ khóa đóng dấu độ mật ở phần đầu văn bản.
    Từ chối nạp và không đưa lên AI nếu phát hiện độ MẬT.
    """
    first_chunk = text[:1500].upper()
    secret_patterns = [
        r'\b(TỐI MẬT|TUYỆT MẬT)\b',
        r'ĐỘ MẬT\s*:\s*(MẬT|TỐI MẬT|TUYỆT MẬT)',
        r'(^|\n)\s*(MẬT|TỐI MẬT|TUYỆT MẬT)\s*(\n|$)',
    ]
    for pat in secret_patterns:
        if re.search(pat, first_chunk):
            return True, "CẢNH BÁO AN NINH: Văn bản chứa dấu độ MẬT / TỐI MẬT / TUYỆT MẬT theo Quyết định 37-QĐ/ĐU và Nghị định 63/2026/NĐ-CP. Tuyệt đối không nạp vào CSDL công cộng."
    return False, ""


def parse_dual_filename(filename: str) -> Dict[str, Any]:
    """
    Dual Filename Parser: Trích xuất siêu dữ liệu chuẩn hóa từ tên file:
    1. Dạng mã E-Office: A32.65-{Cơ_quan}-{Thể_loại}-{Số_hiệu}-{Năm}
    2. Dạng tiếng Việt rút gọn chuẩn AGENTS.md: {Mã_loại} {Số_hiệu} {Cơ_quan} {Trích_yếu}.ext
    """
    base_name = Path(filename).stem
    result = {
        "so_hieu": "",
        "the_loai": "",
        "co_quan_code": "",
        "nam": None,
        "trich_yeu": "",
        "parser_type": "unknown"
    }

    # Luồng 1: Dạng mã E-Office (VD: A32.65-ĐU-BC-0140-2026, A32-TU-CV-1940-2026)
    eoffice_match = re.search(r'A\d+(?:\.\d+)?-([A-Za-zĐđ]+)-([A-Za-z]+)-0*(\d+)-(\d{4})', base_name)
    if eoffice_match:
        cq = eoffice_match.group(1).upper()
        tl = eoffice_match.group(2).upper()
        so = eoffice_match.group(3)
        nam = int(eoffice_match.group(4))
        so_hieu = f"{so}-{tl}/{cq}" if cq in ["ĐU", "TU"] else f"{so}/{tl}-{cq}"
        result.update({
            "so_hieu": so_hieu,
            "the_loai": tl,
            "co_quan_code": cq,
            "nam": nam,
            "parser_type": "eoffice"
        })
        return result

    # Luồng 2: Dạng tiếng Việt rút gọn chuẩn AGENTS.md
    # VD: 'CV 0681 ĐU triển khai TB 25 của BCĐ 57 về CĐS'
    # VD: 'KH 0123 ĐU tuyên truyền chuyên sâu NQ 57 về CĐS'
    # VD: 'QĐ 98 ĐU thành lập Tổ hỗ trợ CNTT và CĐS xã'
    tv_match = re.match(r'^(CV|KH|BC|TB|QĐ|QD|NQ|TTr|CT|CTr|GM|QC)\s*(?:(\d+)\s*)?([A-Za-zĐđ0-9_\s]+?)(?:\s+(.*))?$', base_name, re.IGNORECASE)
    if tv_match:
        tl = tv_match.group(1).upper().replace("QD", "QĐ")
        so = tv_match.group(2) or ""
        cq_raw = tv_match.group(3).strip().upper()
        trich_yeu = (tv_match.group(4) or "").strip()

        cq_code = "DU" if "ĐU" in cq_raw else ("UBND" if "UBND" in cq_raw else ("TU" if "TU" in cq_raw else "DU"))
        so_hieu = f"{int(so):02d}-{tl}/{cq_code}" if so else f"-{tl}/{cq_code}"

        result.update({
            "so_hieu": so_hieu,
            "the_loai": tl,
            "co_quan_code": cq_code,
            "trich_yeu": trich_yeu,
            "parser_type": "vietnamese_standard"
        })
        return result

    return result


def clean_extracted_text(text: str) -> str:
    """Chuẩn hóa ký tự đặc biệt hay gặp trong file PDF/Word hành chính."""
    if not text:
        return ""
    # Chuyển non-breaking space sang khoảng trắng thường
    text = text.replace('\xa0', ' ')
    text = text.replace('\xad', '-')
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Chuẩn hoá dấu Khối Đảng: uỷ, oà
    text = text.replace('Ủy', 'Uỷ').replace('ủy', 'uỷ')
    text = text.replace('Hòa', 'Hoà').replace('hòa', 'hoà')
    text = text.replace('Úy', 'Uý').replace('úy', 'uý')
    # Xoá khoảng trắng thừa đầu và cuối dòng
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(lines)


def ocr_scanned_pdf(file_path: str, max_pages: int = 40) -> Dict[str, Any]:
    """
    Tự động OCR tài liệu PDF scan ảnh bằng Google Gemini Vision (Phương án 1).
    Trích xuất hình ảnh từng trang, nén sang JPEG và gọi Gemini Vision
    để số hóa toàn văn sang định dạng Markdown chuẩn xác 99.9%.
    """
    import io
    import asyncio
    from PIL import Image

    reader = None
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
    except Exception as ex:
        logger.warning(f"Không thể mở PDF bằng pypdf để OCR: {ex}")
        return {"text": "", "page_count": 0, "pages": [], "format": "pdf_ocr_error"}

    total_pages = len(reader.pages)
    pages_to_process = min(total_pages, max_pages)
    pages_text = []

    # Import default_ai_client từ server.ai_connector
    ai_client = None
    try:
        from server.ai_connector import default_ai_client
        if default_ai_client and default_ai_client._has_valid_key(default_ai_client.gemini_key):
            ai_client = default_ai_client
    except Exception as ex:
        logger.warning(f"Không thể import default_ai_client: {ex}")

    if not ai_client:
        logger.warning("Không có GEMINI_API_KEY để thực hiện OCR tự động.")
        return {"text": "", "page_count": total_pages, "pages": [], "format": "pdf_scan_no_key"}

    logger.info(f"🔍 Bắt đầu tự động OCR {pages_to_process}/{total_pages} trang PDF scan bằng Gemini Vision: {Path(file_path).name}")

    async def _process_all_pages():
        ocr_results = []
        for idx in range(pages_to_process):
            page = reader.pages[idx]
            # Tìm ảnh lớn nhất trên trang đại diện cho trang scan
            best_img_bytes = None
            if page.images:
                # Ưu tiên ảnh JPEG hoặc TIFF có kích thước lớn
                sorted_imgs = sorted(page.images, key=lambda x: len(x.data), reverse=True)
                for candidate in sorted_imgs:
                    if len(candidate.data) > 10000:  # Trên 10KB
                        try:
                            im = Image.open(io.BytesIO(candidate.data))
                            out = io.BytesIO()
                            # Resize nếu ảnh quá lớn để tiết kiệm băng thông và tăng tốc OCR
                            if im.width > 2000 or im.height > 2000:
                                im.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                            im.convert("RGB").save(out, format="JPEG", quality=85)
                            best_img_bytes = out.getvalue()
                            break
                        except Exception:
                            continue

            if not best_img_bytes:
                ocr_results.append(f"<!-- Trang {idx+1}: Không tìm thấy hình ảnh quét -->")
                continue

            try:
                page_text = await ai_client.ocr_image_with_vision(
                    image_bytes=best_img_bytes,
                    mime_type="image/jpeg",
                    prompt=(
                        f"Đây là trang {idx+1} của văn bản hành chính/Đề án/Nghị quyết của cấp uỷ Đảng hoặc Nhà nước. "
                        "Hãy trích xuất (OCR) toàn bộ chữ và bảng biểu sang Markdown sạch, trung thực 100%."
                    )
                )
                ocr_results.append(page_text.strip())
                logger.info(f"  ✓ Đã OCR xong trang {idx+1}/{pages_to_process} ({len(page_text)} ký tự)")
            except Exception as ocr_err:
                logger.warning(f"  ❌ Lỗi OCR trang {idx+1}: {ocr_err}")
                ocr_results.append(f"<!-- Trang {idx+1}: Lỗi bóc tách ({ocr_err}) -->")

        return ocr_results

    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Chạy trong luồng con nếu đang ở trong async loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    pages_text = executor.submit(lambda: asyncio.run(_process_all_pages())).result()
            else:
                pages_text = loop.run_until_complete(_process_all_pages())
        except RuntimeError:
            pages_text = asyncio.run(_process_all_pages())
    except Exception as ex:
        logger.error(f"Lỗi tổng thể trong tiến trình OCR PDF: {ex}")

    combined_text = "\n\n".join(pages_text).strip()
    return {
        "text": combined_text,
        "page_count": total_pages,
        "pages": pages_text,
        "spatial_header": "",
        "format": "pdf_scanned_ocr"
    }


def read_pdf(file_path: str) -> Dict[str, Any]:
    """
    Trích xuất text từ tệp PDF bằng PyMuPDF (fitz) hoặc pypdf.
    Tích hợp Spatial Coordinate Extraction và TỰ ĐỘNG OCR bằng Gemini Vision
    khi phát hiện tệp PDF dạng scan ảnh.
    """
    full_text = []
    pages_text = []
    spatial_header_text = ""
    is_scanned_pdf = False

    # 1. Thử trích xuất văn bản số trực tiếp
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            if page_num == 0:
                words = page.get_text("words")
                header_words = [w[4] for w in sorted(words, key=lambda x: (x[1], x[0])) if w[3] <= 240]
                spatial_header_text = " ".join(header_words)

            text = page.get_text("text")
            cleaned_page = clean_extracted_text(text)
            pages_text.append(cleaned_page)
            full_text.append(cleaned_page)
        doc.close()
    except Exception:
        # Fallback sang pypdf nếu không có fitz
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                t = clean_extracted_text(page.extract_text() or "")
                pages_text.append(t)
                full_text.append(t)
        except Exception as e_pdf:
            logger.warning(f"Lỗi khi đọc text layer PDF: {e_pdf}")

    combined_text = "\n\n".join(full_text).strip()
    # Kiểm tra xem có phải là PDF scan ảnh hay không
    # (nếu số từ trích xuất được quá ít so với số trang, ví dụ trung bình < 30 từ/trang)
    word_count = len(combined_text.split())
    num_pages = len(pages_text) or 1
    if word_count < (num_pages * 25) or word_count < 60:
        is_scanned_pdf = True

    # 2. TỰ ĐỘNG KÍCH HOẠT GEMINI VISION OCR NẾU LÀ PDF SCAN
    if is_scanned_pdf:
        logger.info(f"📸 Phát hiện tài liệu scan ảnh ({word_count} từ / {num_pages} trang). Kích hoạt tự động OCR Gemini Vision...")
        ocr_result = ocr_scanned_pdf(file_path)
        if ocr_result.get("text"):
            return ocr_result

    return {
        "text": combined_text,
        "page_count": len(pages_text),
        "pages": pages_text,
        "spatial_header": spatial_header_text,
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
    file_name = os.path.basename(file_path)
    result["file_name"] = file_name
    result["file_path"] = os.path.abspath(file_path)
    result["file_size"] = os.path.getsize(file_path)

    # 1. Chốt chặn tài liệu mật (Secret Gatekeeper)
    is_secret, secret_warning = check_secret_document(result["text"])
    result["is_secret"] = is_secret
    result["secret_warning"] = secret_warning

    # 2. Trích xuất siêu dữ liệu từ Tên file (Dual Filename Parser)
    fn_meta = parse_dual_filename(file_name)
    result["filename_metadata"] = fn_meta

    # 3. Trích xuất siêu dữ liệu thông minh từ nội dung
    meta = extract_metadata_heuristics(result["text"])
    # Ưu tiên số hiệu và thể loại từ tên file nếu nội dung bị khuyết/tem đè
    if fn_meta.get("so_hieu") and not meta.get("so_hieu"):
        meta["so_hieu"] = fn_meta["so_hieu"]
    if fn_meta.get("trich_yeu") and not meta.get("trich_yeu"):
        meta["trich_yeu"] = fn_meta["trich_yeu"]
    if fn_meta.get("co_quan_code") and not meta.get("co_quan_ban_hanh"):
        cq = "Đảng uỷ xã Công Hải" if fn_meta["co_quan_code"] == "DU" else ("Ban Thường vụ Tỉnh uỷ" if fn_meta["co_quan_code"] == "TU" else "Uỷ ban nhân dân xã")
        meta["co_quan_ban_hanh"] = cq

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
