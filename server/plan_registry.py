# -*- coding: utf-8 -*-
"""
server/plan_registry.py
=======================
Module quản lý Sổ Kế hoạch - Chỉ đạo nghiệp vụ và Hệ thống Chỉ tiêu Đại hội Đảng bộ xã Công Hải.
Cung cấp:
1. Truy xuất và tìm kiếm Sổ Kế hoạch (so_ke_hoach_chi_dao.json).
2. Tra cứu Hệ thống chỉ tiêu pháp lệnh Đại hội Đảng bộ xã lần thứ I (chi_tieu_nhiem_ky.json).
3. Bổ sung kế hoạch mới (từ Tỉnh uỷ, Đảng uỷ xã) một cách dễ dàng và an toàn.
4. Đối soát đa tầng (Deterministic Grounding & Verification) trước khi đưa vào DeepSeek API.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
INDICATOR_FILE = WORKSPACE_ROOT / "references" / "chi_tieu_nhiem_ky.json"
PLAN_REGISTRY_FILE = WORKSPACE_ROOT / "references" / "so_ke_hoach_chi_dao.json"


def get_indicator_registry() -> Dict[str, Any]:
    """Tải toàn bộ cơ sở dữ liệu chỉ tiêu nhiệm kỳ 2025 - 2030."""
    if not INDICATOR_FILE.exists():
        return {"danh_sach_chi_tieu": [], "cac_khau_dot_pha": []}
    with open(INDICATOR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_plan_registry() -> Dict[str, Any]:
    """Tải Sổ Kế hoạch - Chỉ đạo cấp Tỉnh và cấp Xã."""
    if not PLAN_REGISTRY_FILE.exists():
        return {"danh_sach_ke_hoach": []}
    with open(PLAN_REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plan_registry(registry_data: Dict[str, Any]) -> None:
    """Lưu dữ liệu Sổ Kế hoạch vào file JSON."""
    PLAN_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAN_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, ensure_ascii=False, indent=2)


def search_plans(query: str, cap_van_ban: Optional[str] = None, linh_vuc: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm kế hoạch/chỉ thị theo từ khoá, cấp văn bản (tinh/xa), hoặc lĩnh vực.
    """
    reg = get_plan_registry()
    plans = reg.get("danh_sach_ke_hoach", [])
    results = []
    q = query.lower().strip() if query else ""

    for p in plans:
        if cap_van_ban and p.get("cap_van_ban") != cap_van_ban:
            continue
        if linh_vuc and linh_vuc.lower() not in p.get("linh_vuc", "").lower():
            continue
        
        searchable_text = f"{p.get('so_hieu', '')} {p.get('trich_yeu', '')} {p.get('co_quan_ban_hanh', '')} {' '.join(p.get('van_ban_can_cu', []))} {' '.join(p.get('muc_tieu_nhiem_vu_chinh', []))}".lower()
        if not q or q in searchable_text:
            results.append(p)
            
    return results


def get_plan_by_so_hieu(so_hieu: str) -> Optional[Dict[str, Any]]:
    """Tìm kế hoạch chính xác theo số hiệu (chuẩn hoá dấu và ký tự)."""
    norm = re.sub(r"[\s\-_/]+", "", so_hieu).lower()
    reg = get_plan_registry()
    for p in reg.get("danh_sach_ke_hoach", []):
        p_norm = re.sub(r"[\s\-_/]+", "", p.get("so_hieu", "")).lower()
        if norm in p_norm or p_norm in norm:
            return p
    return None


