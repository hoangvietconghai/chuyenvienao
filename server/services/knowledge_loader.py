# -*- coding: utf-8 -*-
"""
server/services/knowledge_loader.py
====================================
Bộ nạp Tri thức & Kỹ năng Chọn lọc cho DeepSeek (Context & Skill Injection).
Giúp DeepSeek am hiểu sâu sắc dự án Văn phòng Đảng uỷ xã Công Hải như Antigravity,
đồng thời tối ưu hoá lượng token (chỉ nạp đúng tri thức cần thiết theo từng nghiệp vụ).
"""

from pathlib import Path
from typing import Dict, Optional

from server.config import BASE_DIR
from server.logger import get_logger

logger = get_logger("knowledge_loader")

# Thư mục chứa skills và references
SKILLS_DIR = BASE_DIR / ".agents" / "skills"
REFERENCES_DIR = BASE_DIR / "references"

# Bộ nhớ đệm cache để không phải đọc đĩa nhiều lần
_SKILL_CACHE: Dict[str, str] = {}
_LOCAL_KNOWLEDGE_CACHE: Optional[str] = None


def get_core_rules() -> str:
    """Quy chuẩn cốt lõi bắt buộc của Đảng bộ xã Công Hải (rút trích từ AGENTS.md)."""
    return """=== QUY CHUẨN NỀN TẢNG BẮT BUỘC (VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI) ===
1. MÔ HÌNH CHÍNH QUYỀN 02 CẤP (từ 01/7/2025):
   - Cấp tỉnh (Tỉnh uỷ Khánh Hoà, UBND tỉnh Khánh Hoà) -> Cấp xã (Đảng uỷ xã Công Hải, UBND xã Công Hải).
   - HOÀN TOÀN KHÔNG CÒN CẤP HUYỆN. Khi phát hiện cấp huyện, chỉ ghi ngắn gọn: "không còn cấp huyện nữa" (sai sót đánh máy).
   - Đảng bộ xã Công Hải là Đảng bộ cơ sở trực thuộc Tỉnh uỷ Khánh Hoà.
2. LÃNH ĐẠO CẤP UỶ & CÁN BỘ PHỤ TRÁCH:
   - Bí thư Đảng uỷ: đồng chí Vũ Thị Thuỳ Trang.
   - Phó Bí thư Đảng uỷ: đồng chí Nguyễn Xuân Hoàng.
   - Phó Chánh Văn phòng Đảng uỷ (phụ trách Văn phòng): đồng chí Ngô Hoàng Việt.
   - Cán bộ BTV Tỉnh uỷ phụ trách địa bàn xã: đồng chí Lương Đức Hải (Uỷ viên BTV Tỉnh uỷ Khánh Hoà).
3. 5 CƠ QUAN CHUYÊN MÔN CẤP XÃ:
   - Uỷ ban nhân dân xã; Ban Xây dựng Đảng; Uỷ ban Kiểm tra Đảng uỷ; Cơ quan UBMTTQVN xã; Văn phòng Đảng uỷ.
4. ĐƠN VỊ HÀNH CHÍNH (08 THÔN CHÍNH THỨC):
   - Gồm: Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng.
5. CHÍNH TẢ KHỐI ĐẢNG & NGÀY THÁNG:
   - Đặt dấu chuẩn: "oà", "uỷ", "uý" (Đảng uỷ, Khánh Hoà, Ban Thường vụ, Uỷ ban).
   - Ngày tháng trong nội dung: ghi dạng số "dd/mm/yyyy", tuyệt đối không ghi chữ "ngày... tháng... năm...".
6. THỂ THỨC VĂN BẢN (HƯỚNG DẪN SỐ 05-HD/VPTW):
   - Căn lề: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm.
   - Spacing & Giãn dòng: Before 6pt, After 6pt, Line spacing Exactly 18pt, Font Times New Roman 14.
   - Thụt đầu dòng: Tất cả đoạn văn, mục lớn, tiểu mục, gạch đầu dòng (-) hoặc cộng (+) đều thụt đúng 1cm (10mm).
   - In đậm chỉ mục: Số/chữ chỉ mục VÀ tiêu đề (trước dấu hai chấm) in đậm đồng bộ. Sau dấu hai chấm in thường. Tuyệt đối không in đậm gạch (-) hoặc cộng (+).
7. NGUYÊN TẮC AN TOÀN & TIẾT KIỆM:
   - Không hỏi, lưu mật khẩu; không nhập thông tin Bí mật Nhà nước.
   - AI hỗ trợ - Con người quyết định (mọi văn bản là dự thảo tham mưu, cán bộ tự tay duyệt/ký).
   - Tiết kiệm token: Tuyệt đối không in lại toàn văn văn bản vào chat khi đã xuất Word. Chỉ tóm tắt phân công, lưu ý nghiệp vụ và gửi link tải.
"""


