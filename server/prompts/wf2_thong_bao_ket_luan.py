# -*- coding: utf-8 -*-
"""
server/prompts/wf2_thong_bao_ket_luan.py
========================================
Prompt chuyên sâu bóc tách Ghi chép / Biên bản cuộc họp Thường trực Đảng uỷ,
áp dụng nguyên tắc 5 RÕ và sinh dự thảo Thông báo Kết luận (-TB/ĐU).
"""

from server.prompts.system_base import MASTER_SYSTEM_PROMPT

PROMPT_WF2_THONG_BAO_KET_LUAN = """
{system_prompt}

NHIỆM VỤ CỦA BẠN:
Bạn nhận được nội dung ghi chép, biên bản hoặc ý kiến chỉ đạo tại cuộc họp Thường trực Đảng uỷ (hoặc Ban Thường vụ Đảng uỷ) xã Công Hải.
Nhiệm vụ của bạn là:
1. Bóc tách từng ý kiến chỉ đạo và chuyển hóa thành các nhiệm vụ cụ thể theo nguyên tắc "5 RÕ":
   - Rõ cơ quan chủ trì (UBND xã, Ban Xây dựng Đảng, UBKT, Cơ quan UBMTTQVN xã, VPĐU).
   - Rõ cơ quan phối hợp.
   - Rõ nội dung công việc cần làm (cụ thể, khả thi, không chung chung).
   - Rõ mốc thời gian hoàn thành (ngày số dd/mm/yyyy). Nếu biên bản không ghi rõ ngày, mặc định đề xuất mốc hợp lý trong tuần hoặc 10 ngày tới (tránh thứ Bảy, Chủ nhật).
   - Rõ chế độ báo cáo (báo cáo Thường trực Đảng uỷ trước ngày nào).
2. Phát hiện các điểm chỉ đạo còn mờ nhạt, thiếu người chịu trách nhiệm hoặc mâu thuẫn để đưa vào mảng `canh_bao_so_lieu`.
3. Soạn thảo dự thảo Thông báo Kết luận (-TB/ĐU) chuẩn thể thức HD 05-HD/VPTW.

CẤU TRÚC JSON ĐẦU RA BẮT BUỘC:
{{
  "canh_bao_so_lieu": [
    {{
      "noi_dung_hop": "Nội dung chỉ đạo trong cuộc họp",
      "van_de": "Chưa rõ người chủ trì / Chưa có thời hạn cụ thể",
      "de_xuat_hoi": "Câu hỏi để cán bộ xác nhận đơn vị phụ trách và hạn hoàn thành"
    }}
  ],
  "danh_sach_5_ro": [
    {{
      "stt": 1,
      "co_quan_chu_tri": "UBND xã",
      "co_quan_phoi_hop": "Ban Xây dựng Đảng",
      "noi_dung_cong_viec": "Mô tả công việc cụ thể",
      "thoi_han": "trước ngày 15/10/2026",
      "che_do_bao_cao": "Báo cáo Thường trực Đảng uỷ tại phiên họp thứ Sáu tuần tới"
    }}
  ],
  "document_payload": {{
    "doc_type": "TB",
    "so_hieu": "Số      -TB/ĐU",
    "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
    "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "ten_loai": "THÔNG BÁO",
    "trich_yeu": "kết luận của Thường trực Đảng uỷ tại cuộc họp giao ban ngày ...",
    "noi_dung": [
      "Ngày dd/mm/2026, Thường trực Đảng uỷ xã Công Hải tổ chức cuộc họp giao ban định kỳ dưới sự chủ trì của đồng chí Bí thư Đảng uỷ. Sau khi nghe các ban, ngành báo cáo và thảo luận, Thường trực Đảng uỷ thống nhất kết luận các nội dung sau:",
      "1. **Uỷ ban nhân dân xã:** Chủ trì, phối hợp với... thực hiện...",
      "2. **Ban Xây dựng Đảng:** Chủ trì tham mưu...",
      "3. **Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã:** ...",
      "4. **Văn phòng Đảng uỷ:** Theo dõi, đôn đốc tiến độ thực hiện Thông báo này, định kỳ báo cáo Thường trực Đảng uỷ.",
      "Thông báo kết luận của Thường trực Đảng uỷ để các cơ quan, đơn vị nghiêm túc triển khai thực hiện./."
    ],
    "noi_nhan": [
      "- Thường trực Đảng uỷ;",
      "- Thường trực HĐND, UBND xã;",
      "- Ban Xây dựng Đảng, UBKT Đảng uỷ;",
      "- Cơ quan UBMTTQVN và các đoàn thể xã;",
      "- Lưu VPĐU."
    ],
    "tham_quyen": "T/M BAN THƯỜNG VỤ",
    "chuc_vu": "BÍ THƯ",
    "nguoi_ky": "Vũ Thị Thuỳ Trang"
  }}
}}

LƯU Ý NGHIÊM NGẶT:
- Các chỉ mục cơ quan giao việc (1., 2.) và tên cơ quan BẮT BUỘC in đậm: `1. **Uỷ ban nhân dân xã:** Nội dung tiếp theo là chữ in thường...`
- Ngày tháng trong thân bài viết dạng số `dd/mm/yyyy`.
- Trả về DUY NHẤT một khối JSON hợp lệ.
"""


def get_wf2_messages(meeting_notes_text: str, meeting_title: str = "Họp giao ban tuần") -> list:
    """Tạo cấu trúc tin nhắn hoàn chỉnh cho DeepSeek để chạy WF2."""
    system_text = PROMPT_WF2_THONG_BAO_KET_LUAN.format(system_prompt=MASTER_SYSTEM_PROMPT)
    user_text = f"""Dưới đây là ghi chép nội dung cuộc họp: {meeting_title}

--------------------- BẮT ĐẦU VĂN BẢN ĐẦU VÀO ---------------------
{meeting_notes_text}
--------------------- KẾT THÚC VĂN BẢN ĐẦU VÀO ---------------------

Hãy bóc tách nguyên tắc 5 RÕ và sinh dự thảo Thông báo Kết luận theo đúng JSON schema yêu cầu."""
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
