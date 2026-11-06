import os
import sys
import shutil
import zipfile
import re
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'references/Danh mục vị trí việc làm/0. A1_A2_Văn phòng Đảng uỷ.xlsx'
backup_path = 'references/Danh mục vị trí việc làm/0. A1_A2_Văn phòng Đảng uỷ_backup_before_c1_fill.xlsx'

# 1. Backup
shutil.copyfile(file_path, backup_path)
print(f"1. Đã sao lưu dự phòng: {backup_path}")

# 2. Load workbook
wb = openpyxl.load_workbook(file_path, data_only=False)
ws_c1 = wb['6. C1_VTVL']

# 3. Dữ liệu chuẩn 07 VTVL Văn phòng Đảng uỷ theo QĐ 503-QĐ/TU
vtvl_data = [
    (
        'LĐ,QL.01',
        'Lãnh đạo, quản lý Văn phòng đảng uỷ cấp xã (Chánh Văn phòng, Phó Chánh Văn phòng)',
        'Cán bộ',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    ),
    (
        'CMNV.02',
        'Chuyên viên về Văn phòng cấp uỷ',
        'Công chức',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    ),
    (
        'CMNV.03',
        'Chuyên viên về chuyển đổi số',
        'Công chức',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    ),
    (
        'CMNV.04',
        'Cơ yếu viên',
        'Công chức',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    ),
    (
        'CMNV.05',
        'Kế toán viên',
        'Công chức',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    ),
    (
        'CMNV.06',
        'Văn thư, Lưu trữ',
        'Công chức',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    ),
    (
        'CMNV.07',
        'Thủ quỹ',
        'Công chức',
        'Quyết định số 503-QĐ/TU ngày 15/6/2026 của BTV Tỉnh uỷ',
        'Mức chung 1.904 giờ – Bộ luật Lao động và quy định về thời giờ làm việc',
        'Tiếp tục sử dụng',
        'Phổ biến (40 giờ/tuần)'
    )
]

for idx, item in enumerate(vtvl_data, start=3):
    ma, ten, loai_nl, qd, can_cu, tt, che_do = item
    ws_c1.cell(idx, 1, ma)       # Col A: Mã VTVL
    ws_c1.cell(idx, 2, ten)      # Col B: Tên VTVL
    ws_c1.cell(idx, 3, loai_nl)  # Col C: Loại nhân lực
    ws_c1.cell(idx, 4, qd)       # Col D: Quyết định
    # Col E: Giữ nguyên công thức
    ws_c1.cell(idx, 5, f'=IF(A{idx}="","",IF(NOT(OR(J{idx}="Phổ biến (40 giờ/tuần)",J{idx}="Đặc thù")),"",IF(OR(J{idx}="Đặc thù",H{idx}<>""),IF(AND(ISNUMBER(H{idx}),H{idx}>0,F{idx}<>"",I{idx}="Đã kiểm chứng"),H{idx},""),QUY_GIO_PP2)))')
    ws_c1.cell(idx, 6, can_cu)   # Col F: Căn cứ xác định quỹ giờ
    ws_c1.cell(idx, 7, tt)       # Col G: Trạng thái
    ws_c1.cell(idx, 8, None)     # Col H: Giờ riêng (để trống)
    ws_c1.cell(idx, 9, None)     # Col I: Xác nhận giờ riêng (để trống)
    ws_c1.cell(idx, 10, che_do)  # Col J: Chế độ làm việc
    # Col K: Giữ nguyên công thức
    ws_c1.cell(idx, 11, f'=IF(A{idx}="","",IF(J{idx}="","CHƯA CHỌN CHẾ ĐỘ LÀM VIỆC",IF(NOT(OR(J{idx}="Phổ biến (40 giờ/tuần)",J{idx}="Đặc thù")),"CHẾ ĐỘ KHÔNG HỢP LỆ",IF(AND(J{idx}="Đặc thù",E{idx}=""),"THIẾU GIỜ ĐẶC THÙ",IF(AND(H{idx}<>"",E{idx}=""),"GIỜ CHƯA XÁC NHẬN",IF(E{idx}="","THIẾU MẪU SỐ","ĐẠT"))))))')

print(f"2. Đã nạp thành công {len(vtvl_data)} VTVL vào sheet 6. C1_VTVL (Dòng 3 -> 9).")

# Clear external links attribute in openpyxl
wb._external_links = []
wb.save(file_path)
print("3. Đã lưu tệp workbook.")

# Patch VML comments in zip
temp_zip = file_path + ".temp.zip"
total_patched = 0
with zipfile.ZipFile(file_path, 'r') as zin, zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        content = zin.read(item.filename)
        if 'commentsdrawing' in item.filename.lower() and item.filename.endswith('.vml'):
            text = content.decode('utf-8', errors='ignore')
            new_text = re.sub(r'width:[0-9.]+(?:px|pt);height:[0-9.]+(?:px|pt)', 'width:360pt;height:180pt', text)
            def add_autofit(m):
                tag = m.group(0)
                if 'AutoFit' not in tag:
                    pfx_match = re.search(r'<([a-zA-Z0-9]+):ClientData', tag)
                    pfx = pfx_match.group(1) if pfx_match else 'x'
                    return tag.replace('>', f'>\n    <{pfx}:AutoFit/>', 1)
                return tag
            new_text = re.sub(r'<[a-zA-Z0-9]+:ClientData[^>]*>', add_autofit, new_text)
            content = new_text.encode('utf-8')
            total_patched += 1
        zout.writestr(item, content)

os.replace(temp_zip, file_path)
print(f"4. Đã bảo toàn định dạng Note/Comment ({total_patched} tệp).")