def get_local_knowledge_summary() -> str:
    """Tóm tắt tri thức & số liệu địa phương chính thống từ references/tong_quan_xa_cong_hai.md."""
    global _LOCAL_KNOWLEDGE_CACHE
    if _LOCAL_KNOWLEDGE_CACHE:
        return _LOCAL_KNOWLEDGE_CACHE

    _LOCAL_KNOWLEDGE_CACHE = """=== TRI THỨC & SỐ LIỆU ĐỊA PHƯƠNG CHÍNH THỐNG XÃ CÔNG HẢI ===
(Cập nhật theo references/tong_quan_xa_cong_hai.md ngày 14/10/2026)
- Diện tích tự nhiên: 124,19 km² (12.419,00 ha); tỷ lệ che phủ rừng đạt 69,17% (hơn 8.590 ha). Chiều dài bờ biển: 4,7 km (vịnh Bình Tiên, Bãi Thùng, Bãi Nước Ngọt, Bãi Chuối).
- Dân số & Dân tộc: Dân số thường trú 14.972 người (tổng quy mô kể cả tạm trú: 15.110 người); gồm đồng bào dân tộc thiểu số chiếm 78,5% (chủ yếu dân tộc Raglai, tập trung tại các thôn Phước Chiến, Động Thông, Ma Trai) và người Kinh chiếm 21,5%. Cơ sở tôn giáo: Chùa Long Cát (thôn Hiệp Kiết) và Nhà thờ Tin lành Báp Tít Hy Vọng (thôn Kà Rôm).
- Tổ chức Đảng & Bộ máy: Từ 30/9/2026 có 23 chi bộ trực thuộc Đảng uỷ xã (không còn 02 Đảng bộ bộ phận), tổng 382 đảng viên; 08 thôn mới (Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng); biên chế 72 cán bộ, công chức (Khối Đảng-MTTQ: 31, Chính quyền: 41).
- Thủy văn & Công trình trọng điểm: Hồ chứa nước Sông Trâu (800 ha mặt nước, tưới 3.000 ha, an ninh nguồn nước toàn xã); Hồ Ma Trai, Hồ Ba Chi.
- MỤC TIÊU ĐẠI HỘI ĐẢNG BỘ XÃ LẦN THỨ I (NHIỆM KỲ 2025 - 2030):
  + Tốc độ tăng trưởng tổng giá trị sản phẩm: 11 - 12%/năm.
  + Thu ngân sách nhà nước trên địa bàn: tăng bình quân 12%/năm.
  + Xây dựng Nông thôn mới: Đạt chuẩn "Xã Nông thôn mới nâng cao".
  + Giảm nghèo: Đến năm 2030 KHÔNG CÒN HỘ NGHÈO (tuyệt đối không đặt nghi vấn chỉ tiêu này).
  + Cơ cấu kinh tế đến 2030: Công nghiệp - xây dựng - dịch vụ chiếm 77 - 78%.
- TRỤ CỘT KINH TẾ:
  1. Du lịch sinh thái, nghỉ dưỡng cao cấp ven biển (Bình Tiên, Bãi Thùng - 439 ha) và du lịch văn hoá bản địa Raglai.
  2. Năng lượng tái tạo (tổ hợp quy hoạch 758 MW: 108 MW đang vận hành, 650 MW quy hoạch mới).
  3. Khai thác, chế biến khoáng sản đá xây dựng chất lượng cao (núi Giác Lan, Cô Lô, Tây Kà Rôm).
  4. Nông nghiệp ứng dụng công nghệ cao thích ứng biến đổi khí hậu (cây ăn quả chịu hạn: điều, xoài, mít, mãng cầu).
- CHUYỂN ĐỔI SỐ & ĐỀ ÁN 06 (BAN CHỈ ĐẠO 57):
  + Trung tâm Phục vụ Hành chính công xã đặt tại Nhà Văn hoá thôn Ba Hồ (cũ) thuộc thôn Kà Rôm.
  + Triển khai 100% dịch vụ công trực tuyến toàn trình, làm sạch và chuẩn hoá dữ liệu đảng viên và dân cư.
"""
    return _LOCAL_KNOWLEDGE_CACHE


