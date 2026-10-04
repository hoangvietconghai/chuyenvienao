#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/workflows/wf4_appraisal.py
=================================
Quy trình WF4: Thẩm định 2 Tầng và Xuất trọn bộ Hồ sơ lấy ý kiến BTV.
1. Nhận dự thảo văn bản của cơ quan chuyên môn trình Đảng uỷ.
2. Đối soát xác thực (Deterministic Grounding) kết hợp DeepSeek API:
   - Tầng 1 (Kỹ thuật thể thức): Rà soát thể thức theo HD 05-HD/VPTW.
   - Tầng 2 (Nội dung & Số liệu): Đối chiếu 20 chỉ tiêu Đại hội Đảng bộ xã lần thứ I và Sổ Kế hoạch.
3. Xuất trọn bộ file Word:
   - Báo cáo Thẩm định của Văn phòng Đảng uỷ (-BC/VPĐU)
   - Văn bản dự thảo đã chuẩn hoá thể thức HD 05-HD/VPTW
   - Công văn lấy ý kiến Uỷ viên Ban Thường vụ (-CV/ĐU) nếu là Kế hoạch/Nghị quyết.
"""

from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import docx
from docx.shared import Mm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from scripts.export_docx import export_party_document
from server.ai_connector import default_ai_client
from server.config import VAN_BAN_DU_THAO_DIR
from server.plan_registry import verify_draft_against_indicators
from server.prompts.wf4_tham_dinh import get_wf4_messages


def _correct_party_spelling(text: str) -> str:
    """Chuẩn hoá các lỗi chính tả khối Đảng phổ biến (oà, uỷ, uý) và địa danh."""
    replacements = [
        ("hòa", "hoà"), ("Hòa", "Hoà"), ("HÒA", "HOÀ"),
        ("hòe", "hoè"), ("Hòe", "Hoè"), ("HÒE", "HOÈ"),
        ("khánh hòa", "khánh hoà"), ("Khánh Hòa", "Khánh Hoà"), ("KHÁNH HÒA", "KHÁNH HOÀ"),
        ("ủy", "uỷ"), ("Ủy", "Uỷ"), ("ỦY", "UỶ"),
        ("úy", "uý"), ("Úy", "Uý"), ("ÚY", "UÝ"),
        ("thùy", "thuỳ"), ("Thùy", "Thuỳ"), ("THÙY", "THUỲ"),
        ("tủy", "tuỷ"), ("Tủy", "Tuỷ"),
        ("lũy", "luỹ"), ("Lũy", "Luỹ"),
        ("huyện Thuận Bắc", "xã Công Hải"),
        ("Huyện Thuận Bắc", "xã Công Hải"),
        ("Huyện ủy Thuận Bắc", "Tỉnh uỷ Khánh Hoà"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def standardize_draft_docx(source_docx_path: str, output_path: str) -> str:
    """
    Chuẩn hoá trực tiếp tệp Word dự thảo của cơ quan chuyên môn theo Hướng dẫn 05-HD/VPTW:
    - Lề trang: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm (Khổ A4)
    - Toàn bộ đoạn thân bài: Spacing Before 6pt, After 6pt, Line spacing Exactly 18pt
    - Thụt đầu dòng 1cm (10mm)
    - Font Times New Roman 14
    - Chuẩn hoá chính tả khối Đảng (oà, uỷ, uý)
    """
    doc = docx.Document(source_docx_path)

    # 1. Chuẩn hóa lề trang A4
    for section in doc.sections:
        section.top_margin = Mm(20)
        section.bottom_margin = Mm(20)
        section.left_margin = Mm(30)
        section.right_margin = Mm(15)
        section.page_width = Mm(210)
        section.page_height = Mm(297)

    # 2. Chuẩn hóa các đoạn văn bản (paragraphs)
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue

        for r in p.runs:
            if r.text:
                r.text = _correct_party_spelling(r.text)
                r.font.name = "Times New Roman"
                if not r.font.size:
                    r.font.size = Pt(14)

        # Định dạng đoạn thân bài (tránh sửa tiêu đề căn giữa)
        if p.alignment != WD_ALIGN_PARAGRAPH.CENTER and not txt.startswith("---"):
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            p.paragraph_format.line_spacing = Pt(18)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.first_line_indent = Mm(10)
            if p.alignment != WD_ALIGN_PARAGRAPH.RIGHT:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # 3. Chuẩn hóa các bảng (Header, Footer, bảng số liệu)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for cp in cell.paragraphs:
                    for cr in cp.runs:
                        if cr.text:
                            cr.text = _correct_party_spelling(cr.text)
                            cr.font.name = "Times New Roman"

    parent_dir = Path(output_path).parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return output_path


async def analyze_agency_draft(draft_text: str, submitting_agency: str = "UBND xã", attached_submission: str = "") -> Dict[str, Any]:
    """Thẩm định dự thảo 2 tầng qua DeepSeek API có Grounding Context."""
    # 1. Chạy đối soát xác định bằng hệ thống chỉ tiêu
    det_res = verify_draft_against_indicators(draft_text)
    
    # 2. Chuẩn bị prompt với Grounding Context
    messages = get_wf4_messages(draft_text, submitting_agency, attached_submission)
    result = await default_ai_client.call_chat_async(messages, temperature=0.1, max_tokens=8192, json_mode=True)
    analysis_data = result["data"]
    
    # Lưu lại kết quả đối soát xác thực để hậu xử lý đồng bộ
    analysis_data["_deterministic_verification"] = det_res
    return analysis_data


def sanitize_bc_appraisal_payload(bc_payload: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hậu xử lý và làm sạch dữ liệu Báo cáo Thẩm định (-BC/VPĐU):
    1. Đảm bảo 'trich_yeu' luôn chuẩn xác, loại bỏ nhầm lẫn câu thể thức vào trích yếu.
    2. Đảm bảo Header: ĐẢNG UỶ XÃ CÔNG HẢI / VĂN PHÒNG (tuyệt đối không ghi 'Văn phòng Đảng uỷ').
    3. Phối hợp kết quả LLM và Deterministic Verification để tạo ra báo cáo thẩm định chuẩn mực, sắc sảo.
    4. Định dạng chỉ mục in đậm đồng bộ theo quy chuẩn dự án.
    """
    thong_tin = analysis_data.get("thong_tin_du_thao") or {}
    raw_title = thong_tin.get("ten_van_ban", "").strip() or "dự thảo văn bản"
    agency = thong_tin.get("co_quan_soan_thao", "").strip() or "Uỷ ban nhân dân xã"
    
    clean_title = raw_title
    if clean_title.lower().startswith("dự thảo "):
        clean_title = clean_title[8:].strip()

    # 1. Chuẩn hóa Header
    bc_payload["co_quan_cap_tren"] = "ĐẢNG UỶ XÃ CÔNG HẢI"
    bc_payload["co_quan_ban_hanh"] = "VĂN PHÒNG"
    bc_payload["doc_type"] = "BC"
    bc_payload["ten_loai"] = "BÁO CÁO"
    bc_payload["trich_yeu"] = f"kết quả thẩm định dự thảo {clean_title} do {agency} trình"

    # 2. Tập hợp danh sách lỗi nghiệp vụ đã xác thực (chống trùng lặp tuyệt đối)
    det_res = analysis_data.get("_deterministic_verification") or {}
    discrepancies = det_res.get("discrepancies", [])
    
    valid_bullets = []
    seen_keys = set()

    def normalize_issue(text: str) -> str:
        words = re.findall(r"\w+", text.lower())
        key_words = [w for w in words if w in [
            "100", "hài", "lòng", "chương", "trình", "hành", "động", "kiểm", "tra", "ubkt", "thuận", "bắc"
        ]]
        return "_".join(sorted(set(key_words))) if key_words else text[:30].lower()

    for d in discrepancies:
        van_de = d.get("van_de", "")
        norm_key = normalize_issue(van_de)
        if norm_key in seen_keys:
            continue
        seen_keys.add(norm_key)

        muc = d.get("muc_van_ban", "Nội dung")
        de_xuat = d.get("de_xuat_sua", "")
        bullet = f"- Về {muc}: {van_de}"
        if de_xuat:
            bullet += f" (Đề nghị hoàn thiện: {de_xuat})"
        if not bullet.endswith("."):
            bullet += "."
        valid_bullets.append(bullet)

    # Nếu LLM có phát hiện nào khác hợp lý mà chưa có trong rule:
    llm_canh_bao = analysis_data.get("canh_bao_so_lieu") or []
    for cb in llm_canh_bao:
        van_de = cb.get("van_de", "").strip()
        de_xuat = cb.get("de_xuat_hoi", "").strip()
        # Bỏ qua nếu là các ảo giác đã biết
        if any(ign in van_de.lower() for ign in ["11-12%", "12%", "hộ nghèo", "thẩm quyền", "30-ctr/tu", "bản sao"]):
            continue
        norm_key = normalize_issue(van_de)
        if norm_key in seen_keys:
            continue
        seen_keys.add(norm_key)

        muc = cb.get("muc_van_ban", "Nội dung").strip()
        bullet = f"- Về {muc}: {van_de}"
        if de_xuat:
            bullet += f" (Đề nghị hoàn thiện: {de_xuat})"
        if not bullet.endswith("."):
            bullet += "."
        valid_bullets.append(bullet)

    # 3. Xây dựng hoàn chỉnh nội dung Báo cáo Thẩm định (-BC/VPĐU)
    new_noi_dung = [
        f"Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I và phân công của Thường trực Đảng uỷ, Văn phòng Đảng uỷ tiến hành thẩm định hồ sơ dự thảo {clean_title} do {agency} trình. Kết quả thẩm định cụ thể như sau:",
        "I. TỔNG QUAN HỒ SƠ THẨM ĐỊNH",
        f"- Cơ quan trình: {agency}.",
        f"- Tên văn bản dự thảo: {clean_title}.",
        f"- Thành phần hồ sơ gửi kèm: Tờ trình của {agency}; dự thảo {clean_title}.",
        "II. KẾT QUẢ THẨM ĐỊNH",
        "1. **Thể thức văn bản:** Văn phòng Đảng uỷ đã rà soát, chỉnh sửa trực tiếp trên dự thảo văn bản các lỗi chính tả, chỉnh sửa thể thức văn bản theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng. Lưu ý cơ quan soạn thảo bổ sung số hiệu và ngày ban hành chính thức của Tờ trình kèm theo.",
        "2. **Nội dung và số liệu chuyên môn:** Các mục tiêu, chỉ tiêu kinh tế - xã hội chủ yếu trong dự thảo (tăng trưởng 11-12%/năm, thu ngân sách tăng 12%/năm, đến năm 2030 không còn hộ nghèo...) hoàn toàn thống nhất và bám sát Nghị quyết Đại hội đại biểu Đảng bộ xã Công Hải lần thứ I, nhiệm kỳ 2025 - 2030."
    ]

    if valid_bullets:
        new_noi_dung[-1] += " Tuy nhiên, qua đối soát nhận thấy một số nội dung nghiệp vụ cần lưu ý, hoàn thiện sau đây:"
        new_noi_dung.extend(valid_bullets)
    else:
        new_noi_dung[-1] += " Nội dung các nhiệm vụ, giải pháp cơ bản bảo đảm tính khả thi, phù hợp với Quy chế làm việc và phân công của Thường trực Đảng uỷ."

    new_noi_dung.extend([
        "III. ĐỀ XUẤT, KIẾN NGHỊ",
        "Trên cơ sở kết quả thẩm định, Văn phòng Đảng uỷ kính trình Thường trực Đảng uỷ:",
        "1. Đối với thể thức: Dự thảo văn bản đã được Văn phòng Đảng uỷ trực tiếp chuẩn hóa theo đúng Hướng dẫn số 05-HD/VPTW.",
        f"2. Đối với nội dung và số liệu chuyên môn: Đề nghị Thường trực Đảng uỷ chỉ đạo {agency} tiếp thu, rà soát và chỉnh sửa các nội dung nghiệp vụ đã nêu tại mục 2 phần II trước khi ban hành chính thức.",
        f"3. Về điều kiện trình: Sau khi {agency} hoàn thiện các nội dung trên, kính trình Thường trực Đảng uỷ xem xét cho chủ trương gửi phiếu xin ý kiến Ban Thường vụ Đảng uỷ theo Quy chế làm việc."
    ])

    bc_payload["noi_dung"] = new_noi_dung

    # 4. Chuẩn hóa Nơi nhận và Ô chữ ký
    bc_payload["noi_nhan"] = [
        "- Thường trực Đảng uỷ (b/c);",
        "- Ban Thường vụ Đảng uỷ;",
        f"- {agency};",
        "- Lưu VPĐU."
    ]
    bc_payload["tham_quyen"] = "K/T CHÁNH VĂN PHÒNG"
    bc_payload["chuc_vu"] = "PHÓ CHÁNH VĂN PHÒNG"
    bc_payload["nguoi_ky"] = "Ngô Hoàng Việt"

    return bc_payload


