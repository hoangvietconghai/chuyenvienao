# -*- coding: utf-8 -*-
"""
server/prompts/wf1_tong_hop_bao_cao.py
======================================
Prompt chuyên sâu bóc tách và tổng hợp Báo cáo Tuần của Văn phòng Đảng uỷ.
Tối ưu riêng cho DeepSeek: Ràng buộc cấu trúc 4 mảng nghiệp vụ, nguyên tắc giữ nguyên số liệu gốc,
và kiểm tra mâu thuẫn số liệu chéo.
"""

from server.prompts.system_base import MASTER_SYSTEM_PROMPT

PROMPT_WF1_TONG_HOP_BAO_CAO = """
{system_prompt}

NHIỆM VỤ CỦA BẠN:
Bạn nhận được nội dung báo cáo tuần/tháng từ các cơ quan chuyên môn thuộc xã Công Hải (UBND xã, Ban Xây dựng Đảng, Uỷ ban Kiểm tra, Cơ quan UBMTTQVN xã...).
Nhiệm vụ của bạn là:
1. Đọc kỹ và bóc tách thông tin từ các báo cáo thành phần.
2. Kiểm tra tính nhất quán của số liệu: Tuyệt đối giữ nguyên 100% số liệu gốc. Nếu phát hiện số liệu mâu thuẫn giữa các ngành hoặc số liệu bất thường, BẮT BUỘC liệt kê vào mảng `canh_bao_so_lieu`.
3. Tổng hợp thành một Báo cáo Tuần toàn diện của Văn phòng Đảng uỷ (-BC/VPĐU) để báo cáo Thường trực Đảng uỷ.
4. Trình bày nội dung theo bố cục chuẩn mực gồm 4 phần:
   - I. CÔNG TÁC XÂY DỰNG ĐẢNG VÀ HỆ THỐNG CHÍNH TRỊ
   - II. TÌNH HÌNH KINH TẾ - XÃ HỘI, QUỐC PHÒNG - AN NINH
   - III. ĐÁNH GIÁ CHUNG VÀ TỒN TẠI, HẠN CHẾ
   - IV. NHIỆM VỤ TRỌNG TÂM TUẦN TỚI

CẤU TRÚC JSON ĐẦU RA BẮT BUỘC:
{{
  "canh_bao_so_lieu": [
    {{
      "co_quan": "UBND xã",
      "van_de": "Mô tả chi tiết số liệu hoặc điểm mâu thuẫn phát hiện",
      "de_xuat_hoi": "Câu hỏi cụ thể để cán bộ xác nhận với cơ quan báo cáo"
    }}
  ],
  "tong_hop_so_lieu_chinh": {{
    "thu_ngan_sach": "Số liệu kèm đơn vị tính (nếu có)",
    "ket_nap_dang": "Số lượng đảng viên mới (nếu có)",
    "an_ninh_trat_tu": "Số vụ vi phạm (nếu có)",
    "hoat_dong_noi_bat": ["Danh sách các điểm nổi bật nhất"]
  }},
  "document_payload": {{
    "doc_type": "BC",
    "so_hieu": "Số      -BC/VPĐU",
    "co_quan_cap_tren": "ĐẢNG UỶ XÃ CÔNG HẢI",
    "co_quan_ban_hanh": "VĂN PHÒNG",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "ten_loai": "BÁO CÁO",
    "trich_yeu": "tình hình công tác tuần ... năm 2026 và một số nhiệm vụ trọng tâm tuần tới",
    "noi_dung": [
      "I. CÔNG TÁC XÂY DỰNG ĐẢNG VÀ HỆ THỐNG CHÍNH TRỊ",
      "1. **Công tác chính trị tư tưởng và tuyên giáo:** ...",
      "2. **Công tác tổ chức cán bộ và đảng viên:** ...",
      "3. **Công tác kiểm tra, giám sát:** ...",
      "4. **Công tác Mặt trận và đoàn thể:** ...",
      "II. TÌNH HÌNH KINH TẾ - XÃ HỘI, QUỐC PHÒNG - AN NINH",
      "1. **Về kinh tế và ngân sách:** ...",
      "2. **Về văn hóa - xã hội và an sinh:** ...",
      "3. **Về quốc phòng, an ninh và trật tự an toàn xã hội:** ...",
      "III. ĐÁNH GIÁ CHUNG VÀ TỒN TẠI, HẠN CHẾ",
      "1. **Đánh giá chung:** ...",
      "2. **Một số tồn tại, hạn chế:** ...",
      "IV. MỘT SỐ NHIỆM VỤ TRỌNG TÂM TUẦN TỚI",
      "1. ...",
      "2. ..."
    ],
    "noi_nhan": [
      "- Thường trực Đảng uỷ (b/c);",
      "- Các đồng chí UVTV Đảng uỷ;",
      "- Lãnh đạo HĐND, UBND xã;",
      "- Lưu VPĐU."
    ],
    "tham_quyen": "",
    "chuc_vu": "CHÁNH VĂN PHÒNG",
    "nguoi_ky": "Chánh Văn phòng"
  }}
}}

LƯU Ý NGHIÊM NGẶT:
- Các chỉ mục cấp 2 (1., 2., 3.) và tiêu đề chỉ mục BẮT BUỘC in đậm đồng bộ theo mẫu: `1. **Tiêu đề:** Nội dung diễn giải sau dấu hai chấm là chữ thường...`
- Ngày tháng trong nội dung viết dạng số `dd/mm/yyyy`.
- Trả về DUY NHẤT một khối JSON hợp lệ.
"""


def get_wf1_messages(input_reports_text: str, week_number: str = "...") -> list:
    """Tạo cấu trúc tin nhắn hoàn chỉnh cho DeepSeek để chạy WF1."""
    system_text = PROMPT_WF1_TONG_HOP_BAO_CAO.format(system_prompt=MASTER_SYSTEM_PROMPT)
    user_text = f"""Dưới đây là các báo cáo từ các cơ quan, đơn vị gửi về phục vụ tổng hợp Báo cáo tuần số {week_number}:

--------------------- BẮT ĐẦU VĂN BẢN ĐẦU VÀO ---------------------
{input_reports_text}
--------------------- KẾT THÚC VĂN BẢN ĐẦU VÀO ---------------------

Hãy phân tích, đối chiếu số liệu và trả về JSON theo đúng định dạng yêu cầu."""
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
