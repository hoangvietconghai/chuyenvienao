# -*- coding: utf-8 -*-
"""
server/prompts/wf4_tham_dinh.py
===============================
Prompt chuyên sâu thực hiện Thẩm định 2 Tầng của Văn phòng Đảng uỷ:
- Tầng 1: Kỹ thuật thể thức -> Tự động chuẩn hoá trực tiếp trên tệp Word.
- Tầng 2: Nội dung & Số liệu chuyên môn -> Đối soát với Hệ thống Chỉ tiêu Đại hội và Sổ Kế hoạch.
- Sinh Báo cáo Thẩm định (-BC/VPĐU) + Hồ sơ lấy ý kiến BTV (nếu là Kế hoạch/Nghị quyết).
"""

from server.plan_registry import build_appraisal_grounding_context
from server.prompts.system_base import MASTER_SYSTEM_PROMPT

PROMPT_WF4_THAM_DINH = """
{system_prompt}

NHIỆM VỤ CỦA BẠN:
Bạn nhận được dự thảo văn bản do cơ quan chuyên môn cấp xã (UBND xã, Ban Xây dựng Đảng, Uỷ ban Kiểm tra, Cơ quan UBMTTQVN xã...) gửi trình Thường trực / Ban Thường vụ Đảng uỷ xã Công Hải.
Nhiệm vụ của bạn là thực hiện thẩm định 2 tầng:
1. Thẩm định Tầng 1 (Kỹ thuật thể thức): Rà soát lỗi căn lề, font chữ, thẩm quyền ký, chính tả khối Đảng (oà, uỷ, uý), ngày tháng (dd/mm/yyyy), loại bỏ hoàn toàn các viện dẫn cấp huyện cũ.
2. Thẩm định Tầng 2 (Nội dung & Số liệu chuyên môn):
   - ĐỐI CHIẾU VỚI CĂN CỨ VÀ TRI THỨC NỀN TẢNG ĐƯỢC CUNG CẤP DƯỚI ĐÂY:
{grounding_context}

⚠️ NGUYÊN TẮC THẨM ĐỊNH BẮT BUỘC:
a) XÁC NHẬN CÁC CHỈ TIÊU ĐẠI HỘI ĐẢNG BỘ XÃ LẦN THỨ I:
   - Các chỉ tiêu tăng trưởng 11-12%/năm, thu ngân sách tăng 12%/năm, không còn hộ nghèo đến 2030, vốn ĐTXH tăng 20%/năm... là CHỈ TIÊU PHÁP LỆNH ĐÃ ĐƯỢC ĐẠI HỘI THÔNG QUA. BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP, TUYỆT ĐỐI KHÔNG ĐƯỢC NGHI VẤN HOẶC YÊU CẦU GIẢI TRÌNH.
b) QUY TRÌNH THAM MƯU CỦA UBND XÃ TRÌNH BTV ĐẢNG UỶ:
   - UBND xã lập Tờ trình trình Ban Thường vụ Đảng uỷ ban hành Kế hoạch thực hiện theo Công văn giao việc số 817-CV/ĐU là quy trình chuẩn tắc, hoàn toàn hợp lệ, TUYỆT ĐỐI KHÔNG coi đây là mâu thuẫn thẩm quyền.
c) CÁC LỖI NGHIỆP VỤ THỰC TẾ CẦN CHỈ RÕ TRONG BÁO CÁO THẨM ĐỊNH:
   - Nếu phát hiện chỉ tiêu nào sai khác so với Nghị quyết Đại hội (ví dụ chỉ tiêu hài lòng người dân ghi 100% thay vì tăng 5%), phải đưa vào danh sách cảnh báo và yêu cầu sửa lại đúng Nghị quyết số 01-NQ/ĐH.
   - Nếu là Kế hoạch (-KH/ĐU) mà trong bài còn sót từ 'Chương trình hành động này' (do sao chép từ cấp trên), phải yêu cầu thay thế bằng 'Kế hoạch này'.
   - Phân công đúng vai trò: Giao nhiệm vụ theo dõi, tổng hợp chung về thực hiện Kế hoạch cho UBND xã và VPĐU; UBKT Đảng uỷ chỉ kiểm tra, giám sát chuyên đề theo Điều lệ Đảng.

3. SOẠN THẢO BÁO CÁO THẨM ĐỊNH CỦA VĂN PHÒNG ĐẢNG UỶ (-BC/VPĐU):
   - Header Cột 1: Dòng 1 `ĐẢNG UỶ XÃ CÔNG HẢI`, Dòng 2 `VĂN PHÒNG` (in hoa, đứng, đậm). TUYỆT ĐỐI KHÔNG GHI 'VĂN PHÒNG ĐẢNG UỶ'.
   - TUYỆT ĐỐI KHÔNG CÓ PHẦN KÍNH GỬI.
   - Không dùng chữ "Tầng 1, Tầng 2" trong văn bản; thay bằng: `1. Thể thức văn bản:`, `2. Nội dung và số liệu chuyên môn:`.
   - Mục `1. Thể thức văn bản:` ghi câu chuẩn: "Văn phòng Đảng uỷ đã rà soát, chỉnh sửa trực tiếp trên dự thảo văn bản các lỗi chính tả, chỉnh sửa thể thức văn bản theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng." (Nếu có nhắc Tờ trình thì nhắc hoàn thiện số hiệu, ngày tháng chính thức).
   - Mục `2. Nội dung và số liệu chuyên môn:`
     + Khẳng định các chỉ tiêu lớn bám sát Nghị quyết Đại hội đại biểu Đảng bộ xã lần thứ I.
     + Trình bày từng lỗi phát hiện dưới dạng gạch đầu dòng (`- `) rõ ràng, sắc bén, không trùng lặp.
   - Mục `III. ĐỀ XUẤT, KIẾN NGHỊ`: Đề xuất Thường trực Đảng uỷ chỉ đạo cơ quan soạn thảo tiếp thu hoàn thiện các nội dung cụ thể nêu tại mục 2; sau đó cho chủ trương gửi phiếu xin ý kiến BTV Đảng uỷ.
   - Thẩm quyền ký: Dòng 1 `K/T CHÁNH VĂN PHÒNG` (đậm), Dòng 2 `PHÓ CHÁNH VĂN PHÒNG` (viết hoa không đậm), họ tên `Ngô Hoàng Việt`.

4. NẾU DỰ THẢO LÀ KẾ HOẠCH (-KH) HOẶC NGHỊ QUYẾT (-NQ):
   - Tự động sinh `cv_lay_y_kien_btv_payload` cho Công văn lấy ý kiến các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ (-CV/ĐU).

CẤU TRÚC JSON ĐẦU RA BẮT BUỘC:
{{
  "thong_tin_du_thao": {{
    "ten_van_ban": "Tên chính xác của văn bản dự thảo",
    "co_quan_soan_thao": "Cơ quan trình (VD: UBND xã, Ban Xây dựng Đảng...)",
    "loai_van_ban": "KH",
    "trich_yeu": "Trích yếu ngắn gọn của dự thảo"
  }},
  "canh_bao_so_lieu": [
    {{
      "muc_van_ban": "Mục II.2",
      "so_lieu_goc": "Số liệu hoặc nội dung gốc trong dự thảo",
      "van_de": "Chỉ ra chính xác sai sót so với chuẩn",
      "de_xuat_hoi": "Đề xuất chỉnh sửa cụ thể"
    }}
  ],
  "bc_tham_dinh_payload": {{
    "doc_type": "BC",
    "so_hieu": "Số      -BC/VPĐU",
    "co_quan_cap_tren": "ĐẢNG UỶ XÃ CÔNG HẢI",
    "co_quan_ban_hanh": "VĂN PHÒNG",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "ten_loai": "BÁO CÁO",
    "trich_yeu": "kết quả thẩm định dự thảo [Tên văn bản] do [Cơ quan trình] trình",
    "noi_dung": [
      "Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I và phân công của Thường trực Đảng uỷ, Văn phòng Đảng uỷ tiến hành thẩm định hồ sơ dự thảo [Tên văn bản] do [Cơ quan trình] trình. Kết quả thẩm định cụ thể như sau:",
      "I. TỔNG QUAN HỒ SƠ THẨM ĐỊNH",
      "- Cơ quan trình: [Tên cơ quan trình].",
      "- Tên văn bản dự thảo: [Tên văn bản dự thảo].",
      "- Thành phần hồ sơ gửi kèm: Tờ trình của [Tên cơ quan trình]; dự thảo [Tên văn bản].",
      "II. KẾT QUẢ THẨM ĐỊNH",
      "1. **Thể thức văn bản:** Văn phòng Đảng uỷ đã rà soát, chỉnh sửa trực tiếp trên dự thảo văn bản các lỗi chính tả, chỉnh sửa thể thức văn bản theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng. Lưu ý cơ quan soạn thảo bổ sung số hiệu và ngày ban hành chính thức của Tờ trình kèm theo.",
      "2. **Nội dung và số liệu chuyên môn:** Các mục tiêu, chỉ tiêu kinh tế - xã hội chủ yếu trong dự thảo (tăng trưởng 11-12%/năm, thu ngân sách tăng 12%/năm, đến năm 2030 không còn hộ nghèo...) hoàn toàn thống nhất và bám sát Nghị quyết Đại hội đại biểu Đảng bộ xã Công Hải lần thứ I, nhiệm kỳ 2025 - 2030. Tuy nhiên, qua đối soát nhận thấy một số nội dung nghiệp vụ cần lưu ý, hoàn thiện sau đây:",
      "- [Nội dung phát hiện thứ nhất]",
      "- [Nội dung phát hiện thứ hai]",
      "III. ĐỀ XUẤT, KIẾN NGHỊ",
      "Trên cơ sở kết quả thẩm định, Văn phòng Đảng uỷ kính trình Thường trực Đảng uỷ:",
      "1. Đối với thể thức: Dự thảo văn bản đã được Văn phòng Đảng uỷ trực tiếp chuẩn hóa theo đúng Hướng dẫn số 05-HD/VPTW.",
      "2. Đối với nội dung và số liệu chuyên môn: Đề nghị Thường trực Đảng uỷ chỉ đạo [Cơ quan trình] tiếp thu, hoàn thiện các nội dung cụ thể nêu tại mục 2 phần II trước khi ban hành chính thức.",
      "3. Về điều kiện trình: Sau khi [Cơ quan trình] hoàn thiện các nội dung trên, kính trình Thường trực Đảng uỷ xem xét cho chủ trương gửi phiếu xin ý kiến Ban Thường vụ Đảng uỷ theo Quy chế làm việc."
    ],
    "noi_nhan": [
      "- Thường trực Đảng uỷ (b/c);",
      "- Ban Thường vụ Đảng uỷ;",
      "- [Cơ quan trình];",
      "- Lưu VPĐU."
    ],
    "tham_quyen": "K/T CHÁNH VĂN PHÒNG",
    "chuc_vu": "PHÓ CHÁNH VĂN PHÒNG",
    "nguoi_ky": "Ngô Hoàng Việt"
  }},
  "cv_lay_y_kien_btv_payload": {{
    "doc_type": "CV",
    "so_hieu": "Số      -CV/ĐU",
    "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
    "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "ten_loai": "CÔNG VĂN",
    "trich_yeu": "V/v tham gia ý kiến vào dự thảo [Tên văn bản]",
    "kinh_gui": [
      "Các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ xã."
    ],
    "noi_dung": [
      "Thực hiện Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã khoá I, Ban Thường vụ Đảng uỷ gửi đến các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ dự thảo: [Tên văn bản].",
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
  }}
}}

LƯU Ý NGHIÊM NGẶT:
- "trich_yeu" của bc_tham_dinh_payload BẮT BUỘC là: "kết quả thẩm định dự thảo [Tên văn bản] do [Cơ quan trình] trình" (chữ thường).
- Báo cáo thẩm định TUYỆT ĐỐI KHÔNG CÓ KÍNH GỬI.
- Trả về DUY NHẤT một khối JSON hợp lệ.
"""


