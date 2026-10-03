#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/export_docx.py
======================
Hệ thống tự động sinh tệp Word (.docx) chuẩn thể thức văn bản khối Đảng 
theo Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.

Áp dụng cho: Đảng uỷ xã Công Hải, tỉnh Khánh Hoà
Hỗ trợ các thể loại:
  - CV  : Công văn giao việc, chỉ đạo, đôn đốc (-CV/ĐU)
  - KH  : Kế hoạch triển khai, hành động (-KH/ĐU)
  - NQ  : Nghị quyết chuyên đề, nghị quyết năm (-NQ/ĐU)
  - QD  : Quyết định cán bộ, kết nạp đảng, thành lập ban (-QĐ/ĐU)
  - TB  : Thông báo kết luận cuộc họp Thường vụ, Thường trực (-TB/ĐU)
  - KL  : Kết luận Hội nghị Ban Chấp hành (-KL/ĐU)
  - BC  : Báo cáo công tác tháng/quý/năm, chuyên đề (-BC/ĐU)
  - TTr : Tờ trình xin chủ trương, trình cấp trên/nội bộ (-TTr/ĐU)
  - CT  : Chỉ thị công tác (-CT/ĐU)
  - CTr : Chương trình hành động (-CTr/ĐU)
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import docx
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import qn


# ==============================================================================
# 1. HELPER XML VÀ ĐỊNH DẠNG CƠ BẢN
# ==============================================================================