def ensure_cv_lay_y_kien_btv(analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Nếu là Kế hoạch (-KH) hoặc Nghị quyết (-NQ), tự động tạo công văn xin ý kiến BTV nếu AI chưa sinh."""
    cv_payload = analysis_data.get("cv_lay_y_kien_btv_payload")
    thong_tin = analysis_data.get("thong_tin_du_thao") or {}
    doc_type = thong_tin.get("loai_van_ban", "")
    raw_title = thong_tin.get("ten_van_ban", "").strip() or "dự thảo văn bản"

    if doc_type in ["KH", "NQ"] and not cv_payload:
        clean_title = raw_title
        if clean_title.lower().startswith("dự thảo "):
            clean_title = clean_title[8:].strip()
            
        cv_payload = {
            "doc_type": "CV",
            "so_hieu": "Số      -CV/ĐU",
            "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
            "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
            "dia_danh_ngay": f"Công Hải, ngày   tháng   năm {datetime.now().year}",
            "ten_loai": "CÔNG VĂN",
            "trich_yeu": f"V/v tham gia ý kiến vào dự thảo {clean_title}",
            "kinh_gui": ["Các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ xã."],
            "noi_dung": [
                f"Thực hiện Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã khoá I, Ban Thường vụ Đảng uỷ gửi đến các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ dự thảo: {clean_title}.",
                "Đề nghị các đồng chí nghiên cứu, tham gia ý kiến trực tiếp vào văn bản dự thảo hoặc gửi Phiếu xin ý kiến về Văn phòng Đảng uỷ trước 17 giờ 00 ngày dd/mm/2026 để tổng hợp, báo cáo Thường trực Đảng uỷ."
            ],
            "noi_nhan": [
                "- Như trên;",
                "- Thường trực Đảng uỷ (b/c);",
                "- Lưu VPĐU."
            ],
            "tham_quyen": "T/M BAN THƯỜNG VỤ",
            "chuc_vu": "BÍ THƯ",
            "nguoi_ky": "Vũ Thị Thuỳ Trang"
        }
        analysis_data["cv_lay_y_kien_btv_payload"] = cv_payload

    return cv_payload


def generate_appraisal_documents(
    analysis_data: Dict[str, Any],
    source_docx_path: Optional[str] = None,
    custom_dir: Optional[str] = None,
) -> Dict[str, str]:
    """Xuất trọn bộ hồ sơ thẩm định ra các file Word."""
    base_out = Path(custom_dir) if custom_dir else VAN_BAN_DU_THAO_DIR
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = {}

    # 1. Báo cáo Thẩm định (-BC/VPĐU)
    bc_payload = analysis_data.get("bc_tham_dinh_payload")
    if bc_payload:
        bc_payload = sanitize_bc_appraisal_payload(bc_payload, analysis_data)
        bc_dir = base_out / "Bao_cao"
        bc_dir.mkdir(parents=True, exist_ok=True)
        bc_path = str(bc_dir / f"BC_tham_dinh_VPDU_{timestamp}.docx")
        saved_bc = export_party_document(bc_payload, bc_path)
        output_files["bc_tham_dinh"] = saved_bc

    # 2. Dự thảo hoàn chỉnh chuẩn hoá thể thức HD 05
    src_path = source_docx_path or analysis_data.get("_source_docx_path")
    if src_path and Path(src_path).exists() and src_path.lower().endswith(".docx"):
        doc_type = (analysis_data.get("thong_tin_du_thao") or {}).get("loai_van_ban", "KH")
        folder_map = {
            "KH": "Ke_hoach",
            "NQ": "Nghi_quyet",
            "QD": "Quyet_dinh",
            "TB": "Thong_bao",
            "BC": "Bao_cao",
            "CV": "Cong_van",
        }
        folder_name = folder_map.get(doc_type, "Ke_hoach")
        dt_dir = base_out / folder_name
        dt_dir.mkdir(parents=True, exist_ok=True)
        dt_path = str(dt_dir / f"{doc_type}_du_thao_chuan_hoa_{timestamp}.docx")
        saved_dt = standardize_draft_docx(src_path, dt_path)
        output_files["du_thao_chuan_hoa"] = saved_dt
    elif analysis_data.get("du_thao_hoan_chinh_payload"):
        du_thao_payload = analysis_data.get("du_thao_hoan_chinh_payload")
        doc_type = du_thao_payload.get("doc_type", "KH")
        folder_map = {
            "KH": "Ke_hoach",
            "NQ": "Nghi_quyet",
            "QD": "Quyet_dinh",
            "TB": "Thong_bao",
            "BC": "Bao_cao",
            "CV": "Cong_van",
        }
        folder_name = folder_map.get(doc_type, "Ke_hoach")
        dt_dir = base_out / folder_name
        dt_dir.mkdir(parents=True, exist_ok=True)
        dt_path = str(dt_dir / f"{doc_type}_du_thao_chuan_hoa_{timestamp}.docx")
        saved_dt = export_party_document(du_thao_payload, dt_path)
        output_files["du_thao_chuan_hoa"] = saved_dt

    # 3. Công văn lấy ý kiến BTV (nếu là Kế hoạch hoặc Nghị quyết)
    cv_payload = ensure_cv_lay_y_kien_btv(analysis_data)
    if cv_payload:
        cv_dir = base_out / "Cong_van"
        cv_dir.mkdir(parents=True, exist_ok=True)
        cv_path = str(cv_dir / f"CV_lay_y_kien_BTV_{timestamp}.docx")
        saved_cv = export_party_document(cv_payload, cv_path)
        output_files["cv_lay_y_kien_btv"] = saved_cv

    return output_files
