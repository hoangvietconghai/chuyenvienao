# -*- coding: utf-8 -*-
"""
scripts/generate_cv_lay_y_kien_3tbkl.py
Tạo tệp Word (.docx) Công văn lấy ý kiến Ủy viên Ban Thường vụ Đảng uỷ 
đối với chùm 03 dự thảo Thông báo Kết luận kiểm tra PCTNLPTC năm 2026 (không kèm phiếu).
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.export_docx import PartyDocumentBuilder


def generate_cv_lay_y_kien():
    data_cv = {
        "doc_type": "CV",
        "so_hieu": "Số        -CV/ĐU",
        "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
        "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "trich_yeu": "Góp ý các Dự thảo Thông báo Kết luận kiểm tra\ncủa Ban Thường vụ Đảng uỷ",
        "kinh_gui": ["Các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ."],
        "noi_dung": [
            "Tiếp nhận Báo cáo kết quả kiểm tra của Đoàn kiểm tra theo các Quyết định số 56-QĐ/ĐU, 57-QĐ/ĐU, 58-QĐ/ĐU ngày 15/8/2026 của Ban Thường vụ Đảng uỷ và Báo cáo thẩm định số 19-BC/VPĐU ngày 02/10/2026 của Văn phòng Đảng uỷ về kết quả thẩm định chùm 03 dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực năm 2026;",
            "Thường trực Đảng uỷ kính gửi các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ nghiên cứu, rà soát, đề xuất và đóng góp ý kiến đối với 03 Dự thảo Thông báo Kết luận kiểm tra của Ban Thường vụ Đảng uỷ, cụ thể gồm:",
            "- Dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ thôn Suối Giếng.",
            "- Dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ Trường Mẫu giáo Công Hải.",
            "- Dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ Công an xã.",
            "*(Hồ sơ gửi kèm gồm: 03 bản dự thảo Thông báo Kết luận đã được Văn phòng Đảng uỷ rà soát, chuẩn hóa thể thức và Báo cáo thẩm định tổng hợp số 19-BC/VPĐU)*.",
            "Đề nghị các đồng chí nghiên cứu, tham gia đóng góp ý kiến bằng văn bản hoặc góp ý trực tiếp vào các bản dự thảo (gửi kèm); nội dung góp ý gửi về Thường trực Đảng uỷ (qua Văn phòng Đảng uỷ) **trước ngày 08/10/2026** để tổng hợp, tiếp thu và hoàn thiện các văn bản trình đồng chí Bí thư Đảng uỷ ký ban hành chính thức.",
            "Qua thời gian nêu trên, nếu các đồng chí không có ý kiến gửi về xem như thống nhất với nội dung các Dự thảo Thông báo Kết luận./."
        ],
        "noi_nhan": [
            "- Như trên;",
            "- Thường trực Đảng uỷ (để b/c);",
            "- Lưu VPĐU (CV-2026)."
        ],
        "tham_quyen": "T/L BAN THƯỜNG VỤ",
        "chuc_vu": "PHÓ CHÁNH VĂN PHÒNG",
        "nguoi_ky": "Ngô Hoàng Việt"
    }

    builder = PartyDocumentBuilder(data_cv)
    builder.build_header()
    builder.build_title_section()
    builder.build_body()
    builder.build_footer()

    out_file = os.path.abspath(r"van_ban_du_thao\CV_lay_y_kien_BTV_ve_03_TBKL_kiem_tra_PCTNLPTC_2026.docx")
    builder.save(out_file)
    print(f"Đã xuất Công văn lấy ý kiến chùm 03 TBKL: {out_file}")
    return out_file


if __name__ == "__main__":
    generate_cv_lay_y_kien()
