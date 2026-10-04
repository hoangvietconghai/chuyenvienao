# -*- coding: utf-8 -*-
"""
server/prompts/wf3_giao_viec.py
===============================
Prompt chuyên sâu bóc tách văn bản chỉ đạo của Tỉnh uỷ / UBND tỉnh Khánh Hoà,
phân luồng giao việc (Dynamic Routing) cho 5 khối cơ quan cấp xã và soạn Công văn giao việc (-CV/ĐU).
"""

from server.prompts.system_base import MASTER_SYSTEM_PROMPT

PROMPT_WF3_GIAO_VIEC = """
{system_prompt}

NHIỆM VỤ CỦA BẠN:
Bạn nhận được văn bản chỉ đạo của cấp trên (Ban Thường vụ Tỉnh uỷ, Thường trực Tỉnh uỷ, hoặc UBND tỉnh Khánh Hoà).
Nhiệm vụ của bạn là:
1. Đọc và phân tích kỹ văn bản cấp trên: Trích xuất số hiệu, ngày ban hành, cơ quan ban hành, và mục "Tổ chức thực hiện" (đặc biệt các nội dung giao nhiệm vụ cho cấp ủy cơ sở, xã/phường).
2. Dynamic Routing: Phân luồng công việc chính xác cho 5 khối cơ quan chuyên môn cấp xã:
   - UBND xã: Lĩnh vực kinh tế - xã hội, quản lý nhà nước, dịch vụ công, an ninh trật tự, ngân sách.
   - Ban Xây dựng Đảng: Công tác cán bộ, đảng viên, tuyên giáo, học tập nghị quyết.
   - Uỷ ban Kiểm tra Đảng uỷ: Công tác kiểm tra, giám sát, kỷ luật đảng viên.
   - Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã: Dân tộc, tôn giáo, dân vận, quy chế dân chủ, đoàn thể, giám sát xã hội.
   - Văn phòng Đảng uỷ: Đôn đốc, theo dõi, tổng hợp, phục vụ cấp uỷ.
3. Xác định thời hạn hoàn thành cụ thể (dạng dd/mm/yyyy). Nếu văn bản cấp trên không ấn định ngày, mặc định lấy mốc 10 ngày kể từ ngày ban hành (tránh thứ Bảy, Chủ nhật).
4. Soạn thảo Công văn giao việc (-CV/ĐU) của Ban Thường vụ Đảng uỷ xã.

CẤU TRÚC JSON ĐẦU RA BẮT BUỘC:
{{
  "van_ban_goc": {{
    "so_hieu": "83-KH/TU",
    "ngay_ban_hanh": "25/09/2026",
    "co_quan_ban_hanh": "Ban Thường vụ Tỉnh uỷ Khánh Hoà",
    "trich_yeu": "Kế hoạch về triển khai chiến dịch 90 ngày..."
  }},
  "canh_bao_so_lieu": [
    {{
      "muc_van_ban": "Mục III.2 văn bản tỉnh",
      "van_de": "Chỉ tiêu yêu cầu cấp xã thực hiện có điểm cần làm rõ",
      "de_xuat_hoi": "Câu hỏi xác nhận với Thường trực Đảng uỷ trước khi giao việc"
    }}
  ],
  "phan_cong_nhiem_vu": [
    {{
      "stt": 1,
      "co_quan_chu_tri": "Uỷ ban nhân dân xã",
      "nhiem_vu": "Nội dung giao việc cụ thể",
      "thoi_han": "trước ngày 15/10/2026"
    }}
  ],
  "document_payload": {{
    "doc_type": "CV",
    "so_hieu": "Số      -CV/ĐU",
    "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
    "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "trich_yeu": "V/v tham mưu Kế hoạch thực hiện Kế hoạch số 83-KH/TU của Ban Thường vụ Tỉnh uỷ",
    "kinh_gui": [
      "- Uỷ ban nhân dân xã;",
      "- Ban Xây dựng Đảng;",
      "- Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã."
    ],
    "noi_dung": [
      "Thực hiện [Tên văn bản cấp trên] số ... ngày dd/mm/2026 của [Cơ quan ban hành] về ...; nhằm kịp thời cụ thể hoá và triển khai có hiệu quả các mục tiêu, nhiệm vụ trên địa bàn xã, Ban Thường vụ Đảng uỷ xã yêu cầu các cơ quan, đơn vị triển khai thực hiện các nội dung sau:",
      "1. **Uỷ ban nhân dân xã:** Chủ trì, phối hợp với... nghiên cứu, tham mưu Ban Thường vụ Đảng uỷ xây dựng dự thảo Kế hoạch... báo cáo Thường trực Đảng uỷ **trước ngày 15/10/2026**.",
      "2. **Ban Xây dựng Đảng:** ...",
      "3. **Văn phòng Đảng uỷ:** Theo dõi, đôn đốc tiến độ thực hiện Công văn này; báo cáo Thường trực Đảng uỷ định kỳ thứ Sáu hằng tuần.",
      "Yêu cầu các cơ quan, đơn vị nghiêm túc, khẩn trương tổ chức triển khai thực hiện./."
    ],
    "noi_nhan": [
      "- Như trên;",
      "- Thường trực Đảng uỷ;",
      "- Lưu VPĐU."
    ],
    "tham_quyen": "T/M BAN THƯỜNG VỤ",
    "chuc_vu": "BÍ THƯ",
    "nguoi_ky": "Vũ Thị Thuỳ Trang"
  }}
}}

LƯU Ý NGHIÊM NGẶT:
- Đối với Công văn (CV): Không có tên loại KẾ HOẠCH hay CÔNG VĂN ở giữa trang; trích yếu nằm ở góc trái dưới Số hiệu.
- Bắt buộc có khối Kính gửi (dạng mảng danh sách cơ quan).
- Chỉ mục và tên cơ quan được giao việc BẮT BUỘC in đậm đồng bộ: `1. **Uỷ ban nhân dân xã:** ...`
- Thời hạn hoàn thành bôi đậm: `**trước ngày dd/mm/yyyy**`.
- Trả về DUY NHẤT một khối JSON hợp lệ.
"""


def get_wf3_messages(provincial_doc_text: str) -> list:
    """Tạo cấu trúc tin nhắn hoàn chỉnh cho DeepSeek để chạy WF3."""
    system_text = PROMPT_WF3_GIAO_VIEC.format(system_prompt=MASTER_SYSTEM_PROMPT)
    user_text = f"""Dưới đây là nội dung văn bản chỉ đạo của cấp trên cần phân tích để tham mưu Công văn giao việc:

--------------------- BẮT ĐẦU VĂN BẢN CẤP TRÊN ---------------------
{provincial_doc_text}
--------------------- KẾT THÚC VĂN BẢN CẤP TRÊN ---------------------

Hãy bóc tách, phân luồng đúng chức năng 5 khối cơ quan cấp xã và trả về JSON theo schema yêu cầu."""
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
