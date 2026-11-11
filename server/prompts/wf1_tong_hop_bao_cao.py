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
Bạn nhận được nội dung báo cáo tuần từ các cơ quan chuyên môn thuộc xã Công Hải (UBND xã, Ban Xây dựng Đảng, Uỷ ban Kiểm tra, Cơ quan UBMTTQVN xã, Sổ văn bản đi của Đảng uỷ...).
Nhiệm vụ của bạn là tổng hợp Báo cáo Tuần của Văn phòng Đảng uỷ (-BC/VPĐU) theo đúng **Mô hình Chuẩn tối ưu của Văn phòng Đảng uỷ xã Công Hải**:

1. Đọc kỹ và bóc tách thông tin từ các báo cáo thành phần (UBND xã) và Sổ văn bản đi của Đảng uỷ trong tuần.
2. Tuyệt đối giữ nguyên 100% số liệu gốc (thu ngân sách, chi ngân sách, giải ngân đầu tư công, diện tích mùa vụ, đối tượng trợ cấp, TTHC...).
3. BỐ CỤC CHUẨN TỐI ƯU GỒM 02 PHẦN LỚN:

   **I. KẾT QUẢ TRIỂN KHAI NHIỆM VỤ**
   - **1. Công tác lãnh đạo, chỉ đạo của Thường trực, Ban Thường vụ Đảng uỷ:**
     + Về quán triệt, tuyên truyền và triển khai các văn bản của cấp trên (Nghị quyết, Chỉ thị, Hướng dẫn của TW, Tỉnh uỷ).
     + Chỉ đạo các cơ quan, đơn vị, các chi bộ trực thuộc triển khai các kế hoạch, nhiệm vụ trọng tâm của Đảng uỷ.
     + Các cuộc họp Thường trực, Ban Thường vụ Đảng uỷ trong tuần, làm việc với các chi bộ thôn, kết luận chỉ đạo.
     + Hoạt động tham dự hội nghị cấp trên và sự kiện của Thường trực Đảng uỷ; kết quả ban hành văn bản đi trong tuần.
   - **2. Công tác chỉ đạo, điều hành của Uỷ ban nhân dân xã:**
     (Gom súc tích theo các gạch đầu dòng chuyên đề lớn):
     + Về kinh tế, ngân sách và đầu tư công (thu - chi ngân sách, tiến độ giải ngân đầu tư công).
     + Về nông nghiệp, nông thôn mới và quản lý đất đai (cây trồng, vật nuôi, NTM, cấp GCN, đăng ký đất đai).
     + Về xây dựng, công thương và các dự án trọng điểm (GPMB đường sắt tốc độ cao, các công trình hạ tầng).
     + Về văn hoá - xã hội và chính sách an sinh (trợ cấp xã hội qua tài khoản, BHYT, lao động việc làm).
     + Về cải cách hành chính và chuyển đổi số (tiếp nhận hồ sơ TTHC, trực tuyến 100%, Đề án 06).
     + Về quốc phòng - an ninh và nội chính (trực SSCĐ, tuần tra ANTT, PCCC, tiếp công dân).

   **II. NHIỆM VỤ TRỌNG TÂM TUẦN TỚI (TUẦN ...)**
   Mở đầu: *"Thường trực, Ban Thường vụ Đảng uỷ tập trung lãnh đạo, chỉ đạo triển khai thực hiện các nhiệm vụ trọng tâm... Trọng tâm lãnh đạo, chỉ đạo các khối cơ quan tuần ...:"*
   Phân công nhiệm vụ cụ thể cho **06 khối cơ quan / đầu mối thực hiện (Nguyên tắc 5 Rõ)**:
   - **1. Uỷ ban nhân dân xã:** Tập trung giải ngân, giải quyết điểm nóng cơ sở, PCCC, đất đai, an ninh trật tự...
   - **2. Ban Xây dựng Đảng:** Công tác tư tưởng, tuyên giáo, chuẩn hoá dữ liệu đảng viên, sinh hoạt chi bộ...
   - **3. Uỷ ban Kiểm tra Đảng uỷ:** Kiểm tra, giám sát theo kế hoạch và giám sát sau các cuộc họp BTV...
   - **4. Uỷ ban Mặt trận Tổ quốc Việt Nam xã:** Ngày hội Đại đoàn kết, Tháng vì người nghèo, Dân vận khéo...
   - **5. Văn phòng Đảng uỷ:** Chuẩn bị nội dung giao ban, đôn đốc kết luận, phục vụ Thường trực/BTV...
   - **6. Các chi bộ trực thuộc Đảng uỷ:** Sinh hoạt chi bộ, chuẩn hoá dữ liệu đảng viên, đời sống nhân dân ở thôn...

   Đoạn kết: *"Trên đây là Báo cáo tình hình công tác tuần ... và một số nhiệm vụ trọng tâm tuần ... Văn phòng Đảng uỷ báo cáo Thường trực Đảng uỷ xem xét, chỉ đạo./."*

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
    "thu_ngan_sach": "Số liệu kèm đơn vị tính",
    "giai_ngan_dau_tu": "Tỷ lệ % và số tiền",
    "hoat_dong_noi_bat": ["Danh sách các điểm nổi bật nhất"]
  }},
  "document_payload": {{
    "doc_type": "BC",
    "so_hieu": "Số      -BC/VPĐU",
    "co_quan_cap_tren": "ĐẢNG UỶ XÃ CÔNG HẢI",
    "co_quan_ban_hanh": "VĂN PHÒNG",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "ten_loai": "BÁO CÁO",
    "trich_yeu": "tình hình thực hiện công tác tuần ... và một số nhiệm vụ trọng tâm tuần ...",
    "noi_dung": [
      "Thực hiện Chương trình công tác của Thường trực, Ban Thường vụ Đảng uỷ tuần ... Văn phòng Đảng uỷ xã báo cáo tình hình công tác tuần ... và nhiệm vụ trọng tâm tuần ... như sau:",
      "**I. KẾT QUẢ TRIỂN KHAI NHIỆM VỤ**",
      "**1. Công tác lãnh đạo, chỉ đạo của Thường trực, Ban Thường vụ Đảng uỷ:**",
      "- Về quán triệt, tuyên truyền và triển khai các văn bản của cấp trên: ...",
      "- Chỉ đạo các cơ quan, đơn vị, các chi bộ trực thuộc...: ...",
      "- Trong tuần, Thường trực, Ban Thường vụ Đảng uỷ họp...: ...",
      "- Thường trực Đảng uỷ tham dự các hội nghị...: ...",
      "**2. Công tác chỉ đạo, điều hành của Uỷ ban nhân dân xã:**",
      "- Về kinh tế, ngân sách và đầu tư công: ...",
      "- Về nông nghiệp, nông thôn mới và quản lý đất đai: ...",
      "- Về văn hoá - xã hội và chính sách an sinh: ...",
      "- Về cải cách hành chính và chuyển đổi số: ...",
      "- Về quốc phòng - an ninh: ...",
      "**II. NHIỆM VỤ TRỌNG TÂM TUẦN TỚI (TUẦN ...)**",
      "Thường trực, Ban Thường vụ Đảng uỷ tập trung lãnh đạo, chỉ đạo triển khai thực hiện các nhiệm vụ trọng tâm... Trọng tâm lãnh đạo, chỉ đạo các khối cơ quan tuần ...:",
      "**1. Uỷ ban nhân dân xã:** ...",
      "**2. Ban Xây dựng Đảng:** ...",
      "**3. Uỷ ban Kiểm tra Đảng uỷ:** ...",
      "**4. Uỷ ban Mặt trận Tổ quốc Việt Nam xã:** ...",
      "**5. Văn phòng Đảng uỷ:** ...",
      "**6. Các chi bộ trực thuộc Đảng uỷ:** ...",
      "Trên đây là Báo cáo tình hình công tác tuần ... Văn phòng Đảng uỷ báo cáo Thường trực Đảng uỷ xem xét, chỉ đạo./."
    ],
    "noi_nhan": [
      "- Thường trực Đảng uỷ (để b/c);",
      "- Ban Thường vụ Đảng uỷ;",
      "- Thường trực HĐND, UBND xã;",
      "- Các cơ quan tham mưu Đảng uỷ;",
      "- Uỷ ban MTTQ và các đoàn thể xã;",
      "- Lưu: VPĐU."
    ],
    "tham_quyen": "",
    "chuc_vu": "PHÓ CHÁNH VĂN PHÒNG",
    "nguoi_ky": "Ngô Hoàng Việt"
  }}
}}

LƯU Ý NGHIÊM NGẶT:
- In đậm đúng các chỉ mục cấp 1 và cấp 2.
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
