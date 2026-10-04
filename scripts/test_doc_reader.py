#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/test_doc_reader.py
==========================
Unit test cho module doc_reader.py:
- Kiểm tra đọc tệp DOCX thực tế
- Kiểm tra tạo và đọc tệp TXT
- Kiểm tra tạo và đọc tệp PDF qua PyMuPDF
- Kiểm tra tính đúng đắn của siêu dữ liệu bóc tách
"""

import os
import sys
import tempfile
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from scripts.doc_reader import extract_document_text, extract_metadata_heuristics


class TestDocReader(unittest.TestCase):

    def test_read_real_docx(self):
        docx_path = os.path.join(BASE_DIR, "van_ban_du_thao", "2026", "Ke_hoach", "TC05_KH_Kiem_tra_chi_muc.docx")
        if os.path.exists(docx_path):
            result = extract_document_text(docx_path)
            self.assertEqual(result["format"], "docx")
            self.assertGreater(len(result["text"]), 100)
            print(f"\n[PASS] Đọc DOCX thực tế thành công ({len(result['text'])} ký tự).")
        else:
            print("\n[SKIP] Không tìm thấy tệp DOCX mẫu để kiểm tra.")

    def test_read_txt_and_heuristics(self):
        sample_text = """ĐẢNG BỘ TỈNH KHÁNH HOÀ
BAN THƯỜNG VỤ
*
Số 83-KH/TU

ĐẢNG CỘNG SẢN VIỆT NAM
Khánh Hoà, ngày 25 tháng 9 năm 2026

KẾ HOẠCH
về việc triển khai chiến dịch 90 ngày làm sạch dữ liệu đất đai

Thực hiện chỉ đạo của Ban Thường vụ Tỉnh uỷ...
Ban Thường vụ Tỉnh uỷ yêu cầu các địa phương thực hiện các nhiệm vụ sau:
1. Uỷ ban nhân dân cấp xã rà soát toàn bộ dữ liệu địa chính.
"""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as f:
            f.write(sample_text)
            temp_path = f.name

        try:
            result = extract_document_text(temp_path)
            self.assertEqual(result["format"], "txt")
            meta = result["metadata"]
            self.assertEqual(meta["so_hieu"], "83-KH/TU")
            self.assertEqual(meta["ngay_thang"], "25/09/2026")
            self.assertEqual(meta["co_quan_ban_hanh"], "Ban Thường vụ Tỉnh uỷ Khánh Hoà")
            self.assertEqual(meta["suggested_type"], "cap_tren")
            self.assertEqual(meta["suggested_wf"], "wf3_giao_viec")
            print("\n[PASS] Đọc TXT và nhận diện siêu dữ liệu Heuristics thành công 100%.")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_read_pdf_generation(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF không được cài đặt")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name

        try:
            doc = fitz.open()
            page = doc.new_page()
            font_path = "C:/Windows/Fonts/times.ttf"
            if os.path.exists(font_path):
                page.insert_font(fontname="times", fontfile=font_path)
                page.insert_text(
                    (50, 72),
                    "ĐẢNG UỶ XÃ CÔNG HẢI\nSố 12-BC/UBND\nBáo cáo tình hình tuần 40",
                    fontsize=12,
                    fontname="times"
                )
            else:
                page.insert_text(
                    (50, 72),
                    "DANG UY XA CONG HAI\nSo 12-BC/UBND\nBao cao tinh hinh tuan 40",
                    fontsize=12
                )
            doc.save(pdf_path)
            doc.close()

            result = extract_document_text(pdf_path)
            self.assertEqual(result["format"], "pdf")
            self.assertIn("Báo cáo tình hình tuần 40", result["text"])
            self.assertEqual(result["metadata"]["suggested_type"], "bao_cao_co_so")
            self.assertEqual(result["metadata"]["suggested_wf"], "wf1_tong_hop_bao_cao")
            print("[PASS] Tạo và đọc PDF thử nghiệm thành công 100%.")
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)


if __name__ == "__main__":
    unittest.main()