def set_cell_margins(cell, top=0, bottom=0, left=0, right=0):
    """Thiết lập padding lề trong của ô bảng (đơn vị: dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{margin_name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def remove_table_borders(table):
    """Xóa toàn bộ đường viền để tạo lưới bảng ẩn (Invisible Grid)."""
    tblBorders = parse_xml(r'''
        <w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>
        </w:tblBorders>
    ''')
    table._tbl.tblPr.append(tblBorders)


def add_horizontal_line(paragraph, width_pt=186, weight_pt=0.75):
    """Thêm đường kẻ liền ngang màu đen dưới tiêu ngữ Đảng (kéo dài toàn bộ dòng chữ ĐCSVN, độ dày 3/4pt)."""
    vml_xml = f'''<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:v="urn:schemas-microsoft-com:vml">
        <w:pict>
            <v:line from="0,0" to="{width_pt}pt,0" strokecolor="#000000" strokeweight="{weight_pt}pt"/>
        </w:pict>
    </w:r>'''
    paragraph._p.append(parse_xml(vml_xml))


def parse_markdown_runs(paragraph, text, base_font_size=14, base_font_name="Times New Roman", default_bold=False, default_italic=False):
    """
    Phân tích chuỗi có định dạng markdown cơ bản (**in đậm**, *in nghiêng*) 
    và thêm các run tương ứng vào paragraph.
    """
    pattern = r'(\*\*.*?\*\*|\*.*?\*)'
    tokens = re.split(pattern, text)
    
    for token in tokens:
        if not token:
            continue
        is_bold = default_bold
        is_italic = default_italic
        clean_text = token
        
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            is_bold = True
            clean_text = token[2:-2]
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            is_italic = True
            clean_text = token[1:-1]
            
        run = paragraph.add_run(clean_text)
        run.font.name = base_font_name
        run.font.size = Pt(base_font_size)
        run.font.bold = is_bold
        run.font.italic = is_italic
        run.font.color.rgb = RGBColor(0, 0, 0)


# ==============================================================================
# 2. CLASS PARTY DOCUMENT BUILDER (ENGINE TỔNG QUÁT)
# ==============================================================================

class PartyDocumentBuilder:
    """Bộ tạo lập văn bản Đảng chuẩn thể thức HD 05-HD/VPTW."""

    FOLDER_ROUTING = {
        "CV": "Cong_van",
        "KH": "Ke_hoach",
        "NQ": "Nghi_quyet",
        "QD": "Quyet_dinh",
        "TB": "Thong_bao",
        "KL": "Ket_luan",
        "BC": "Bao_cao",
        "TTr": "To_trinh",
        "CT": "Chi_thi",
        "CTR": "Chuong_trinh"
    }

    TYPE_LABELS = {
        "KH": "KẾ HOẠCH",
        "NQ": "NGHỊ QUYẾT",
        "QD": "QUYẾT ĐỊNH",
        "TB": "THÔNG BÁO",
        "KL": "KẾT LUẬN",
        "BC": "BÁO CÁO",
        "TTr": "TỜ TRÌNH",
        "CT": "CHỈ THỊ",
        "CTR": "CHƯƠNG TRÌNH"
    }

    def __init__(self, data: dict):
        self.data = data
        self.doc_type = data.get("doc_type", "CV").upper()
        self.doc = docx.Document()
        self._setup_page()

    def _setup_page(self):
        """Khổ giấy A4, Lề trang chuẩn: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm."""
        for section in self.doc.sections:
            section.page_width = Mm(210)
            section.page_height = Mm(297)
            section.left_margin = Mm(30)
            section.right_margin = Mm(15)
            section.top_margin = Mm(20)
            section.bottom_margin = Mm(20)
            section.header.is_linked_to_previous = False
            section.footer.is_linked_to_previous = False

        # Cấu hình Style mặc định
        style = self.doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(14)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        style.paragraph_format.line_spacing = Pt(18)
        style.paragraph_format.space_before = Pt(6)
        style.paragraph_format.space_after = Pt(6)

    def build_header(self):
        """Dựng Bảng 1 hàng 2 cột ẩn viền phần Quốc hiệu / Tiêu đề và Số hiệu."""
        table = self.doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        remove_table_borders(table)

        col1 = table.columns[0]
        col2 = table.columns[1]
        col1.width = Mm(75)
        col2.width = Mm(90)

        cell_left = table.cell(0, 0)
        cell_right = table.cell(0, 1)
        cell_left.width = Mm(75)
        cell_right.width = Mm(90)
        set_cell_margins(cell_left, top=0, bottom=0, left=0, right=70)
        set_cell_margins(cell_right, top=0, bottom=0, left=70, right=0)

        # --- CỘT 1 (TRÁI): Cơ quan ban hành & Số hiệu ---
        so_hieu = self.data.get("so_hieu", f"Số      -{self.doc_type}/ĐU")
        
        # Mặc định cho văn bản Cấp uỷ
        default_tren = "ĐẢNG BỘ TỈNH KHÁNH HOÀ"
        default_bh = "ĐẢNG UỶ XÃ CÔNG HẢI"
        
        # Nhận diện tự động nếu là văn bản của Văn phòng Đảng uỷ (/VPĐU, /VP)
        raw_cq_bh = str(self.data.get("co_quan_ban_hanh", "")).upper()
        if "/VPĐU" in so_hieu.upper() or "/VP" in so_hieu.upper() or "VĂN PHÒNG" in raw_cq_bh:
            default_tren = "ĐẢNG UỶ XÃ CÔNG HẢI"
            default_bh = "VĂN PHÒNG"
        elif "/UBKT" in so_hieu.upper() or "KIỂM TRA" in raw_cq_bh:
            default_tren = "ĐẢNG UỶ XÃ CÔNG HẢI"
            default_bh = "UỶ BAN KIỂM TRA"
        elif "/BXĐĐ" in so_hieu.upper() or "XÂY DỰNG ĐẢNG" in raw_cq_bh:
            default_tren = "ĐẢNG UỶ XÃ CÔNG HẢI"
            default_bh = "BAN XÂY DỰNG ĐẢNG"

        co_quan_tren = self.data.get("co_quan_cap_tren", default_tren)
        co_quan_bh = self.data.get("co_quan_ban_hanh", default_bh)

        # 1. Cơ quan cấp trên
        p_cq_tren = cell_left.paragraphs[0]
        p_cq_tren.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cq_tren.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_cq_tren.paragraph_format.line_spacing = 1.05
        p_cq_tren.paragraph_format.space_before = Pt(0)
        p_cq_tren.paragraph_format.space_after = Pt(1)
        r = p_cq_tren.add_run(co_quan_tren)
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)

        # 2. Cơ quan ban hành
        p_cq_bh = cell_left.add_paragraph()
        p_cq_bh.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cq_bh.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_cq_bh.paragraph_format.line_spacing = 1.05
        p_cq_bh.paragraph_format.space_before = Pt(0)
        p_cq_bh.paragraph_format.space_after = Pt(1)
        r = p_cq_bh.add_run(co_quan_bh)
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.bold = True

        # 3. Dấu sao (*)
        p_sao = cell_left.add_paragraph()
        p_sao.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sao.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_sao.paragraph_format.line_spacing = 1.0
        p_sao.paragraph_format.space_before = Pt(0)
        p_sao.paragraph_format.space_after = Pt(2)
        r = p_sao.add_run("*")
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.bold = True

        # 4. Số hiệu
        p_so = cell_left.add_paragraph()
        p_so.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_so.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_so.paragraph_format.line_spacing = 1.05
        p_so.paragraph_format.space_before = Pt(0)
        p_so.paragraph_format.space_after = Pt(3)
        r = p_so.add_run(so_hieu)
        r.font.name = "Times New Roman"
        r.font.size = Pt(13.5)

        # 5. Nếu là CÔNG VĂN: Trích yếu nằm dưới số hiệu tại cột 1
        if self.doc_type == "CV":
            trich_yeu = self.data.get("trich_yeu", "")
            if trich_yeu:
                p_trichyeu = cell_left.add_paragraph()
                p_trichyeu.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_trichyeu.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                p_trichyeu.paragraph_format.line_spacing = 1.05
                p_trichyeu.paragraph_format.space_before = Pt(0)
                p_trichyeu.paragraph_format.space_after = Pt(0)
                r = p_trichyeu.add_run(trich_yeu)
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.font.italic = True

        # --- CỘT 2 (PHẢI): Tiêu ngữ Đảng & Ngày tháng ---
        p_tieungu = cell_right.paragraphs[0]
        p_tieungu.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_tieungu.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_tieungu.paragraph_format.line_spacing = 1.05
        p_tieungu.paragraph_format.space_before = Pt(0)
        p_tieungu.paragraph_format.space_after = Pt(1)
        r = p_tieungu.add_run("ĐẢNG CỘNG SẢN VIỆT NAM")
        r.font.name = "Times New Roman"
        r.font.size = Pt(14)
        r.font.bold = True

        # Đường kẻ ngang
        p_line = cell_right.add_paragraph()
        p_line.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_line.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_line.paragraph_format.line_spacing = 1.0
        p_line.paragraph_format.space_before = Pt(0)
        p_line.paragraph_format.space_after = Pt(4)
        add_horizontal_line(p_line, width_pt=186, weight_pt=0.75)

        # Ngày tháng năm
        dia_danh_ngay = self.data.get("dia_danh_ngay", "Công Hải, ngày   tháng   năm 2026")
        p_ngay = cell_right.add_paragraph()
        p_ngay.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_ngay.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_ngay.paragraph_format.line_spacing = 1.05
        p_ngay.paragraph_format.space_before = Pt(0)
        p_ngay.paragraph_format.space_after = Pt(0)
        r = p_ngay.add_run(dia_danh_ngay)
        r.font.name = "Times New Roman"
        r.font.size = Pt(13.5)
        r.font.italic = True

    def build_title_section(self):
        """Dựng phần Tiêu đề và Trích yếu văn bản (cho các văn bản có tên loại)."""
        # Khoảng đệm sau Header
        p_space = self.doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(0)
        p_space.paragraph_format.space_after = Pt(6)
        p_space.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_space.paragraph_format.line_spacing = 1.0

        if self.doc_type != "CV":
            ten_loai = self.data.get("ten_loai", self.TYPE_LABELS.get(self.doc_type, self.doc_type))
            trich_yeu = self.data.get("trich_yeu", "")
            
            p_ten = self.doc.add_paragraph()
            p_ten.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_ten.paragraph_format.space_before = Pt(6)
            p_ten.paragraph_format.space_after = Pt(4)
            p_ten.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            p_ten.paragraph_format.line_spacing = 1.15
            r = p_ten.add_run(ten_loai.upper())
            r.font.name = "Times New Roman"
            r.font.size = Pt(15)
            r.font.bold = True

            if trich_yeu:
                p_ty = self.doc.add_paragraph()
                p_ty.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_ty.paragraph_format.space_before = Pt(0)
                p_ty.paragraph_format.space_after = Pt(10)
                p_ty.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                p_ty.paragraph_format.line_spacing = 1.15
                r = p_ty.add_run(trich_yeu)
                r.font.name = "Times New Roman"
                r.font.size = Pt(14)
                r.font.bold = True

        # Khối Kính gửi: BẢNG 1 HÀNG 2 CỘT ẨN VIỀN
        kinh_gui = self.data.get("kinh_gui", [])
        if kinh_gui:
            if isinstance(kinh_gui, str):
                if "\n" in kinh_gui:
                    kinh_gui = [x.strip() for x in kinh_gui.split("\n") if x.strip()]
                else:
                    kinh_gui = [kinh_gui.strip()]

            kg_table = self.doc.add_table(rows=1, cols=2)
            kg_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            remove_table_borders(kg_table)

            # Tổng độ rộng: 165mm (A4 210mm - trái 30mm - phải 15mm)
            col1_kg = kg_table.columns[0]
            col2_kg = kg_table.columns[1]
            col1_kg.width = Mm(45)
            col2_kg.width = Mm(120)

            cell_kg_l = kg_table.cell(0, 0)
            cell_kg_r = kg_table.cell(0, 1)
            cell_kg_l.width = Mm(45)
            cell_kg_r.width = Mm(120)
            set_cell_margins(cell_kg_l, top=0, bottom=0, left=0, right=40)
            set_cell_margins(cell_kg_r, top=0, bottom=0, left=40, right=0)

            # Cột 1: Chữ "Kính gửi:" CANH SÁT LỀ PHẢI
            p_kg_l = cell_kg_l.paragraphs[0]
            p_kg_l.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_kg_l.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            p_kg_l.paragraph_format.line_spacing = Pt(18)
            p_kg_l.paragraph_format.space_before = Pt(6)
            p_kg_l.paragraph_format.space_after = Pt(6)
            r_l = p_kg_l.add_run("Kính gửi: ")
            r_l.font.name = "Times New Roman"
            r_l.font.size = Pt(14)
            r_l.font.italic = True

            # Cột 2: Danh sách cơ quan nhận CANH SÁT LỀ TRÁI (không bị xuống dòng)
            for idx, target in enumerate(kinh_gui):
                p_t = cell_kg_r.paragraphs[0] if idx == 0 else cell_kg_r.add_paragraph()
                p_t.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_t.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                p_t.paragraph_format.line_spacing = Pt(18)
                p_t.paragraph_format.space_before = Pt(6)
                p_t.paragraph_format.space_after = Pt(6)

                target_text = target.strip()
                if len(kinh_gui) > 1 and not target_text.startswith("- "):
                    target_text = f"- {target_text}"

                r_t = p_t.add_run(target_text)
                r_t.font.name = "Times New Roman"
                r_t.font.size = Pt(14)
                r_t.font.bold = False

    def _format_body_paragraph(self, p, first_line_indent_mm=10, before_pt=6, after_pt=6, line_spacing_pt=18, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p.alignment = align
        p.paragraph_format.left_indent = Mm(0)
        p.paragraph_format.right_indent = Mm(0)
        p.paragraph_format.first_line_indent = Mm(first_line_indent_mm)
        p.paragraph_format.space_before = Pt(before_pt)
        p.paragraph_format.space_after = Pt(after_pt)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(line_spacing_pt)

    def _render_paragraph_content(self, p, text, default_bold=False, default_italic=False):
        """
        Quy chuẩn in đậm chỉ mục chuẩn HD 05-HD/VPTW và chỉ đạo của Thường trực Đảng uỷ:
        - Trong TẤT CẢ các loại văn bản (NQ, KH, QD, TB, KL, BC, TTr, CV...):
          Phần chỉ mục (1., 2., 3..., a), b)..., - ) VÀ TIÊU ĐỀ CHỈ MỤC (trước dấu hai chấm :) 
          BẮT BUỘC ĐƯỢC IN ĐẬM ĐỒNG BỘ.
        - Toàn bộ nội dung diễn giải sau dấu hai chấm (:) là chữ IN THƯỜNG (trừ các từ bọc markdown cụ thể).
        - Tuyệt đối KHÔNG in đậm cả đoạn nội dung.
        - Tự động chuẩn hóa dù dữ liệu đầu vào là 1. **Tiêu đề:**, **1. Tiêu đề:**, hay 1. Tiêu đề:.
        """
        text = text.strip()
        if not text:
            return

        if default_bold:
            # Nếu đoạn được chỉ định in đậm toàn bộ (ví dụ đề mục lớn)
            parse_markdown_runs(p, text, base_font_size=14, default_bold=True, default_italic=default_italic)
            return

        # Chuẩn hóa nếu dấu - hoặc + vô tình bị bọc trong markdown **: **- Tiêu đề** -> - **Tiêu đề**
        text = re.sub(r'^\*\*\s*([-+])\s*', r'\1 **', text)

        # 1. Nhận diện cấu trúc Chỉ mục kèm Tiêu đề (có dấu hai chấm :)
        colon_idx = text.find(':')
        if colon_idx != -1:
            prefix_part = text[:colon_idx].strip()
            body_part = text[colon_idx + 1:].strip()
            
            # Làm sạch các ký hiệu markdown trong phần tiền tố và tiêu đề để nhận diện
            clean_prefix = prefix_part.replace('**', '').replace('*', '').strip()
            
            # Khớp tiền tố chỉ mục: Chỉ áp dụng in đậm đồng bộ cho Số (1., 2.) và Chữ cái (a), b), a., b.)
            # Tuyệt đối KHÔNG in đậm chỉ mục dấu gạch ngang (-) và dấu cộng (+) (chuẩn Cấp 4, 5 HD 05-HD/VPTW)
            m_pref = re.match(r'^(\d+\.|[a-z]\)|[a-z]\.)\s*(.*)$', clean_prefix)
            if m_pref:
                indicator_sym = m_pref.group(1).strip()
                indicator_name = m_pref.group(2).strip()
                # Tiêu đề chỉ mục hợp lệ thường có độ dài vừa phải (<= 120 ký tự)
                if indicator_name and len(indicator_name) <= 120:
                    bold_title = f"{indicator_sym} {indicator_name}:"
                    
                    # BẮT BUỘC: In đậm CẢ CHỈ MỤC VÀ TIÊU ĐỀ CHỈ MỤC
                    r_title = p.add_run(bold_title + (" " if body_part else ""))
                    r_title.font.name = "Times New Roman"
                    r_title.font.size = Pt(14)
                    r_title.font.bold = True
                    r_title.font.italic = default_italic
                    r_title.font.color.rgb = RGBColor(0, 0, 0)
                    
                    # Dọn sạch các ký tự markdown thừa ở đầu body_part nếu có
                    clean_body = re.sub(r'^\*\*\s*', '', body_part)
                    if clean_body:
                        # BẮT BUỘC: Nội dung sau dấu hai chấm là chữ in thường
                        parse_markdown_runs(p, clean_body, base_font_size=14, default_bold=False, default_italic=default_italic)
                    return

        # 2. Nhận diện Tiêu đề tiểu mục độc lập (ví dụ: "1. Mục tiêu tổng quát", "2. Nhiệm vụ và giải pháp")
        m_sub = re.match(r'^((?:\d+\.|[a-z]\))\s+[A-ZÀ-Ỹ][^.\n]{2,80})$', text)
        if m_sub:
            clean_sub = text.replace('**', '').replace('*', '').strip()
            r_sub = p.add_run(clean_sub)
            r_sub.font.name = "Times New Roman"
            r_sub.font.size = Pt(14)
            r_sub.font.bold = True
            r_sub.font.italic = default_italic
            r_sub.font.color.rgb = RGBColor(0, 0, 0)
            return

        # 3. Các đoạn nội dung diễn giải thông thường: không in đậm mặc định
        parse_markdown_runs(p, text, base_font_size=14, default_bold=default_bold, default_italic=default_italic)

    def build_body(self):
        """Dựng phần nội dung văn bản (chuẩn Justified, 1cm, Before 6pt, After 6pt, Exactly 18pt)."""
        # Căn cứ pháp lý (nếu có danh sách căn cứ riêng)
        can_cu_list = self.data.get("can_cu", [])
        for cc in can_cu_list:
            p = self.doc.add_paragraph()
            self._format_body_paragraph(p, first_line_indent_mm=10, before_pt=6, after_pt=6, line_spacing_pt=18)
            parse_markdown_runs(p, cc, base_font_size=14, default_italic=True)

        # Nội dung chính
        noi_dung = self.data.get("noi_dung", [])
        
        # Hỗ trợ dạng văn bản thuần chuỗi (Text string có xuống dòng)
        if isinstance(noi_dung, str):
            noi_dung = [line.strip() for line in noi_dung.split("\n") if line.strip()]

        for item in noi_dung:
            if isinstance(item, str):
                text = item.strip()
                if not text:
                    continue
                p = self.doc.add_paragraph()
                
                # 1. Nhận diện Tiêu đề mục lớn độc lập (PHẦN THỨ..., I., II., III. không có nội dung sau dấu :)
                is_major_heading = bool(re.match(r'^(PHẦN\s+[A-Z0-9À-Ỹ]+|[I|V|X]+\.\s+[^\n:]+$)', text))
                
                if is_major_heading:
                    self._format_body_paragraph(p, first_line_indent_mm=10, before_pt=6, after_pt=6, line_spacing_pt=18, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
                    parse_markdown_runs(p, text, base_font_size=14, default_bold=True)
                else:
                    # 2. Đoạn nội dung thân bài: thụt đầu dòng đúng 10mm (1cm), Before 6pt, After 6pt, line spacing 18pt
                    self._format_body_paragraph(p, first_line_indent_mm=10, before_pt=6, after_pt=6, line_spacing_pt=18)
                    self._render_paragraph_content(p, text, default_bold=False)

            elif isinstance(item, dict):
                # Object cấu trúc chi tiết
                text = item.get("text", "")
                indent = item.get("indent", 10)
                align = WD_ALIGN_PARAGRAPH.JUSTIFY
                if item.get("align") == "center":
                    align = WD_ALIGN_PARAGRAPH.CENTER
                elif item.get("align") == "left":
                    align = WD_ALIGN_PARAGRAPH.LEFT
                elif item.get("align") == "right":
                    align = WD_ALIGN_PARAGRAPH.RIGHT

                before = item.get("before", 6)
                after = item.get("after", 6)
                line_spacing = item.get("line_spacing", 18)
                bold = item.get("bold", False)
                italic = item.get("italic", False)

                p = self.doc.add_paragraph()
                self._format_body_paragraph(p, first_line_indent_mm=indent, before_pt=before, after_pt=after, line_spacing_pt=line_spacing, align=align)
                self._render_paragraph_content(p, text, default_bold=bold, default_italic=italic)

    def build_footer(self):
        """Dựng Bảng 1 hàng 2 cột ẩn viền phần Nơi nhận và Thẩm quyền ký."""
        table = self.doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        remove_table_borders(table)

        col1_f = table.columns[0]
        col2_f = table.columns[1]
        col1_f.width = Mm(75)
        col2_f.width = Mm(90)

        cell_f_left = table.cell(0, 0)
        cell_f_right = table.cell(0, 1)
        cell_f_left.width = Mm(75)
        cell_f_right.width = Mm(90)
        set_cell_margins(cell_f_left, top=0, bottom=0, left=0, right=70)
        set_cell_margins(cell_f_right, top=0, bottom=0, left=70, right=0)

        # --- CỘT TRÁI: NƠI NHẬN ---
        noi_nhan_list = self.data.get("noi_nhan", ["- Như trên;", "- Thường trực Đảng uỷ;", "- Lưu VPĐU."])
        p_nn_title = cell_f_left.paragraphs[0]
        p_nn_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_nn_title.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_nn_title.paragraph_format.line_spacing = 1.05
        p_nn_title.paragraph_format.space_before = Pt(0)
        p_nn_title.paragraph_format.space_after = Pt(2)
        r_nn = p_nn_title.add_run("Nơi nhận:")
        r_nn.font.name = "Times New Roman"
        r_nn.font.size = Pt(14)
        r_nn.font.underline = True

        for item in noi_nhan_list:
            p_item = cell_f_left.add_paragraph()
            p_item.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_item.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            p_item.paragraph_format.line_spacing = 1.05
            p_item.paragraph_format.space_before = Pt(0)
            p_item.paragraph_format.space_after = Pt(1)
            r_it = p_item.add_run(item)
            r_it.font.name = "Times New Roman"
            r_it.font.size = Pt(12)

        # --- CỘT PHẢI: THẨM QUYỀN ĐỀ KÝ & HỌ TÊN ---
        tm_text = self.data.get("tham_quyen", "").strip()
        chuc_vu_text = self.data.get("chuc_vu", "BÍ THƯ").strip()
        ho_ten_text = self.data.get("nguoi_ky", "Vũ Thị Thuỳ Trang").strip()

        # Chuẩn hóa thẩm quyền ký khối Văn phòng Đảng uỷ:
        # 1. Nếu ký Thừa lệnh (T/L BAN THƯỜNG VỤ / T/L ĐẢNG UỶ):
        if tm_text.upper().startswith("T/L"):
            # Giữ nguyên tm_text là T/L BAN THƯỜNG VỤ (in đậm)
            # Dòng 2 là chức vụ (CHÁNH VĂN PHÒNG hoặc PHÓ CHÁNH VĂN PHÒNG) viết hoa in thường không in đậm
            pass
        # 2. Nếu Phó Chánh Văn phòng ký thay: Dòng 1 là K/T CHÁNH VĂN PHÒNG, Dòng 2 là PHÓ CHÁNH VĂN PHÒNG
        elif "PHÓ CHÁNH VĂN PHÒNG" in chuc_vu_text.upper():
            tm_text = "K/T CHÁNH VĂN PHÒNG"
            chuc_vu_text = "PHÓ CHÁNH VĂN PHÒNG"
        # 3. Nếu Chánh Văn phòng ký trực tiếp theo thẩm quyền: Ghi trực tiếp CHÁNH VĂN PHÒNG (không có dòng VĂN PHÒNG ĐẢNG UỶ)
        elif chuc_vu_text.upper().strip() == "CHÁNH VĂN PHÒNG":
            tm_text = ""
            chuc_vu_text = "CHÁNH VĂN PHÒNG"
        # 4. Loại bỏ chuỗi 'VĂN PHÒNG ĐẢNG UỶ' nếu bị truyền nhầm vào tham_quyen
        elif "VĂN PHÒNG" in tm_text.upper() and not tm_text.upper().startswith("K/T"):
            tm_text = ""

        p_first = cell_f_right.paragraphs[0]
        p_first.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_first.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_first.paragraph_format.line_spacing = 1.05
        p_first.paragraph_format.space_before = Pt(0)
        p_first.paragraph_format.space_after = Pt(2)

        if tm_text:
            r_tm = p_first.add_run(tm_text)
            r_tm.font.name = "Times New Roman"
            r_tm.font.size = Pt(13.5)
            r_tm.font.bold = True

            p_cv = cell_f_right.add_paragraph()
            p_cv.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cv.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            p_cv.paragraph_format.line_spacing = 1.05
            p_cv.paragraph_format.space_before = Pt(0)
            p_cv.paragraph_format.space_after = Pt(0)
            r_cv = p_cv.add_run(chuc_vu_text)
            r_cv.font.name = "Times New Roman"
            r_cv.font.size = Pt(13.5)
            # Dòng thứ 2 chức danh (BÍ THƯ, PHÓ BÍ THƯ, PHÓ CHÁNH VĂN PHÒNG...): Viết hoa, in thường, không in đậm
            r_cv.font.bold = False
        else:
            # Ghi trực tiếp chức danh (ví dụ: CHÁNH VĂN PHÒNG)
            r_cv = p_first.add_run(chuc_vu_text)
            r_cv.font.name = "Times New Roman"
            r_cv.font.size = Pt(13.5)
            r_cv.font.bold = True

        # Tên người ký nằm cách chức danh đúng 5 dòng (5 dòng cỡ 14pt)
        for _ in range(5):
            p_blank = cell_f_right.add_paragraph()
            p_blank.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_blank.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            p_blank.paragraph_format.line_spacing = Pt(14)
            p_blank.paragraph_format.space_before = Pt(0)
            p_blank.paragraph_format.space_after = Pt(0)
            r_b = p_blank.add_run()
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(14)

        p_ten = cell_f_right.add_paragraph()
        p_ten.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ten.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p_ten.paragraph_format.line_spacing = 1.05
        p_ten.paragraph_format.space_before = Pt(0)
        p_ten.paragraph_format.space_after = Pt(0)
        r_ten = p_ten.add_run(ho_ten_text)
        r_ten.font.name = "Times New Roman"
        r_ten.font.size = Pt(14)
        r_ten.font.bold = True

    def save(self, target_path: str = None) -> str:
        """Lưu tệp .docx vào đường dẫn chỉ định hoặc tự điều hướng theo thể loại."""
        if not target_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            folder_name = self.FOLDER_ROUTING.get(self.doc_type, "Khac")
            year_str = str(datetime.now().year)
            out_dir = os.path.join(base_dir, "van_ban_du_thao", year_str, folder_name)
            os.makedirs(out_dir, exist_ok=True)
            
            prefix = self.doc_type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(out_dir, f"{prefix}_du_thao_{timestamp}.docx")
        else:
            parent_dir = os.path.dirname(os.path.abspath(target_path))
            os.makedirs(parent_dir, exist_ok=True)

        try:
            self.doc.save(target_path)
            print(f"[THÀNH CÔNG] Đã xuất file Word: {target_path}")
            return target_path
        except PermissionError:
            alt_path = target_path.replace(".docx", "_v2.docx")
            self.doc.save(alt_path)
            print(f"[CẢNH BÁO] File gốc đang mở trong Word, đã lưu bản thay thế: {alt_path}")
            return alt_path


# ==============================================================================
# 3. INTERFACE FUNCTIONS & CLI
# ==============================================================================

def export_party_document(data: dict, output_path: str = None) -> str:
    """Hàm công khai nhận dict dữ liệu và xuất ra file Word."""
    builder = PartyDocumentBuilder(data)
    builder.build_header()
    builder.build_title_section()
    builder.build_body()
    builder.build_footer()
    return builder.save(output_path)


def run_demo():
    """Tạo mẫu kiểm thử cho 3 thể loại văn bản Đảng điển hình (CV, KH, TB)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("--- Đang sinh mẫu thử nghiệm thể thức HD 05-HD/VPTW ---")

    # Mẫu 1: Công văn giao việc
    cv_data = {
        "doc_type": "CV",
        "so_hieu": "Số      -CV/ĐU",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "trich_yeu": "V/v tham mưu Kế hoạch thực hiện\nKế hoạch số 101-KH/TU của\nBan Thường vụ Tỉnh uỷ",
        "kinh_gui": ["Uỷ ban nhân dân xã."],
        "noi_dung": [
            "Thực hiện Kế hoạch số 101-KH/TU ngày 15/6/2026 của Ban Thường vụ Tỉnh uỷ về hành động 100 ngày làm việc giải quyết điểm nghẽn về chuyển đổi số; nhằm tập trung tháo gỡ khó khăn, khơi thông các điểm nghẽn, tạo bước chuyển biến rõ nét trong công tác chuyển đổi số và nâng cao hiệu quả phục vụ người dân, doanh nghiệp trên địa bàn xã, Ban Thường vụ Đảng uỷ xã yêu cầu Uỷ ban nhân dân xã triển khai thực hiện các nội dung sau:",
            "1. **Chủ trì, phối hợp với các cơ quan, đơn vị liên quan** khẩn trương nghiên cứu, tham mưu Ban Thường vụ Đảng uỷ xã xây dựng dự thảo Kế hoạch thực hiện Kế hoạch số 101-KH/TU của Ban Thường vụ Tỉnh uỷ. Trong đó, bám sát các mục tiêu, nhiệm vụ và giải pháp trọng tâm; xác định rõ lộ trình thực hiện trong 100 ngày làm việc, phân công trách nhiệm cụ thể.",
            "2. Hoàn chỉnh hồ sơ dự thảo Kế hoạch, báo cáo Thường trực Đảng uỷ và trình Ban Thường vụ Đảng uỷ xã xem xét, cho ý kiến **trước ngày 10/10/2026**.",
            "Uỷ ban nhân dân xã nghiêm túc, khẩn trương tổ chức triển khai thực hiện./."
        ],
        "noi_nhan": [
            "- Như trên;",
            "- Thường trực Đảng uỷ;",
            "- Lưu VPĐU."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "BÍ THƯ",
        "nguoi_ky": "Vũ Thị Thuỳ Trang",
        "output_path": os.path.join(base_dir, "van_ban_du_thao", "2026", "Cong_van", "Demo_CV_giao_viec.docx")
    }
    export_party_document(cv_data, cv_data["output_path"])

    # Mẫu 2: Kế hoạch của Cấp uỷ
    kh_data = {
        "doc_type": "KH",
        "so_hieu": "Số      -KH/ĐU",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "ten_loai": "KẾ HOẠCH",
        "trich_yeu": "thực hiện Kế hoạch số 101-KH/TU ngày 15/6/2026 của Ban Thường vụ Tỉnh uỷ\nvề hành động 100 ngày giải quyết điểm nghẽn chuyển đổi số",
        "can_cu": [
            "Căn cứ Điều lệ Đảng Cộng sản Việt Nam;",
            "Căn cứ Kế hoạch số 101-KH/TU ngày 15/6/2026 của Ban Thường vụ Tỉnh uỷ Khánh Hoà;",
            "Căn cứ Quy chế làm việc số 01-QC/ĐU của Ban Chấp hành Đảng bộ xã Công Hải nhiệm kỳ 2025 - 2030,"
        ],
        "noi_dung": [
            "I. MỤC ĐÍCH, YÊU CẦU",
            "1. **Mục đích:** Cụ thể hoá các mục tiêu, nhiệm vụ của Ban Thường vụ Tỉnh uỷ phù hợp với tình hình thực tiễn tại xã Công Hải; tạo sự chuyển biến căn bản, đột phá trong nhận thức và hành động của cả hệ thống chính trị về chuyển đổi số.",
            "2. **Yêu cầu:** Bám sát nguyên tắc \"5 Rõ\": rõ người, rõ việc, rõ tiến độ, rõ trách nhiệm và rõ hiệu quả. Tuyệt đối không hình thức, khẩu hiệu chung chung.",
            "II. NỘI DUNG VÀ NHIỆM VỤ TRỌNG TÂM",
            "1. Tập trung số hoá 100% hồ sơ, tài liệu nghiệp vụ Đảng bộ xã trước ngày 30/11/2026.",
            "2. Đẩy mạnh hướng dẫn cài đặt và sử dụng dịch vụ công trực tuyến, tài khoản định danh VNeID cho 100% cán bộ, đảng viên và tối thiểu 85% nhân dân trong độ tuổi.",
            "III. TỔ CHỨC THỰC HIỆN",
            "1. **Uỷ ban nhân dân xã:** Chủ trì triển khai các giải pháp hạ tầng kỹ thuật và dịch vụ công trực tuyến.",
            "2. **Văn phòng Đảng uỷ:** Theo dõi, đôn đốc tiến độ thực hiện Kế hoạch này; định kỳ thứ Sáu hằng tuần báo cáo Thường trực Đảng uỷ."
        ],
        "noi_nhan": [
            "- Ban Thường vụ Tỉnh uỷ (b/c);",
            "- Thường trực Đảng uỷ;",
            "- UBND xã, UBMTTQ xã;",
            "- Các chi bộ trực thuộc;",
            "- Lưu VPĐU."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "BÍ THƯ",
        "nguoi_ky": "Vũ Thị Thuỳ Trang",
        "output_path": os.path.join(base_dir, "van_ban_du_thao", "2026", "Ke_hoach", "Demo_KH_chuyen_doi_so.docx")
    }
    export_party_document(kh_data, kh_data["output_path"])

    print("--- Đã hoàn thành sinh toàn bộ mẫu thử nghiệm! ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trình sinh file Word (.docx) văn bản Đảng chuẩn thể thức HD 05-HD/VPTW.")
    parser.add_argument("--input", "-i", type=str, help="Đường dẫn tệp JSON chứa cấu trúc dữ liệu văn bản.")
    parser.add_argument("--output", "-o", type=str, help="Đường dẫn tệp docx đầu ra mong muốn.")
    parser.add_argument("--demo", action="store_true", help="Chạy chế độ sinh thử nghiệm các mẫu văn bản chuẩn.")

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.input:
        if not os.path.exists(args.input):
            print(f"[LỖI] Không tìm thấy file dữ liệu: {args.input}")
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        export_party_document(doc_data, args.output)
    else:
        run_demo()
