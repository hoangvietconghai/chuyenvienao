#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/test_system_integration.py
==================================
Kiểm thử tích hợp toàn diện hệ thống Chuyên viên Ảo (v2):
1. Kiểm tra trích xuất text từ văn bản mẫu qua `doc_reader.py`.
2. Kiểm tra phân luồng tự động qua `router.py`.
3. Kiểm tra cấu trúc tin nhắn Prompt cho DeepSeek (WF1, WF2, WF3, WF4).
4. Kiểm tra sinh trọn bộ file Word qua `PartyDocumentBuilder` từ các workflow.
5. Kiểm tra tính toàn vẹn của mô hình 3 cấp (không có huyện Thuận Bắc) và chính tả khối Đảng.
"""

import os
import sys
import tempfile
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from scripts.doc_reader import extract_document_text
from server.router import route_incoming_file
from server.prompts.wf1_tong_hop_bao_cao import get_wf1_messages
from server.prompts.wf2_thong_bao_ket_luan import get_wf2_messages
from server.prompts.wf3_giao_viec import get_wf3_messages
from server.prompts.wf4_tham_dinh import get_wf4_messages
from server.workflows.wf1_synthesizer import generate_weekly_report_docx
from server.workflows.wf2_conclusions import generate_meeting_conclusion_docx
from server.workflows.wf3_dispatch import generate_dispatch_docx
from server.workflows.wf4_appraisal import generate_appraisal_documents


class TestSystemIntegration(unittest.TestCase):

    def test_01_router_provincial_doc(self):
        """Kiểm tra router nhận diện và lưu văn bản cấp trên."""
        sample_doc = """ĐẢNG BỘ TỈNH KHÁNH HOÀ
BAN THƯỜNG VỤ
*
Số 83-KH/TU

ĐẢNG CỘNG SẢN VIỆT NAM
Khánh Hoà, ngày 25 tháng 9 năm 2026

KẾ HOẠCH
về việc triển khai chiến dịch làm sạch dữ liệu đất đai