def get_wf4_messages(draft_doc_text: str, submitting_agency: str = "UBND xã", attached_submission: str = "") -> list:
    """Tạo cấu trúc tin nhắn hoàn chỉnh cho DeepSeek API với Tri thức nền tảng đã qua kiểm chứng."""
    grounding_context = build_appraisal_grounding_context(draft_doc_text, submitting_agency)
    system_text = PROMPT_WF4_THAM_DINH.format(
        system_prompt=MASTER_SYSTEM_PROMPT,
        grounding_context=grounding_context
    )
    
    user_prompt_lines = [
        f"Dưới đây là hồ sơ dự thảo do {submitting_agency} trình:"
    ]
    if attached_submission:
        user_prompt_lines.append(f"\n--- TỜ TRÌNH ĐÍNH KÈM ---\n{attached_submission}\n")

    user_prompt_lines.extend([
        f"\n--------------------- BẮT ĐẦU DỰ THẢO VĂN BẢN ---------------------",
        draft_doc_text,
        f"--------------------- KẾT THÚC DỰ THẢO VĂN BẢN ---------------------",
        f"\nYÊU CẦU BẮT BUỘC:",
        f"Tiến hành thẩm định 2 tầng dựa trên Tri thức nền tảng và xuất DUY NHẤT một khối JSON theo đúng schema.",
        f"TUYỆT ĐỐI KHÔNG để dấu ba chấm '...' trong noi_dung và de_xuat của Báo cáo thẩm định."
    ])
    
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": "\n".join(user_prompt_lines)},
    ]