def get_skill_instruction(doc_type_or_wf: str) -> str:
    """Nạp nội dung kỹ năng chuẩn mực tương ứng với thể loại văn bản cần xử lý."""
    mapping = {
        "CV": "cong-van",
        "KH": "ke-hoach",
        "BC": "bao-cao",
        "BC_THANG": "bao-cao-thang",
        "bao_cao_thang": "bao-cao-thang",
        "TB": "thong-bao",
        "KL": "ket-luan",
        "QD": "quyet-dinh",
        "NQ": "nghi-quyet",
        "TTR": "to-trinh",
        "CT": "chi-thi",
        "CTR": "chi-thi",
        "wf1_tong_hop_bao_cao": "bao-cao",
        "wf2_thong_bao_ket_luan": "thong-bao",
        "wf3_giao_viec": "cong-van",
        "wf4_tham_dinh": "tham-dinh-van-ban",
        "cds": "tham-muu-chuyen-doi-so",
    }

    key = doc_type_or_wf.upper() if doc_type_or_wf.startswith("wf") is False else doc_type_or_wf
    skill_folder = mapping.get(key, mapping.get(doc_type_or_wf, "cong-van"))

    if skill_folder in _SKILL_CACHE:
        return _SKILL_CACHE[skill_folder]

    skill_file = SKILLS_DIR / skill_folder / "SKILL.md"
    if skill_file.exists():
        try:
            content = skill_file.read_text(encoding="utf-8")
            # Trích phần hướng dẫn nghiệp vụ chính (bỏ qua frontmatter)
            parts = content.split("---", 2)
            main_content = parts[2].strip() if len(parts) >= 3 else content
            # Giới hạn an toàn khoảng 3.500 từ (~4.500 tokens) cho skill cụ thể
            cleaned = "\n".join(line for line in main_content.splitlines() if not line.startswith("<!--"))[:15000]
            _SKILL_CACHE[skill_folder] = f"=== HƯỚNG DẪN NGHIỆP VỤ CHUYÊN SÂU: {skill_folder.upper()} ===\n{cleaned}"
            return _SKILL_CACHE[skill_folder]
        except Exception as ex:
            logger.warning(f"Lỗi đọc skill '{skill_folder}': {ex}")

    return ""


def build_system_knowledge_prompt(doc_type_or_wf: str = "CV", include_local: bool = True) -> str:
    """
    Hàm tổng hợp tri thức cần thiết:
    - Lớp 1: Quy chuẩn cốt lõi bắt buộc (Core Rules)
    - Lớp 2: Tri thức số liệu địa phương xã Công Hải (Local Knowledge)
    - Lớp 3: Kỹ năng chuyên sâu của đúng thể loại văn bản (Target Skill)
    Tổng dung lượng: Chỉ ~ 4.000 - 8.000 tokens, đảm bảo DeepSeek hiểu cặn kẽ và phản hồi chuẩn xác.
    """
    sections = [get_core_rules()]

    if include_local:
        sections.append(get_local_knowledge_summary())

    skill_inst = get_skill_instruction(doc_type_or_wf)
    if skill_inst:
        sections.append(skill_inst)

    return "\n\n".join(sections)