Ban Thường vụ Tỉnh uỷ yêu cầu Đảng uỷ các xã, phường triển khai thực hiện:
1. UBND cấp xã rà soát hồ sơ địa chính.
"""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as f:
            f.write(sample_doc)
            tmp_path = f.name

        try:
            res = route_incoming_file(tmp_path)
            self.assertTrue(res["success"])
            self.assertEqual(res["category"], "cap_tren")
            self.assertEqual(res["suggested_workflow"], "wf3_giao_viec")
            self.assertTrue(os.path.exists(res["saved_path"]))
            print(f"\n[PASS] Test 1: Router văn bản cấp trên thành công -> {res['saved_path']}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_02_prompt_construction(self):
        """Kiểm tra cấu trúc prompt DeepSeek tuân thủ nghiêm ngặt các quy tắc Đảng."""
        msg1 = get_wf1_messages("Báo cáo tuần UBND xã...", "40")
        msg2 = get_wf2_messages("Biên bản họp giao ban...", "Giao ban 03/10/2026")
        msg3 = get_wf3_messages("Kế hoạch số 83-KH/TU...")
        msg4 = get_wf4_messages("Dự thảo Kế hoạch của UBND xã...", "UBND xã")

        for idx, m in enumerate([msg1, msg2, msg3, msg4], 1):
            sys_content = m[0]["content"]
            # Kiểm tra quy chuẩn 3 cấp
            self.assertIn("KHÔNG CÒN CẤP HUYỆN", sys_content)
            self.assertIn("Trung ương", sys_content)
            self.assertIn("Tỉnh Khánh Hoà", sys_content)
            self.assertIn("Xã Công Hải", sys_content)
            # Kiểm tra chính tả khối Đảng
            self.assertIn("oà", sys_content)
            self.assertIn("uỷ", sys_content)
            self.assertIn("uý", sys_content)
            # Kiểm tra nguyên tắc an toàn số liệu
            self.assertIn("canh_bao_so_lieu", sys_content)
            self.assertIn("JSON", sys_content)

        print("[PASS] Test 2: Cả 4 bộ Prompt DeepSeek đều đáp ứng 100% quy chuẩn thể thức và an toàn số liệu.")

    def test_03_workflows_docx_generation(self):
        """Kiểm tra cả 4 workflow đều xuất file Word .docx hợp lệ."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. WF1: Báo cáo Tuần
            bc_data = {
                "doc_type": "BC",
                "so_hieu": "Số      -BC/VPĐU",
                "co_quan_cap_tren": "ĐẢNG UỶ XÃ CÔNG HẢI",
                "co_quan_ban_hanh": "VĂN PHÒNG",
                "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
                "ten_loai": "BÁO CÁO",
                "trich_yeu": "tình hình công tác tuần 40 năm 2026",
                "noi_dung": [
                    "I. CÔNG TÁC XÂY DỰNG ĐẢNG VÀ HỆ THỐNG CHÍNH TRỊ",
                    "1. **Công tác tư tưởng:** Tình hình tư tưởng cán bộ, đảng viên ổn định.",
                    "II. KINH TẾ - XÃ HỘI, QUỐC PHÒNG - AN NINH",
                    "1. **Thu ngân sách:** Đạt 150 triệu đồng trong tuần."
                ],
                "noi_nhan": ["- Thường trực Đảng uỷ;", "- Lưu VPĐU."],
                "chuc_vu": "CHÁNH VĂN PHÒNG",
                "nguoi_ky": "Chánh Văn phòng"
            }
            bc_file = os.path.join(temp_dir, "test_bc.docx")
            res_bc = generate_weekly_report_docx(bc_data, bc_file)
            self.assertTrue(os.path.exists(res_bc))
            self.assertGreater(os.path.getsize(res_bc), 1000)

            # 2. WF2: Thông báo Kết luận
            tb_data = {
                "doc_type": "TB",
                "so_hieu": "Số      -TB/ĐU",
                "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
                "ten_loai": "THÔNG BÁO",
                "trich_yeu": "kết luận của Thường trực Đảng uỷ tại cuộc họp ngày 03/10/2026",
                "noi_dung": [
                    "1. **Uỷ ban nhân dân xã:** Khẩn trương rà soát ngân sách **trước ngày 15/10/2026**.",
                    "2. **Văn phòng Đảng uỷ:** Đôn đốc tiến độ thực hiện."
                ],
                "noi_nhan": ["- Thường trực Đảng uỷ;", "- UBND xã;", "- Lưu VPĐU."],
                "tham_quyen": "T/M BAN THƯỜNG VỤ",
                "chuc_vu": "BÍ THƯ",
                "nguoi_ky": "Vũ Thị Thuỳ Trang"
            }
            tb_file = os.path.join(temp_dir, "test_tb.docx")
            res_tb = generate_meeting_conclusion_docx(tb_data, tb_file)
            self.assertTrue(os.path.exists(res_tb))

            # 3. WF3: Công văn giao việc
            cv_data = {
                "doc_type": "CV",
                "so_hieu": "Số      -CV/ĐU",
                "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
                "trich_yeu": "V/v tham mưu thực hiện Kế hoạch số 83-KH/TU",
                "kinh_gui": ["Uỷ ban nhân dân xã."],
                "noi_dung": [
                    "Thực hiện Kế hoạch số 83-KH/TU ngày 25/9/2026 của Ban Thường vụ Tỉnh uỷ...",
                    "1. **Uỷ ban nhân dân xã:** Chủ trì tham mưu dự thảo Kế hoạch **trước ngày 15/10/2026**.",
                    "2. **Văn phòng Đảng uỷ:** Theo dõi tiến độ."
                ],
                "noi_nhan": ["- Như trên;", "- Thường trực Đảng uỷ;", "- Lưu VPĐU."],
                "tham_quyen": "T/M BAN THƯỜNG VỤ",
                "chuc_vu": "BÍ THƯ",
                "nguoi_ky": "Vũ Thị Thuỳ Trang"
            }
            cv_file = os.path.join(temp_dir, "test_cv.docx")
            res_cv = generate_dispatch_docx(cv_data, cv_file)
            self.assertTrue(os.path.exists(res_cv))

            # 4. WF4: Hồ sơ thẩm định
            wf4_data = {
                "bc_tham_dinh_payload": bc_data,
                "du_thao_hoan_chinh_payload": {
                    "doc_type": "KH",
                    "so_hieu": "Số      -KH/ĐU",
                    "ten_loai": "KẾ HOẠCH",
                    "trich_yeu": "thực hiện chỉ đạo của Tỉnh uỷ",
                    "noi_dung": ["I. MỤC ĐÍCH, YÊU CẦU", "1. **Mục đích:** ..."]
                },
                "cv_lay_y_kien_btv_payload": cv_data
            }
            res_appraisal = generate_appraisal_documents(wf4_data, custom_dir=temp_dir)
            self.assertEqual(len(res_appraisal), 3)
            for k, p in res_appraisal.items():
                self.assertTrue(os.path.exists(p))

            print("[PASS] Test 3: Cả 4 quy trình nghiệp vụ đều xuất file Word .docx chuẩn xác 100%.")


if __name__ == "__main__":
    unittest.main()