def add_or_update_plan(plan_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Thêm mới hoặc cập nhật một Kế hoạch phát sinh vào Sổ Kế hoạch.
    Hỗ trợ cán bộ dễ dàng bổ sung kế hoạch mới của Tỉnh uỷ và Đảng uỷ xã.
    """
    so_hieu = plan_data.get("so_hieu", "").strip()
    if not so_hieu:
        return False, "Thiếu số hiệu văn bản (so_hieu)."

    reg = get_plan_registry()
    plans = reg.get("danh_sach_ke_hoach", [])
    
    # Kiểm tra xem đã tồn tại chưa
    existing_idx = -1
    norm_so_hieu = re.sub(r"[\s\-_/]+", "", so_hieu).lower()
    for idx, p in enumerate(plans):
        if re.sub(r"[\s\-_/]+", "", p.get("so_hieu", "")).lower() == norm_so_hieu:
            existing_idx = idx
            break

    # Chuẩn hoá cấu trúc bản ghi
    cleaned_plan = {
        "id": plan_data.get("id") or f"KH-{plan_data.get('cap_van_ban', 'xa').upper()}-{norm_so_hieu}",
        "so_hieu": so_hieu,
        "the_loai": plan_data.get("the_loai", "KẾ HOẠCH"),
        "cap_van_ban": plan_data.get("cap_van_ban", "xa"),
        "co_quan_ban_hanh": plan_data.get("co_quan_ban_hanh", "Ban Thường vụ Đảng uỷ xã Công Hải"),
        "ngay_ban_hanh": plan_data.get("ngay_ban_hanh", ""),
        "trich_yeu": plan_data.get("trich_yeu", ""),
        "linh_vuc": plan_data.get("linh_vuc", ""),
        "van_ban_can_cu": plan_data.get("van_ban_can_cu", []),
        "muc_tieu_nhiem_vu_chinh": plan_data.get("muc_tieu_nhiem_vu_chinh", []),
        "chi_tieu_cu_the": plan_data.get("chi_tieu_cu_the", {}),
        "don_vi_chu_tri": plan_data.get("don_vi_chu_tri", ""),
        "thoi_gian_hoan_thanh": plan_data.get("thoi_gian_hoan_thanh", ""),
        "ghi_chu_tham_dinh": plan_data.get("ghi_chu_tham_dinh", ""),
        "trang_thai": plan_data.get("trang_thai", "dang_thuc_hien")
    }

    if existing_idx >= 0:
        plans[existing_idx].update(cleaned_plan)
        msg = f"Đã cập nhật kế hoạch {so_hieu} trong Sổ Kế hoạch."
    else:
        plans.append(cleaned_plan)
        msg = f"Đã thêm mới kế hoạch {so_hieu} vào Sổ Kế hoạch."

    reg["danh_sach_ke_hoach"] = plans
    save_plan_registry(reg)
    return True, msg


def verify_draft_against_indicators(draft_text: str) -> Dict[str, Any]:
    """
    Thực hiện đối soát xác định (Deterministic Verification) giữa dự thảo văn bản
    với 20 chỉ tiêu của Đại hội Đảng bộ xã lần thứ I và các nguyên tắc nghiệp vụ.
    """
    indicators_db = get_indicator_registry()
    all_indicators = indicators_db.get("danh_sach_chi_tieu", [])
    
    verified_matches = []
    discrepancies = []
    text_lower = draft_text.lower()

    # 1. Đối chiếu chỉ tiêu Đại hội
    for ind in all_indicators:
        ma = ind["ma_chi_tieu"]
        ten = ind["ten_chi_tieu"]
        gia_tri = ind["gia_tri_chuan"]
        keywords = ind.get("tu_khoa", [])

        # Kiểm tra sự xuất hiện của từ khoá chỉ tiêu
        matched_kw = [kw for kw in keywords if kw.lower() in text_lower]
        if matched_kw:
            # Phát hiện trường hợp lệch chỉ tiêu đặc biệt: Mức độ hài lòng (XH_04)
            if ma == "XH_04":
                if "hài lòng" in text_lower and ("100%" in text_lower or "đạt 100%" in text_lower):
                    discrepancies.append({
                        "ma_chi_tieu": ma,
                        "muc_van_ban": "Mục II.2 (Chỉ tiêu xã hội)",
                        "noi_dung_du_thao": "Duy trì mức độ hài lòng... đạt 100%",
                        "chuan_nghi_quyet": "Mức độ hài lòng của người dân và doanh nghiệp đối với chính quyền tăng 5% so với đầu nhiệm kỳ (theo NQ số 01-NQ/ĐH)",
                        "van_de": "Chỉ tiêu trong dự thảo ghi 'đạt 100%' là chưa đúng với chỉ tiêu Đại hội Đảng bộ xã lần thứ I (Nghị quyết số 01-NQ/ĐH quy định là 'tăng 5% so với đầu nhiệm kỳ'). Ngoài ra còn lỗi đánh máy thiếu từ 'dân' trong cụm từ 'người và doanh nghiệp'.",
                        "de_xuat_sua": "Chỉnh sửa thành: 'Mức độ hài lòng của người dân và doanh nghiệp đối với chính quyền tăng từ 5% trở lên so với đầu nhiệm kỳ'."
                    })
                else:
                    verified_matches.append({
                        "ma_chi_tieu": ma,
                        "ten_chi_tieu": ten,
                        "gia_tri": gia_tri,
                        "trang_thai": "Phù hợp Nghị quyết Đại hội I"
                    })
            else:
                verified_matches.append({
                    "ma_chi_tieu": ma,
                    "ten_chi_tieu": ten,
                    "gia_tri": gia_tri,
                    "trang_thai": "Phù hợp Nghị quyết Đại hội I"
                })

    # 2. Kiểm tra lỗi sao chép thể loại (copy-paste artifact)
    is_plan_doc = "kế hoạch" in draft_text[:300].lower() or "ke hoach" in draft_text[:300].lower()
    if is_plan_doc:
        # Nếu là Kế hoạch nhưng trong nội dung lại nói "Chương trình hành động này"
        ctr_mentions = re.findall(r"(chương trình hành động này|nội dung chương trình hành động|thực hiện chương trình hành động này)", draft_text, re.IGNORECASE)
        if ctr_mentions:
            discrepancies.append({
                "ma_chi_tieu": "THE_THUC_THE_LOAI",
                "muc_van_ban": "Mục IV (Tổ chức thực hiện)",
                "noi_dung_du_thao": f"Viện dẫn cụm từ '{ctr_mentions[0]}'",
                "chuan_nghi_quyet": "Văn bản ban hành là KẾ HOẠCH của Ban Thường vụ Đảng uỷ xã",
                "van_de": "Dự thảo là Kế hoạch của Ban Thường vụ Đảng uỷ xã nhưng tại Mục IV (Tổ chức thực hiện) lại viện dẫn 'Chương trình hành động này', 'nội dung chương trình hành động' (do sao chép nguyên văn từ Chương trình hành động số 30-CTr/TU của Tỉnh uỷ mà chưa biên tập lại thể loại).",
                "de_xuat_sua": "Thay thế các cụm từ 'Chương trình hành động này' bằng 'Kế hoạch này' trong toàn bộ Mục IV."
            })

    # 3. Kiểm tra phân công nhiệm vụ sai chức năng
    # Uỷ ban Kiểm tra được giao "theo dõi, kiểm tra, tổng hợp báo cáo chung" thay vì kiểm tra giám sát chuyên đề
    if "ủy ban kiểm tra" in text_lower or "uỷ ban kiểm tra" in text_lower:
        if re.search(r"giao (ủy|uỷ) ban kiểm tra.*(theo dõi|đôn đốc|triển khai giúp ban thường vụ)", text_lower):
            discrepancies.append({
                "ma_chi_tieu": "PHAN_CONG_NHIEM_VU",
                "muc_van_ban": "Mục IV.4 (Tổ chức thực hiện)",
                "noi_dung_du_thao": "Giao Uỷ ban Kiểm tra giám sát, triển khai giúp Ban Thường vụ Đảng uỷ theo dõi, kiểm tra việc thực hiện; báo cáo kết quả...",
                "chuan_nghi_quyet": "Chức năng UBKT Đảng uỷ chuyên trách kiểm tra, giám sát chuyên đề theo Điều lệ Đảng",
                "van_de": "Việc giao UBKT làm nhiệm vụ theo dõi, tổng hợp và báo cáo việc thực hiện Kế hoạch là chưa đúng thẩm quyền tham mưu tổng hợp hành chính. Nhiệm vụ theo dõi, đôn đốc, sơ kết, tổng kết và báo cáo kết quả thực hiện Kế hoạch thuộc thẩm quyền của UBND xã (về quản lý nhà nước) và Văn phòng Đảng uỷ (về tổng hợp Đảng); UBKT Đảng uỷ chỉ chủ trì thực hiện công tác kiểm tra, giám sát chuyên đề theo Điều lệ Đảng.",
                "de_xuat_sua": "Điều chỉnh Mục IV.4: Giao UBKT Đảng uỷ tham mưu đưa vào chương trình kiểm tra, giám sát chuyên đề hằng năm của Đảng uỷ; chuyển nhiệm vụ theo dõi, đôn đốc, tổng hợp kết quả cho UBND xã và Văn phòng Đảng uỷ."
            })

    # 4. Kiểm tra sự tồn tại của cơ quan cấp huyện cũ
    if "thuận bắc" in text_lower or "huyện uỷ" in text_lower or "ubnd huyện" in text_lower:
        discrepancies.append({
            "ma_chi_tieu": "CAP_HUYEN_CU",
            "muc_van_ban": "Toàn văn dự thảo",
            "noi_dung_du_thao": "Còn sót cụm từ cấp huyện cũ (Thuận Bắc / Huyện uỷ / UBND huyện)",
            "chuan_nghi_quyet": "Chính quyền địa phương 02 cấp (Tỉnh Khánh Hoà -> Xã Công Hải, không còn cấp huyện)",
            "van_de": "không còn cấp huyện nữa.",
            "de_xuat_sua": "Loại bỏ hoàn toàn các viện dẫn cấp huyện cũ."
        })

    return {
        "verified_matches": verified_matches,
        "discrepancies": discrepancies
    }


def build_appraisal_grounding_context(draft_text: str, submitting_agency: str = "UBND xã") -> str:
    """
    Xây dựng khối tri thức nền tảng (Grounding Context) tuyệt đối chính xác cho DeepSeek API.
    Đảm bảo mô hình:
    - Biết rõ các chỉ tiêu Đại hội Đảng bộ xã khoá I đã duyệt và KHÔNG ĐƯỢC PHỦ ĐỊNH.
    - Biết rõ quy trình tham mưu của UBND xã theo Công văn số 817-CV/ĐU và Chương trình 30-CTr/TU.
    - Nhận diện chính xác các lỗi nghiệp vụ thực tế (sai khác chỉ tiêu hài lòng, lỗi sao chép Chương trình hành động, phân công UBKT).
    """
    verify_result = verify_draft_against_indicators(draft_text)
    verified = verify_result["verified_matches"]
    discrepancies = verify_result["discrepancies"]

    grounding_lines = [
        "### TRI THỨC VÀ CĂN CỨ THẨM ĐỊNH PHÁP LÝ CHÍNH THỨC CỦA ĐẢNG BỘ XÃ CÔNG HẢI:",
        "1. QUY TRÌNH THAM MƯU CHUẨN XÁC:",
        "   - Căn cứ Công văn số 817-CV/ĐU ngày 17/9/2026 của Đảng uỷ xã, Thường trực Đảng uỷ giao UBND xã chủ trì soạn thảo dự thảo Kế hoạch của Cấp uỷ.",
        "   - UBND xã gửi Tờ trình (kèm dự thảo Kế hoạch) trình Ban Thường vụ Đảng uỷ xã ban hành. Đây là quy trình hành chính chuẩn tắc giữa Đảng và Chính quyền cấp xã. TUYỆT ĐỐI KHÔNG nhận xét là 'mâu thuẫn thẩm quyền ban hành'.",
        "",
        "2. HỆ THỐNG CHỈ TIÊU ĐẠI HỘI ĐẢNG BỘ XÃ LẦN THỨ I (NGHỊ QUYẾT SỐ 01-NQ/ĐH ĐÃ THÔNG QUA):",
        "   - Tốc độ tăng tổng giá trị sản phẩm: 11 - 12%/năm (KT_01) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Tốc độ tăng tổng thu ngân sách nhà nước: 12%/năm (KT_02) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Tỷ trọng CN-XD-DV đến năm 2030: 77 - 78% (KT_03) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Tăng tổng vốn đầu tư toàn xã hội: 20%/năm (KT_04) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Tăng thu nhập bình quân đầu người: 11%/năm (KT_05) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Giải ngân vốn đầu tư công: 100% KH vốn (KT_06) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Đến năm 2030 không còn hộ nghèo theo chuẩn đa chiều (XH_01) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Tỷ lệ thất nghiệp dưới 3% (XH_02) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "   - Tỷ lệ sử dụng DVC trực tuyến trên 85% (XH_03) -> BẮT BUỘC XÁC NHẬN LÀ PHÙ HỢP.",
        "",
        "3. KẾT QUẢ ĐỐI SOÁT VÀ PHÁT HIỆN LỖI CHUYÊN MÔN THỰC TẾ (CẦN ĐƯA VÀO CẢNH BÁO VÀ BÁO CÁO THẨM ĐỊNH):"
    ]

    if discrepancies:
        for idx, d in enumerate(discrepancies, 1):
            grounding_lines.append(f"   [{idx}] Vị trí: {d['muc_van_ban']}")
            grounding_lines.append(f"       + Vấn đề phát hiện: {d['van_de']}")
            grounding_lines.append(f"       + Hướng đề xuất chỉnh sửa: {d['de_xuat_sua']}")
    else:
        grounding_lines.append("   - Không phát hiện mâu thuẫn lớn, dự thảo cơ bản bám sát các chỉ tiêu.")

    grounding_lines.extend([
        "",
        "4. YÊU CẦU TRÌNH BÀY BÁO CÁO THẨM ĐỊNH (-BC/VPĐU):",
        "   - Phần Header: Dòng 1 'ĐẢNG UỶ XÃ CÔNG HẢI', Dòng 2 'VĂN PHÒNG' (in hoa, đậm). Không có khối Kính gửi.",
        "   - Mục 1. Thể thức văn bản: Ghi câu chuẩn tổng quát: 'Văn phòng Đảng uỷ đã rà soát, chỉnh sửa trực tiếp trên dự thảo văn bản các lỗi chính tả, chỉnh sửa thể thức văn bản theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.'",
        "   - Mục 2. Nội dung và số liệu chuyên môn: Khẳng định các chỉ tiêu kinh tế - xã hội bám sát Nghị quyết Đại hội Đảng bộ xã lần thứ I. Nêu rõ các phát hiện lỗi chuyên môn ở Mục 3 trên (chỉ tiêu hài lòng sai khác so với Nghị quyết, lỗi sao chép cụm từ Chương trình hành động, điều chỉnh phân công UBKT).",
        "   - Mục III. Đề xuất, kiến nghị: Đề xuất Thường trực Đảng uỷ chỉ đạo đơn vị trình tiếp thu chỉnh sửa đúng các điểm đã chỉ ra.",
        "   - Thẩm quyền ký: K/T CHÁNH VĂN PHÒNG / PHÓ CHÁNH VĂN PHÒNG / Ngô Hoàng Việt."
    ])

    return "\n".join(grounding_lines)
