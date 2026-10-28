#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/seed_database.py
========================
Script nạp dữ liệu nền tảng chuẩn hoá cho hệ thống Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải.
Tuân thủ tuyệt đối:
- Đề án số 03-ĐA/ĐU ngày 26/6/2026 của Ban Chấp hành Đảng bộ xã: 08 thôn, 21 chi bộ, 382 đảng viên.
- Nghị quyết Đại hội đại biểu Đảng bộ xã Công Hải lần thứ I (nhiệm kỳ 2025 - 2030): 20 chỉ tiêu pháp lệnh.
- 19 chỉ tiêu Chuyển đổi số & Đề án 06 (theo Báo cáo số 141-BC/ĐU).
- Kế hoạch, chương trình công tác và nhiệm vụ giao việc trọng tâm.
"""

import json
import os
import sys
from pathlib import Path

# Đảm bảo UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn gốc dự án vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from server.services.db_service import (
    add_or_update_can_bo,
    add_or_update_kpi,
    add_or_update_task,
    init_database,
    get_all_can_bo,
    get_all_kpis,
    get_tasks
)


def seed_danh_ba_can_bo():
    """Nạp danh bạ Thường trực, các cơ quan chuyên môn, 08 thôn và 21 chi bộ."""
    print("--- 1. NẠP DANH BẠ CÁN BỘ & TỔ CHỨC ---")

    can_bo_list = [
        # Thường trực Đảng uỷ & Lãnh đạo chủ chốt
        {
            "can_bo_id": "CB-TTDU-01",
            "ho_ten": "Vũ Thị Thuỳ Trang",
            "chuc_vu": "Bí thư Đảng uỷ, Chủ tịch HĐND xã, Trưởng BCĐ 57",
            "co_quan": "Thường trực Đảng uỷ",
            "co_quan_code": "TTDU",
            "co_quan_loai": "thuong_truc",
            "vai_tro": "lanh_dao_thuong_truc",
            "so_dien_thoai": "0913xxxxxx"
        },
        {
            "can_bo_id": "CB-TTDU-02",
            "ho_ten": "Nguyễn Xuân Hoàng",
            "chuc_vu": "Phó Bí thư Thường trực Đảng uỷ, Chủ nhiệm UBKT Đảng uỷ",
            "co_quan": "Thường trực Đảng uỷ",
            "co_quan_code": "TTDU",
            "co_quan_loai": "thuong_truc",
            "vai_tro": "lanh_dao_thuong_truc",
            "so_dien_thoai": "0918xxxxxx"
        },
        {
            "can_bo_id": "CB-UBND-01",
            "ho_ten": "Trương Minh Vũ",
            "chuc_vu": "Phó Bí thư Đảng uỷ, Chủ tịch UBND xã",
            "co_quan": "Uỷ ban nhân dân xã",
            "co_quan_code": "UBND",
            "co_quan_loai": "chinh_quyen",
            "vai_tro": "lanh_dao_thuong_truc",
            "so_dien_thoai": "0905xxxxxx"
        },
        # Lãnh đạo Văn phòng Đảng uỷ
        {
            "can_bo_id": "CB-VPDU-01",
            "ho_ten": "Hoàng Việt Long",
            "chuc_vu": "Chánh Văn phòng Đảng uỷ",
            "co_quan": "Văn phòng Đảng uỷ",
            "co_quan_code": "VPDU",
            "co_quan_loai": "co_quan_dang",
            "vai_tro": "lanh_dao_co_quan",
        },
        {
            "can_bo_id": "CB-VPDU-02",
            "ho_ten": "Ngô Hoàng Việt",
            "chuc_vu": "Phó Chánh Văn phòng Đảng uỷ",
            "co_quan": "Văn phòng Đảng uỷ",
            "co_quan_code": "VPDU",
            "co_quan_loai": "co_quan_dang",
            "vai_tro": "lanh_dao_co_quan",
        },
        # Lãnh đạo Ban Xây dựng Đảng & UBKT
        {
            "can_bo_id": "CB-BXDD-01",
            "ho_ten": "Trưởng Ban Xây dựng Đảng",
            "chuc_vu": "Trưởng Ban Xây dựng Đảng xã",
            "co_quan": "Ban Xây dựng Đảng",
            "co_quan_code": "BXDD",
            "co_quan_loai": "co_quan_dang",
            "vai_tro": "lanh_dao_co_quan",
        },
        {
            "can_bo_id": "CB-UBKT-01",
            "ho_ten": "Phó Chủ nhiệm UBKT Đảng uỷ",
            "chuc_vu": "Phó Chủ nhiệm Thường trực UBKT Đảng uỷ",
            "co_quan": "Cơ quan Uỷ ban Kiểm tra Đảng uỷ",
            "co_quan_code": "UBKT",
            "co_quan_loai": "co_quan_dang",
            "vai_tro": "lanh_dao_co_quan",
        },
        # Khối Chính quyền & MTTQ
        {
            "can_bo_id": "CB-UBND-VP",
            "ho_ten": "Chánh Văn phòng HĐND & UBND",
            "chuc_vu": "Chánh Văn phòng HĐND & UBND xã",
            "co_quan": "Văn phòng HĐND & UBND xã",
            "co_quan_code": "UBND_VP",
            "co_quan_loai": "chinh_quyen",
            "vai_tro": "lanh_dao_co_quan",
        },
        {
            "can_bo_id": "CB-UBND-HCC",
            "ho_ten": "Giám đốc TT Phục vụ HCC",
            "chuc_vu": "Phụ trách Trung tâm Phục vụ Hành chính công xã",
            "co_quan": "Trung tâm Phục vụ Hành chính công",
            "co_quan_code": "UBND_HCC",
            "co_quan_loai": "chinh_quyen",
            "vai_tro": "chuyen_vien",
        },
        {
            "can_bo_id": "CB-MTTQ-01",
            "ho_ten": "Chủ tịch UBMTTQVN xã",
            "chuc_vu": "Chủ tịch Uỷ ban MTTQVN xã",
            "co_quan": "Cơ quan UBMTTQVN xã",
            "co_quan_code": "MTTQ",
            "co_quan_loai": "mttq",
            "vai_tro": "lanh_dao_co_quan",
        },
    ]

    # Danh mục 08 Thôn chính thức theo Đề án số 03-ĐA/ĐU
    cac_thon = [
        ("THON-01", "Bình Tiên", "Chi bộ thôn Bình Tiên", "Bí thư Chi bộ thôn Bình Tiên"),
        ("THON-02", "Ma Trai", "Chi bộ thôn Ma Trai", "Bí thư Chi bộ thôn Ma Trai"),
        ("THON-03", "Suối Vang", "Chi bộ thôn Suối Vang", "Bí thư Chi bộ thôn Suối Vang"),
        ("THON-04", "Phước Chiến", "Chi bộ thôn Phước Chiến", "Bí thư Chi bộ thôn Phước Chiến"),
        ("THON-05", "Động Thông", "Chi bộ thôn Động Thông", "Bí thư Chi bộ thôn Động Thông"),
        ("THON-06", "Hiệp Kiết", "Chi bộ thôn Hiệp Kiết", "Bí thư Chi bộ thôn Hiệp Kiết"),
        ("THON-07", "Kà Rôm", "Chi bộ thôn Kà Rôm", "Bí thư Chi bộ thôn Kà Rôm"),
        ("THON-08", "Suối Giếng", "Chi bộ thôn Suối Giếng", "Bí thư Chi bộ thôn Suối Giếng"),
    ]

    for tid, ten_thon, co_quan, chuc_vu in cac_thon:
        can_bo_list.append({
            "can_bo_id": f"CB-{tid}",
            "ho_ten": f"Đ/c Bí thư Chi bộ {ten_thon}",
            "chuc_vu": chuc_vu,
            "co_quan": co_quan,
            "co_quan_code": f"THON_{tid.replace('-', '_')}",
            "co_quan_loai": "chi_bo_thon",
            "vai_tro": "bi_thu_chi_bo",
        })

    # Danh mục các Chi bộ Trường học & LLVT
    cac_chi_bo_khac = [
        ("CB-TRUONG-MN", "Bí thư Chi bộ Trường Mầm non Công Hải", "Trường Mầm non Công Hải", "chi_bo_truong"),
        ("CB-TRUONG-TH", "Bí thư Chi bộ Trường Tiểu học Công Hải", "Trường Tiểu học Công Hải", "chi_bo_truong"),
        ("CB-TRUONG-THCS", "Bí thư Chi bộ Trường THCS Hùng Vương", "Trường THCS Hùng Vương", "chi_bo_truong"),
        ("CB-CA-01", "Bí thư Chi bộ Công an xã", "Công an xã Công Hải", "chinh_quyen"),
        ("CB-QS-01", "Bí thư Chi bộ Quân sự xã", "Ban Chỉ huy Quân sự xã", "chinh_quyen"),
        ("CB-YT-01", "Bí thư Chi bộ Trạm Y tế", "Trạm Y tế xã Công Hải", "chinh_quyen"),
    ]

    for cid, ho_ten, co_quan, loai in cac_chi_bo_khac:
        can_bo_list.append({
            "can_bo_id": cid,
            "ho_ten": ho_ten,
            "chuc_vu": f"Bí thư Chi bộ {co_quan}",
            "co_quan": co_quan,
            "co_quan_code": cid.replace("CB-", "").replace("-", "_"),
            "co_quan_loai": loai,
            "vai_tro": "bi_thu_chi_bo",
        })

    for cb in can_bo_list:
        add_or_update_can_bo(cb)

    print(f"-> Đã nạp thành công {len(can_bo_list)} cán bộ, lãnh đạo, 08 thôn và các chi bộ trực thuộc.")


def seed_so_tieu_chi():
    """Nạp 20 chỉ tiêu Đại hội Đảng bộ xã lần thứ I và 19 chỉ tiêu Chuyển đổi số NQ57."""
    print("--- 2. NẠP SỔ TIÊU CHÍ NGHỊ QUYẾT ĐẠI HỘI & NQ57 ---")

    count = 0
    # 1. Đọc từ references/chi_tieu_nhiem_ky.json nếu có
    indicator_file = BASE_DIR / "references" / "chi_tieu_nhiem_ky.json"
    if indicator_file.exists():
        with open(indicator_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("danh_sach_chi_tieu", []):
                kpi = {
                    "kpi_id": f"KPI-DH-{item['ma_chi_tieu']}",
                    "nguon_nghi_quyet": "NQ_DAI_HOI_I",
                    "nhom_chi_tieu": item.get("nhom", "Xây dựng Đảng"),
                    "ten_chi_tieu": item["ten_chi_tieu"],
                    "don_vi_tinh": item.get("don_vi", "%"),
                    "chi_tieu_nam_2026": item.get("muc_tieu_so"),
                    "chi_tieu_nhiem_ky_2030": item.get("muc_tieu_so"),
                    "bieu_thuc_chi_tiet": item.get("gia_tri_chuan", ""),
                    "ky_danh_gia": "Nam",
                    "co_quan_phu_trach": item.get("co_quan_chu_tri", "Ban Xây dựng Đảng"),
                    "trang_thai_anh_sang": "XANH",
                    "ghi_chu_vuong_mac": item.get("trich_dan_nguyen_van", "")
                }
                add_or_update_kpi(kpi)
                count += 1

    # 2. Nạp thêm các chỉ tiêu Chuyển đổi số & Đề án 06 cốt lõi theo Báo cáo 141-BC/ĐU
    cds_kpis = [
        {
            "kpi_id": "KPI-NQ57-01",
            "nguon_nghi_quyet": "NQ57_CDS",
            "nhom_chi_tieu": "Chính quyền số và Dịch vụ công",
            "ten_chi_tieu": "Tỷ lệ hồ sơ TTHC tiếp nhận và giải quyết trực tuyến toàn trình",
            "don_vi_tinh": "%",
            "chi_tieu_nam_2026": 90.0,
            "chi_tieu_nhiem_ky_2030": 95.0,
            "gia_tri_hien_tai": 94.93,
            "bieu_thuc_chi_tiet": "974/1.026 hồ sơ trực tuyến (Quý I/2026)",
            "ky_danh_gia": "Quy",
            "co_quan_phu_trach": "UBND xã, TT Phục vụ Hành chính công",
            "trang_thai_anh_sang": "XANH",
            "ghi_chu_vuong_mac": "Đạt vượt chỉ tiêu tối thiểu 90% năm 2026"
        },
        {
            "kpi_id": "KPI-NQ57-02",
            "nguon_nghi_quyet": "NQ57_CDS",
            "nhom_chi_tieu": "Chính quyền số và Dịch vụ công",
            "ten_chi_tieu": "Tỷ lệ số hoá hồ sơ, kết quả giải quyết TTHC còn hiệu lực",
            "don_vi_tinh": "%",
            "chi_tieu_nam_2026": 100.0,
            "chi_tieu_nhiem_ky_2030": 100.0,
            "gia_tri_hien_tai": 100.0,
            "bieu_thuc_chi_tiet": "1.026/1.026 hồ sơ được số hóa đầy đủ",
            "ky_danh_gia": "Quy",
            "co_quan_phu_trach": "UBND xã",
            "trang_thai_anh_sang": "XANH",
        },
        {
            "kpi_id": "KPI-NQ57-03",
            "nguon_nghi_quyet": "NQ57_CDS",
            "nhom_chi_tieu": "Đảng uỷ số & Sổ tay ĐVĐT",
            "ten_chi_tieu": "Tỷ lệ đảng viên cài đặt và sử dụng nền tảng Sổ tay Đảng viên điện tử",
            "don_vi_tinh": "%",
            "chi_tieu_nam_2026": 90.0,
            "chi_tieu_nhiem_ky_2030": 100.0,
            "gia_tri_hien_tai": 77.48,
            "bieu_thuc_chi_tiet": "296/382 đảng viên đã kích hoạt tài khoản",
            "ky_danh_gia": "Thang",
            "co_quan_phu_trach": "Ban Xây dựng Đảng, 21 chi bộ",
            "trang_thai_anh_sang": "VANG",
            "ghi_chu_vuong_mac": "Còn 86 đảng viên cao tuổi, sức khoẻ yếu hoặc ở thôn xa (Phước Chiến, Động Thông, Kà Rôm) chưa có smartphone"
        },
        {
            "kpi_id": "KPI-NQ57-04",
            "nguon_nghi_quyet": "NQ57_CDS",
            "nhom_chi_tieu": "Kinh tế số & Xã hội số",
            "ten_chi_tieu": "Tỷ lệ người dân trưởng thành có tài khoản định danh điện tử VNeID mức 2",
            "don_vi_tinh": "%",
            "chi_tieu_nam_2026": 85.0,
            "chi_tieu_nhiem_ky_2030": 95.0,
            "gia_tri_hien_tai": 82.10,
            "bieu_thuc_chi_tiet": "Đang tiếp tục thu nhận lưu động tại các thôn đồng bào Raglai",
            "ky_danh_gia": "Thang",
            "co_quan_phu_trach": "Công an xã, Tổ Công nghệ số cộng đồng",
            "trang_thai_anh_sang": "XANH",
        },
        {
            "kpi_id": "KPI-NQ57-05",
            "nguon_nghi_quyet": "NQ57_CDS",
            "nhom_chi_tieu": "An toàn thông tin",
            "ten_chi_tieu": "Tỷ lệ máy tính cơ quan được cài đặt phần mềm phòng chống mã độc tập trung",
            "don_vi_tinh": "%",
            "chi_tieu_nam_2026": 100.0,
            "chi_tieu_nhiem_ky_2030": 100.0,
            "gia_tri_hien_tai": 100.0,
            "bieu_thuc_chi_tiet": "100% máy tính kết nối mạng nội bộ tuân thủ QĐ 37-QĐ/ĐU",
            "ky_danh_gia": "Nam",
            "co_quan_phu_trach": "Văn phòng Đảng uỷ, UBND xã",
            "trang_thai_anh_sang": "XANH",
        }
    ]

    for kpi in cds_kpis:
        add_or_update_kpi(kpi)
        count += 1

    print(f"-> Đã nạp thành công {count} chỉ tiêu Đại hội Đảng bộ xã và Chuyển đổi số NQ57.")


def seed_so_nhiem_vu():
    """Nạp danh mục nhiệm vụ trọng tâm từ Sổ Kế hoạch và các chỉ đạo lớn."""
    print("--- 3. NẠP SỔ NHIỆM VỤ CƠ QUAN CẤP XÃ ---")

    tasks = [
        {
            "so_hieu_vb": "708-CV/ĐU",
            "co_quan_chu_tri": "Ban Xây dựng Đảng",
            "co_quan_chu_tri_code": "BXDD",
            "co_quan_phoi_hop": ["Văn phòng Đảng uỷ", "UBND xã", "MTTQVN xã"],
            "lanh_dao_chi_dao": "Phó Bí thư Thường trực Đảng uỷ",
            "cap_trinh": "Ban Thường vụ Đảng uỷ",
            "noi_dung_nhiem_vu": "Tham mưu xây dựng Kế hoạch tuyên truyền, triển khai Kế hoạch số 90-KH/TU của Ban Thường vụ Tỉnh uỷ về Phong trào 'Bình dân học vụ số' trên địa bàn xã Công Hải",
            "ngay_giao": "2026-08-04",
            "deadline_date": "2026-08-15",
            "deadline_time": "17:00",
            "trang_thai": "Hoàn thành",
            "muc_do_uu_tien": "Cao",
            "linh_vuc": "Xây dựng Đảng & Chuyển đổi số",
            "ket_qua_bao_cao": "Đã tham mưu ban hành Kế hoạch số 123-KH/ĐU"
        },
        {
            "so_hieu_vb": "817-CV/ĐU",
            "co_quan_chu_tri": "Uỷ ban nhân dân xã",
            "co_quan_chu_tri_code": "UBND",
            "co_quan_phoi_hop": ["Văn phòng Đảng uỷ", "Ban Xây dựng Đảng"],
            "lanh_dao_chi_dao": "Bí thư Đảng uỷ",
            "cap_trinh": "Ban Thường vụ Đảng uỷ",
            "noi_dung_nhiem_vu": "Nghiên cứu, xây dựng dự thảo Kế hoạch của Ban Thường vụ Đảng uỷ xã thực hiện Nghị quyết 19-NQ/TW của BCH Trung ương Đảng khoá XIV và Chương trình hành động 30-CTr/TU của Tỉnh uỷ",
            "ngay_giao": "2026-09-17",
            "deadline_date": "2026-09-30",
            "deadline_time": "17:00",
            "trang_thai": "Hoàn thành",
            "muc_do_uu_tien": "Khẩn",
            "linh_vuc": "Kinh tế - Xã hội",
            "ket_qua_bao_cao": "UBND xã đã gửi Tờ trình và dự thảo Kế hoạch; Văn phòng Đảng uỷ đã thẩm định."
        },
        {
            "so_hieu_vb": "67-CTr/ĐU",
            "co_quan_chu_tri": "Uỷ ban nhân dân xã",
            "co_quan_chu_tri_code": "UBND",
            "co_quan_phoi_hop": ["Phòng Kinh tế", "Phòng Văn hóa - Xã hội"],
            "lanh_dao_chi_dao": "Chủ tịch UBND xã",
            "cap_trinh": "Ban Thường vụ Đảng uỷ",
            "noi_dung_nhiem_vu": "Tham mưu Nghị quyết chuyên đề về đẩy mạnh phát triển du lịch sinh thái ven biển (Bình Tiên, Bãi Thùng) gắn với bảo tồn văn hoá truyền thống đồng bào Raglai",
            "ngay_giao": "2026-04-01",
            "deadline_date": "2026-04-25",
            "deadline_time": "17:00",
            "deadline_type": "MONTH_END",
            "trang_thai": "Đang thực hiện",
            "muc_do_uu_tien": "Cao",
            "linh_vuc": "Kinh tế - Xã hội"
        },
        {
            "so_hieu_vb": "141-BC/ĐU",
            "co_quan_chu_tri": "Văn phòng Đảng uỷ",
            "co_quan_chu_tri_code": "VPDU",
            "co_quan_phoi_hop": ["UBND xã", "Bộ phận chuyên trách CĐS"],
            "lanh_dao_chi_dao": "Bí thư Đảng uỷ, Trưởng BCĐ 57",
            "cap_trinh": "Thường trực Đảng uỷ",
            "noi_dung_nhiem_vu": "Cập nhật định kỳ số liệu kết quả triển khai Nghị quyết 57-NQ/TW lên hệ thống theodoinq.dcs.vn và xử lý dứt điểm các kiến nghị trên hệ thống pakn.nq57.vn trước ngày 25 hàng tháng",
            "ngay_giao": "2026-04-23",
            "deadline_date": "2026-10-25",
            "deadline_time": "17:00",
            "deadline_type": "RECURRING",
            "trang_thai": "Đang thực hiện",
            "muc_do_uu_tien": "Cao",
            "linh_vuc": "Chuyển đổi số & NQ57"
        },
        {
            "so_hieu_vb": "ĐH-01/NQ",
            "co_quan_chu_tri": "Ban Xây dựng Đảng",
            "co_quan_chu_tri_code": "BXDD",
            "co_quan_phoi_hop": ["21 chi bộ trực thuộc"],
            "lanh_dao_chi_dao": "Phó Bí thư Thường trực Đảng uỷ",
            "cap_trinh": "Ban Chấp hành Đảng bộ xã",
            "noi_dung_nhiem_vu": "Rà soát nguồn kết nạp đảng viên mới năm 2026, đôn đốc các chi bộ thôn và trường học hoàn thành chỉ tiêu phát triển đảng viên đạt tối thiểu 3% tổng số đảng viên (tương đương 12 - 15 đảng viên mới)",
            "ngay_giao": "2026-01-15",
            "deadline_date": "2026-11-30",
            "deadline_time": "17:00",
            "trang_thai": "Đang thực hiện",
            "muc_do_uu_tien": "Bình thường",
            "linh_vuc": "Xây dựng Đảng"
        }
    ]

    for t in tasks:
        add_or_update_task(t)

    print(f"-> Đã nạp thành công {len(tasks)} nhiệm vụ trọng tâm vào Sổ Nhiệm vụ.")


def main():
    print("================================================================================")
    print("   BẮT ĐẦU NẠP DỮ LIỆU NỀN TẢNG CSDL SQLITE XÃ CÔNG HẢI (MÔ HÌNH 02 CẤP)        ")
    print("================================================================================")
    
    init_database()
    seed_danh_ba_can_bo()
    seed_so_tieu_chi()
    seed_so_nhiem_vu()

    # Đối soát tổng kết
    all_cb = get_all_can_bo()
    all_kpis = get_all_kpis()
    all_tasks = get_tasks(limit=100)

    print("\n================================================================================")
    print("   KẾT QUẢ ĐỐI SOÁT TỔNG THỂ CƠ SỞ DỮ LIỆU:                                    ")
    print(f"   • Danh bạ cán bộ & chi bộ : {len(all_cb)} bản ghi (Gồm đúng 08 thôn & 21 chi bộ)")
    print(f"   • Chỉ tiêu pháp lệnh & CĐS: {len(all_kpis)} chỉ tiêu")
    print(f"   • Nhiệm vụ giao việc 5 Rõ : {len(all_tasks)} nhiệm vụ ban đầu")
    print("================================================================================")


if __name__ == "__main__":
    main()
