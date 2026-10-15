# -*- coding: utf-8 -*-
"""
Script xuất Bảng phân công nhiệm vụ Tổ hỗ trợ CNTT & Chuyển đổi số Đảng uỷ xã Công Hải
Triển khai chuẩn hoá dữ liệu Đảng viên trên Sổ tay đảng viên điện tử cho 08 thôn và 03 trường học.
"""

import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def create_phan_cong_excel(output_path):
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # STYLES ĐỊNH NGHĨA CHUNG
    # -------------------------------------------------------------
    font_title = Font(name="Times New Roman", size=15, bold=True, color="8B0000") # Đỏ đô
    font_subtitle = Font(name="Times New Roman", size=11, italic=True)
    font_header_sub = Font(name="Times New Roman", size=11, bold=True)
    
    font_table_header = Font(name="Times New Roman", size=11, bold=True, color="FFFFFF")
    font_group_header = Font(name="Times New Roman", size=11, bold=True, color="8B0000")
    
    font_data = Font(name="Times New Roman", size=11)
    font_data_bold = Font(name="Times New Roman", size=11, bold=True)
    font_data_italic = Font(name="Times New Roman", size=11, italic=True)
    
    fill_header = PatternFill(fill_type="solid", start_color="8B0000", end_color="8B0000")
    fill_group = PatternFill(fill_type="solid", start_color="F5EBE6", end_color="F5EBE6")
    fill_zebra = PatternFill(fill_type="solid", start_color="FDFBF7", end_color="FDFBF7")
    fill_highlight = PatternFill(fill_type="solid", start_color="FFF2CC", end_color="FFF2CC")
    
    thin_border_side = Side(border_style="thin", color="D3D3D3")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)

    # =============================================================
    # SHEET 1: PHÂN CÔNG 11 CHI BỘ (8 THÔN & 3 TRƯỜNG HỌC)
    # =============================================================
    ws1 = wb.active
    ws1.title = "Phan_cong_11_Chi_bo"
    ws1.views.sheetView[0].showGridLines = True
    
    # Header khối cấp uỷ
    ws1["A1"] = "ĐẢNG BỘ TỈNH KHÁNH HOÀ"
    ws1["A1"].font = Font(name="Times New Roman", size=10, bold=True)
    ws1["A2"] = "ĐẢNG UỶ XÃ CÔNG HẢI"
    ws1["A2"].font = Font(name="Times New Roman", size=10, bold=True)
    ws1["A3"] = "TỔ HỖ TRỢ CNTT & CĐS"
    ws1["A3"].font = Font(name="Times New Roman", size=10, bold=True, color="8B0000")
    
    ws1["G1"] = "ĐẢNG CỘNG SẢN VIỆT NAM"
    ws1["G1"].font = Font(name="Times New Roman", size=10, bold=True)
    ws1["G2"] = "Công Hải, ngày 16 tháng 10 năm 2026"
    ws1["G2"].font = Font(name="Times New Roman", size=10, italic=True)
    
    # Tiêu đề bảng
    ws1.merge_cells("A5:J5")
    ws1["A5"] = "BẢNG PHÂN CÔNG NHIỆM VỤ HỖ TRỢ CHUẨN HOÁ DỮ LIỆU ĐẢNG VIÊN"
    ws1["A5"].font = font_title
    ws1["A5"].alignment = align_center
    
    ws1.merge_cells("A6:J6")
    ws1["A6"] = "TRÊN HỆ THỐNG SỔ TAY ĐẢNG VIÊN ĐIỆN TỬ CHO 08 THÔN VÀ 03 TRƯỜNG HỌC"
    ws1["A6"].font = Font(name="Times New Roman", size=13, bold=True, color="8B0000")
    ws1["A6"].alignment = align_center

    ws1.merge_cells("A7:J7")
    ws1["A7"] = "(Kèm theo Kế hoạch triển khai của Tổ hỗ trợ theo Quyết định số 98-QĐ/ĐU ngày 30/6/2026 của BTV Đảng uỷ xã)"
    ws1["A7"].font = font_subtitle
    ws1["A7"].alignment = align_center

    # Tiêu đề cột
    headers_s1 = [
        "STT", 
        "Nhóm / Cụm", 
        "Chi bộ trực thuộc", 
        "Số ĐV", 
        "Cán bộ Tổ hỗ trợ\nphụ trách chính", 
        "Cán bộ phối hợp\n(Kỹ thuật & Hồ sơ)", 
        "Đầu mối tại Chi bộ\n(Bí thư / Cấp uỷ viên)", 
        "Địa điểm hỗ trợ", 
        "Thời gian\ntriển khai", 
        "Nội dung trọng tâm & Phương thức hỗ trợ"
    ]
    
    row_idx = 9
    for col_idx, h_text in enumerate(headers_s1, 1):
        cell = ws1.cell(row=row_idx, column=col_idx, value=h_text)
        cell.font = font_table_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_cell
    ws1.row_dimensions[row_idx].height = 36

    # Dữ liệu 11 chi bộ chia theo 3 nhóm
    groups_data = [
        {
            "group_name": "TỔ CÔNG TÁC 1: KHỐI 03 TRƯỜNG HỌC (TRIỂN KHAI ĐIỂM - TẬP TRUNG CHUYÊN MÔN)",
            "leader": "Đ/c Lê Châu Huỳnh Đức (Trường chính) | Đ/c Katơr Thị Duyên (Phân hiệu) | Đ/c Trần Thị Bạch Mai",
            "items": [
                (
                    "1", "Trường học", "Chi bộ Trường Mầm non Công Hải", "23",
                    "Đ/c Lê Châu Huỳnh Đức (Trường chính)\nĐ/c Katơr Thị Duyên (phân hiệu)",
                    "Đ/c Lê Thị Bích Thuỷ (VPĐU)\nĐ/c Mai Thị Thuỷ (VPĐU)",
                    "Đ/c Bí thư Chi bộ\nHiệu trưởng nhà trường",
                    "Văn phòng Trường MN\n(Cơ sở thôn Kà Rôm)",
                    "20/10/2026\n(Thứ Ba - 08h00)",
                    "Chuẩn hoá 100% hồ sơ giáo viên; chụp ảnh thẻ chuẩn phông trắng; kích hoạt tính năng gửi tài liệu họp chi bộ số (Trường chính 11.5 ĐV, Phân hiệu 11.5 ĐV)."
                ),
                (
                    "2", "Trường học", "Chi bộ Trường Tiểu học Công Hải", "41",
                    "Đ/c Lê Châu Huỳnh Đức (Trường chính)\nĐ/c Katơr Thị Duyên (phân hiệu)",
                    "Đ/c Lê Thị Bích Thuỷ (VPĐU)\nĐ/c Mai Thị Thuỷ (VPĐU)",
                    "Đ/c Bí thư Chi bộ\nHiệu trưởng nhà trường",
                    "Văn phòng Trường TH\n(Cơ sở thôn Suối Giếng)",
                    "21/10/2026\n(Thứ Tư - 14h00)",
                    "Rà soát dữ liệu sau sáp nhập 2 trường tiểu học cũ theo Đề án 05; đối soát thẻ Đảng và VNeID (Trường chính 20.5 ĐV, Phân hiệu 20.5 ĐV)."
                ),
                (
                    "3", "Trường học", "Chi bộ Trường THCS Hùng Vương", "16",
                    "Đ/c Trần Thị Bạch Mai\n(Chuyên viên Ban XDĐ)",
                    "Đ/c Lê Thị Bích Thuỷ (VPĐU)\nĐ/c Mai Thị Thuỷ (VPĐU)",
                    "Đ/c Bí thư Chi bộ\nHiệu trưởng nhà trường",
                    "Phòng Tin học\nTrường THCS Hùng Vương",
                    "22/10/2026\n(Thứ Năm - 14h00)",
                    "Hoàn tất dữ liệu giáo viên; tập huấn Cấp uỷ chi bộ tạo cuộc họp, biểu quyết và điểm danh tự động trên app."
                ),
            ]
        },
        {
            "group_name": "TỔ CÔNG TÁC 2: KHỐI 05 THÔN ĐỒNG BẰNG, VEN BIỂN & TRUNG TÂM XÃ",
            "leader": "Phụ trách chính theo từng thôn: Đ/c Lê Thị Bích Thuỷ, Đ/c Mai Thị Thuỷ, Đ/c Chamaléa Xoa",
            "items": [
                (
                    "4", "Thôn đồng bằng", "Chi bộ thôn Kà Rôm", "11",
                    "Đ/c Lê Thị Bích Thuỷ\n(Chuyên viên VPĐU)",
                    "Đ/c Sầm Văn Tim (Ban XDĐ)\nĐ/c Katơr Vế (VPĐU)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Kà Rôm",
                    "24/10/2026\n(Thứ Bảy - 08h30)",
                    "Khớp nối dữ liệu đảng viên thôn Ba Hồ cũ sáp nhập vào; cập nhật tài khoản và phân quyền sinh hoạt."
                ),
                (
                    "5", "Thôn đồng bằng", "Chi bộ thôn Suối Vang", "8",
                    "Đ/c Lê Thị Bích Thuỷ\n(Chuyên viên VPĐU)",
                    "Đ/c Sầm Văn Tim (Ban XDĐ)\nĐ/c Katơr Vế (VPĐU)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Suối Vang",
                    "25/10/2026\n(Chủ Nhật - 08h30)",
                    "Quy mô gọn, hỗ trợ tại chỗ từng đảng viên nông nghiệp cài đặt app và xác thực định danh VNeID mức 2."
                ),
                (
                    "6", "Thôn ven biển", "Chi bộ thôn Bình Tiên", "6",
                    "Đ/c Mai Thị Thuỷ\n(Chuyên viên VPĐU)",
                    "Đ/c Sầm Văn Tim (Ban XDĐ)\nĐ/c Katơr Vế (VPĐU)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà sinh hoạt cộng đồng\nthôn Bình Tiên",
                    "26/10/2026\n(Thứ Hai - 14h00)",
                    "Xuống trực tiếp địa bàn ven biển; hỗ trợ đảng viên nuôi lồng bè, làm du lịch kích hoạt tài khoản số."
                ),
                (
                    "7", "Thôn đồng bằng", "Chi bộ thôn Hiệp Kiết", "21",
                    "Đ/c Chamaléa Xoa\n(Uỷ viên UBKT Đảng uỷ)",
                    "Đ/c Sầm Văn Tim (Ban XDĐ)\nĐ/c Katơr Vế (VPĐU)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Hiệp Kiết",
                    "27 - 28/10/2026\n(Thứ 3-4, 18h30 tối)",
                    "Rà soát biến động sau sáp nhập thôn Xóm Đèn; phân công ĐV trẻ kèm ĐV lớn tuổi; tổ chức vào buổi tối."
                ),
                (
                    "8", "Thôn trung tâm", "Chi bộ thôn Suối Giếng", "31",
                    "Đ/c Mai Thị Thuỷ\n(Chuyên viên VPĐU)",
                    "Đ/c Sầm Văn Tim (Ban XDĐ)\nĐ/c Katơr Vế (VPĐU)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Suối Giếng",
                    "29 - 30/10/2026\n(Thứ 5-6, 18h30 tối)",
                    "Khớp nối hồ sơ thôn Giác Lan sáp nhập; chụp ảnh chân dung phông trắng; kích hoạt 100% tài khoản."
                ),
            ]
        },
        {
            "group_name": "TỔ CÔNG TÁC 3: KHỐI 03 THÔN MIỀN NÚI & ĐỒNG BÀO DTTS RAGLAI PHÍA TÂY",
            "leader": "Phụ trách chính theo từng thôn: Đ/c Katơr Vế, Đ/c Ngô Hoàng Việt",
            "items": [
                (
                    "9", "Thôn DTTS", "Chi bộ thôn Ma Trai", "10",
                    "Đ/c Katơr Vế\n(Chuyên viên VPĐU)",
                    "Đ/c Katơr Thị Duyên (Ban XDĐ)\nĐ/c Chamaléa Xoa (UBKT)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Ma Trai",
                    "02/11/2026\n(Thứ Hai - 08h30)",
                    "Hướng dẫn bằng tiếng Raglai + tiếng Việt; chuẩn bị wifi di động; chuẩn hoá ngày tháng sinh theo CCCD mới."
                ),
                (
                    "10", "Thôn DTTS", "Chi bộ thôn Phước Chiến", "30",
                    "Đ/c Katơr Vế\n(Chuyên viên VPĐU)",
                    "Đ/c Katơr Thị Duyên (Ban XDĐ)\nĐ/c Chamaléa Xoa (UBKT)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Phước Chiến",
                    "03 - 04/11/2026\n(Thứ 3-4, 14h00)",
                    "Rà soát dữ liệu sáp nhập Tập Lá và Đầu Suối A; phối hợp Bí thư Chi đoàn thôn hỗ trợ từng đảng viên lớn tuổi."
                ),
                (
                    "11", "Thôn DTTS", "Chi bộ thôn Động Thông", "40",
                    "Đ/c Ngô Hoàng Việt\n(Phó Chánh VP Đảng uỷ)",
                    "Đ/c Katơr Thị Duyên (Ban XDĐ)\nĐ/c Chamaléa Xoa (UBKT)",
                    "Đ/c Bí thư Chi bộ thôn",
                    "Nhà Văn hoá thôn Động Thông",
                    "05 - 06/11/2026\n(Thứ 5-6, cả ngày & tối)",
                    "Chi bộ đông nhất: Lập 2 bàn lưu động (Bàn 1: đối soát hồ sơ sáp nhập Đầu Suối B; Bàn 2: chụp ảnh, cài app)."
                ),
            ]
        }
    ]

    for g in groups_data:
        row_idx += 1
        ws1.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=10)
        group_cell = ws1.cell(row=row_idx, column=1, value=f"{g['group_name']} — [{g['leader']}]")
        group_cell.font = font_group_header
        group_cell.fill = fill_group
        group_cell.alignment = align_left
        ws1.row_dimensions[row_idx].height = 26
        for c in range(1, 11):
            ws1.cell(row=row_idx, column=c).border = border_cell

        for item in g["items"]:
            row_idx += 1
            ws1.row_dimensions[row_idx].height = 42
            is_zebra = (int(item[0]) % 2 == 0)
            row_fill = fill_zebra if is_zebra else None
            
            for col_idx, val in enumerate(item, 1):
                c_cell = ws1.cell(row=row_idx, column=col_idx, value=val)
                c_cell.font = font_data
                c_cell.border = border_cell
                if row_fill:
                    c_cell.fill = row_fill
                
                # Căn lề riêng từng cột
                if col_idx in [1, 2, 4, 9]:
                    c_cell.alignment = align_center
                elif col_idx == 3:
                    c_cell.alignment = align_left
                    c_cell.font = font_data_bold
                else:
                    c_cell.alignment = align_left

    # Hàng tổng cộng
    row_idx += 1
    ws1.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=3)
    sum_label = ws1.cell(row=row_idx, column=1, value="TỔNG CỘNG 11 CHI BỘ MỤC TIÊU")
    sum_label.font = font_data_bold
    sum_label.alignment = align_center
    sum_label.fill = fill_highlight
    
    sum_val = ws1.cell(row=row_idx, column=4, value="237 ĐV")
    sum_val.font = font_data_bold
    sum_val.alignment = align_center
    sum_val.fill = fill_highlight

    ws1.merge_cells(start_row=row_idx, start_column=5, end_row=row_idx, end_column=10)
    sum_note = ws1.cell(row=row_idx, column=5, value="Phấn đấu 100% đảng viên trong danh sách được rà soát, cài đặt và sử dụng thành thạo Sổ tay ĐVĐT trước 10/11/2026")
    sum_note.font = font_data_italic
    sum_note.alignment = align_left
    sum_note.fill = fill_highlight

    for c in range(1, 11):
        ws1.cell(row=row_idx, column=c).border = border_cell
    ws1.row_dimensions[row_idx].height = 28

    # Chữ ký chân trang
    row_idx += 3
    ws1.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=4)
    ws1.cell(row=row_idx, column=2, value="TM. TỔ CÔNG TÁC\nTỔ PHÓ").font = font_data_bold
    ws1.cell(row=row_idx, column=2).alignment = align_center

    ws1.merge_cells(start_row=row_idx, start_column=7, end_row=row_idx, end_column=10)
    ws1.cell(row=row_idx, column=7, value="TM. TỔ CÔNG TÁC\nTỔ TRƯỞNG").font = font_data_bold
    ws1.cell(row=row_idx, column=7).alignment = align_center

    row_idx += 5
    ws1.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=4)
    ws1.cell(row=row_idx, column=2, value="Sầm Văn Tim").font = font_data_bold
    ws1.cell(row=row_idx, column=2).alignment = align_center

    ws1.merge_cells(start_row=row_idx, start_column=7, end_row=row_idx, end_column=10)
    ws1.cell(row=row_idx, column=7, value="Ngô Hoàng Việt").font = font_data_bold
    ws1.cell(row=row_idx, column=7).alignment = align_center

    # Độ rộng các cột Sheet 1
    col_widths_s1 = [6, 16, 32, 10, 24, 25, 22, 25, 18, 38]
    for i, w in enumerate(col_widths_s1, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # Cố định header
    ws1.freeze_panes = "A10"


    # =============================================================
    # SHEET 2: TỔNG HỢP NHÂN SỰ & TRÁCH NHIỆM (9 THÀNH VIÊN)
    # =============================================================
    ws2 = wb.create_sheet(title="Nhan_su_To_ho_tro")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A2:G2")
    ws2["A2"] = "DANH SÁCH 09 THÀNH VIÊN TỔ HỖ TRỢ & PHÂN CÔNG NHIỆM VỤ CỤ THỂ"
    ws2["A2"].font = font_title
    ws2["A2"].alignment = align_center

    ws2.merge_cells("A3:G3")
    ws2["A3"] = "(Thành lập theo Quyết định số 98-QĐ/ĐU ngày 30/6/2026 của Ban Thường vụ Đảng uỷ xã)"
    ws2["A3"].font = font_subtitle
    ws2["A3"].alignment = align_center

    headers_s2 = [
        "STT", 
        "Họ và tên", 
        "Chức vụ công tác hiện nay", 
        "Chức danh trong Tổ", 
        "Nhóm công tác", 
        "Địa bàn chi bộ được giao phụ trách", 
        "Trách nhiệm chuyên môn chính"
    ]
    
    r2 = 5
    for c_idx, h_text in enumerate(headers_s2, 1):
        cell = ws2.cell(row=r2, column=c_idx, value=h_text)
        cell.font = font_table_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_cell
    ws2.row_dimensions[r2].height = 30

    members = [
        (
            1, "Ngô Hoàng Việt", "Phó Chánh Văn phòng Đảng uỷ", "Tổ trưởng", 
            "Chỉ đạo chung", "Toàn diện 11 chi bộ mục tiêu; trực tiếp tăng cường Tổ 3 (Ma Trai, Phước Chiến, Động Thông)",
            "Chịu trách nhiệm chung trước BTV Đảng uỷ về tiến độ và kết quả; điều hành nhân lực, phương tiện, wifi di động; báo cáo định kỳ Thường trực Đảng uỷ."
        ),
        (
            2, "Sầm Văn Tim", "ĐUV, Phó Trưởng ban Xây dựng Đảng", "Tổ phó", 
            "Trưởng Tổ 2", "05 thôn: Kà Rôm, Suối Vang, Bình Tiên, Hiệp Kiết, Suối Giếng",
            "Chịu trách nhiệm thẩm định tính chuẩn xác của dữ liệu đảng tịch, xử lý các vướng mắc hồ sơ lý lịch gốc sau sáp nhập thôn."
        ),
        (
            3, "Chamaléa Xoa", "Uỷ viên UBKT Đảng uỷ", "Tổ viên", 
            "Trưởng Tổ 3", "03 thôn miền núi DTTS: Ma Trai, Phước Chiến, Động Thông",
            "Giám sát tiến độ, trực tiếp tuyên truyền, giải thích nghiệp vụ bằng ngôn ngữ Raglai; kiểm soát bảo mật thông tin tài khoản đảng viên."
        ),
        (
            4, "Katơr Vế", "Chuyên viên Văn phòng Đảng uỷ", "Tổ viên", 
            "Tổ 2", "Phối hợp Tổ 2 (Kà Rôm, Suối Vang, Bình Tiên, Hiệp Kiết, Suối Giếng)",
            "Hỗ trợ kỹ thuật phần cứng, cài đặt ứng dụng trên điện thoại thông minh, xử lý lỗi đăng nhập, hướng dẫn đảng viên thao tác."
        ),
        (
            5, "Lê Thị Bích Thuỷ", "Chuyên viên Văn phòng Đảng uỷ", "Tổ viên", 
            "Tổ 1", "03 chi bộ Trường học: MN Công Hải, TH Công Hải, THCS Hùng Vương",
            "Đối soát hồ sơ lý lịch đảng viên ngành giáo dục, cập nhật trình độ chuyên môn, lý luận chính trị, chức vụ chính quyền."
        ),
        (
            6, "Mai Thị Thuỷ", "Chuyên viên Văn phòng Đảng uỷ", "Tổ viên", 
            "Tổ 1", "03 chi bộ Trường học: MN Công Hải, TH Công Hải, THCS Hùng Vương",
            "Chụp và chuẩn hoá ảnh đại diện phông trắng; kích hoạt tài khoản; hướng dẫn cấp uỷ trường học lập lịch sinh hoạt chi bộ số."
        ),
        (
            7, "Trần Thị Bạch Mai", "Chuyên viên Ban Xây dựng Đảng", "Tổ viên", 
            "Tổ 2", "05 thôn: Kà Rôm, Suối Vang, Bình Tiên, Hiệp Kiết, Suối Giếng",
            "Quản lý sổ theo dõi đảng viên, rà soát trùng lặp thông tin, chuẩn hoá ngày vào Đảng, ngày chính thức, số thẻ Đảng viên."
        ),
        (
            8, "Katơr Thị Duyên", "Chuyên viên Ban Xây dựng Đảng", "Tổ viên", 
            "Tổ 3", "03 thôn miền núi DTTS: Ma Trai, Phước Chiến, Động Thông",
            "Rà soát đối chiếu hồ sơ đảng viên người DTTS Raglai; hỗ trợ phiên âm, chuẩn hoá họ tên và số định danh CCCD."
        ),
        (
            9, "Lê Châu Huỳnh Đức", "Chuyên viên VP HĐND - UBND xã", "Tổ viên", 
            "Trưởng Tổ 1", "03 chi bộ Trường học & Hỗ trợ kỹ thuật mạng toàn xã",
            "Chuyên gia kỹ thuật hệ thống; bảo đảm hạ tầng mạng, liên thông tài khoản VNeID mức 2; tập huấn phần mềm quản trị cho cấp uỷ."
        ),
    ]

    for m in members:
        r2 += 1
        ws2.row_dimensions[r2].height = 38
        is_zebra = (m[0] % 2 == 0)
        row_fill = fill_zebra if is_zebra else None
        
        for c_idx, val in enumerate(m, 1):
            cell = ws2.cell(row=r2, column=c_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            if row_fill:
                cell.fill = row_fill
            
            if c_idx in [1, 4]:
                cell.alignment = align_center
            elif c_idx == 2:
                cell.alignment = align_left
                cell.font = font_data_bold
            elif c_idx == 3:
                cell.alignment = align_left
            elif c_idx == 5:
                cell.alignment = align_center
                cell.font = font_data_bold
            else:
                cell.alignment = align_left

    col_widths_s2 = [6, 22, 28, 16, 16, 32, 42]
    for i, w in enumerate(col_widths_s2, 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    ws2.freeze_panes = "A6"


    # =============================================================
    # SHEET 3: CHECKLIST QUY TRÌNH 5 BƯỚC THỰC HIỆN TẠI THỰC ĐỊA
    # =============================================================
    ws3 = wb.create_sheet(title="Checklist_Quy_trinh_5_Buoc")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A2:F2")
    ws3["A2"] = "QUY TRÌNH 05 BƯỚC CHUẨN HOÁ DỮ LIỆU ĐẢNG VIÊN TẠI THỰC ĐỊA"
    ws3["A2"].font = font_title
    ws3["A2"].alignment = align_center

    ws3.merge_cells("A3:F3")
    ws3["A3"] = "(Tổ công tác áp dụng thống nhất cho 100% đảng viên tại 08 thôn và 03 trường học)"
    ws3["A3"].font = font_subtitle
    ws3["A3"].alignment = align_center

    headers_s3 = [
        "Bước", 
        "Tên bước thực hiện", 
        "Nội dung thao tác chi tiết", 
        "Yêu cầu kỹ thuật & Chuẩn mực", 
        "Đơn vị/Người phụ trách", 
        "Tiêu chí nghiệm thu hoàn thành"
    ]

    r3 = 5
    for c_idx, h_text in enumerate(headers_s3, 1):
        cell = ws3.cell(row=r3, column=c_idx, value=h_text)
        cell.font = font_table_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_cell
    ws3.row_dimensions[r3].height = 28

    steps = [
        (
            "Bước 1", "Đối soát thông tin định danh cá nhân",
            "Thu thập số CCCD, số điện thoại chính chủ, mã định danh điện tử của đảng viên. Đối soát với dữ liệu VNeID mức 2.",
            "Trùng khớp 100% họ tên, ngày tháng năm sinh, số CCCD giữa hồ sơ Đảng và dữ liệu dân cư.",
            "Cán bộ kỹ thuật + Đảng viên",
            "Đã cập nhật đúng số CCCD và SĐT chính chủ trên hệ thống"
        ),
        (
            "Bước 2", "Chuẩn hoá dữ liệu đảng tịch & Hồ sơ gốc",
            "Đối chiếu ngày kết nạp, ngày chính thức, số thẻ đảng viên, chức vụ hiện tại, nơi sinh hoạt đảng chuyển đến (sau sáp nhập thôn/trường).",
            "Khớp với Sổ đảng viên lưu tại Ban Xây dựng Đảng và Nghị quyết kết nạp của cấp uỷ.",
            "Cán bộ Ban Xây dựng Đảng + Bí thư Chi bộ",
            "100% trường thông tin đảng tịch không bị bỏ trống hoặc sai lệch"
        ),
        (
            "Bước 3", "Chuẩn hoá ảnh chân dung số",
            "Chụp ảnh chân dung đảng viên tại chỗ bằng điện thoại/máy ảnh hoặc lấy từ file ảnh thẻ có sẵn.",
            "Ảnh phông nền trắng, trang phục lịch sự (áo sơ mi/áo dài/veston), rõ mặt, không đeo kính râm, dung lượng dưới 2MB.",
            "Cán bộ Văn phòng Đảng uỷ phụ trách",
            "Hồ sơ điện tử có ảnh đại diện đúng quy chuẩn trang nghiêm của Đảng"
        ),
        (
            "Bước 4", "Cài đặt ứng dụng & Kích hoạt tài khoản",
            "Hướng dẫn tải app 'Sổ tay đảng viên điện tử' từ App Store / Google Play; đăng nhập bằng tài khoản được cấp và hướng dẫn đổi mật khẩu.",
            "Bảo đảm đảng viên tự nhớ mật khẩu hoặc ghi nhớ an toàn; hướng dẫn thao tác đọc tin, nhận thông báo họp.",
            "Cán bộ Kỹ thuật + Đoàn viên hỗ trợ",
            "Đảng viên đăng nhập thành công và thực hiện được thao tác xem tin tức"
        ),
        (
            "Bước 5", "Thiết lập cơ chế '1 kèm 1' & Nghiệm thu",
            "Đối với đảng viên cao tuổi, đảng viên DTTS ít dùng smartphone: Phân công 01 đảng viên trẻ hoặc Bí thư Chi đoàn thôn thường xuyên kèm cặp hỗ trợ khi họp chi bộ.",
            "Có danh sách phân công cụ thể; bàn giao danh sách nghiệm thu có chữ ký xác nhận của Bí thư Chi bộ.",
            "Tổ trưởng / Trưởng tổ + Bí thư Chi bộ thôn/trường",
            "Biên bản bàn giao chuẩn hoá dữ liệu chi bộ có ký nhận của Bí thư Chi bộ"
        ),
    ]

    for s in steps:
        r3 += 1
        ws3.row_dimensions[r3].height = 46
        for c_idx, val in enumerate(s, 1):
            cell = ws3.cell(row=r3, column=c_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            if c_idx == 1:
                cell.alignment = align_center
                cell.font = font_data_bold
                cell.fill = fill_highlight
            elif c_idx == 2:
                cell.alignment = align_left
                cell.font = font_data_bold
            else:
                cell.alignment = align_left

    col_widths_s3 = [10, 24, 38, 32, 24, 30]
    for i, w in enumerate(col_widths_s3, 1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    ws3.freeze_panes = "A6"

    # Lưu file
    wb.save(output_path)
    # copy to van_ban_du_thao/2026/
    import shutil
    draft_dir = r"e:\Viet Design\Chuyên viên ảo\van_ban_du_thao\2026"
    if os.path.exists(draft_dir):
        shutil.copy2(output_path, os.path.join(draft_dir, os.path.basename(output_path)))
    print("Xuat file Excel thanh cong!")

if __name__ == "__main__":
    target_file = r"e:\Viet Design\Chuyên viên ảo\Bang_phan_cong_To_ho_tro_CD_so_Cong_Hai.xlsx"
    create_phan_cong_excel(target_file)
