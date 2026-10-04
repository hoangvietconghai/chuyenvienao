# -*- coding: utf-8 -*-
"""
scripts/clean_so_hoa_corpus.py
==============================
Làm sạch triệt để lỗi dính chữ OCR, rác số trang và chuẩn hoá chính tả khối Đảng
cho toàn bộ kho 163 văn bản số hoá toàn văn tại references/van_ban_so_hoa_toan_van/.
"""

import glob
import os
import re
import sys
import shutil

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CORPUS_DIR = r"references/van_ban_so_hoa_toan_van"
BACKUP_DIR = r"references/van_ban_so_hoa_toan_van_backup"

EXACT_REPLACEMENTS = [
    # 1. Tách số và ngày dính
    (r'(?i)\bsố(\d+)\b', r'số \1'),
    (r'(?i)\bngày(\d+)\b', r'ngày \1'),
    (r'(?i)\btháng(\d+)\b', r'tháng \1'),
    (r'(?i)\bnăm(\d+)\b', r'năm \1'),
    (r'(?i)\bkhóa(\d+)\b', r'khóa \1'),
    (r'(?i)\bkhoá(\d+)\b', r'khoá \1'),

    # 2. Từ ghép hành chính phổ biến bị dính chữ
    ('Cụthểhóa', 'Cụ thể hoá'), ('cụthểhóa', 'cụ thể hoá'),
    ('Cụthểhoá', 'Cụ thể hoá'), ('cụthểhoá', 'cụ thể hoá'),
    ('Cụthể', 'Cụ thể'), ('cụthể', 'cụ thể'),
    ('chủtrương', 'chủ trương'), ('Chủtrương', 'Chủ trương'),
    ('tổchức', 'tổ chức'), ('Tổchức', 'Tổ chức'),
    ('chỉđạo', 'chỉ đạo'), ('Chỉđạo', 'Chỉ đạo'),
    ('lãnhđạo', 'lãnh đạo'), ('Lãnhđạo', 'Lãnh đạo'),
    ('sựnghiệp', 'sự nghiệp'), ('Sựnghiệp', 'Sự nghiệp'),
    ('sựđồng', 'sự đồng'), ('Sựđồng', 'Sự đồng'),
    ('trởthành', 'trở thành'),
    ('lộtrình', 'lộ trình'), ('Lộtrình', 'Lộ trình'),
    ('kếhoạch', 'kế hoạch'), ('Kếhoạch', 'Kế hoạch'),
    ('đềán', 'đề án'), ('Đềán', 'Đề án'),
    ('chỉthị', 'chỉ thị'), ('Chỉthị', 'Chỉ thị'),
    ('nghịquyết', 'nghị quyết'), ('Nghịquyết', 'Nghị quyết'),
    ('kếtluận', 'kết luận'), ('Kếtluận', 'Kết luận'),
    ('quyếtđịnh', 'quyết định'), ('Quyếtđịnh', 'Quyết định'),
    ('chươngtrình', 'chương trình'), ('Chươngtrình', 'Chương trình'),
    ('thôngbáo', 'thông báo'), ('Thôngbáo', 'Thông báo'),
    ('côngvăn', 'công văn'), ('Côngvăn', 'Công văn'),
    ('báocáo', 'báo cáo'), ('Báocáo', 'Báo cáo'),
    ('bảovệ', 'bảo vệ'), ('Bảovệ', 'Bảo vệ'),
    ('xửlý', 'xử lý'), ('Xửlý', 'Xử lý'),
    ('phổbiến', 'phổ biến'), ('Phổbiến', 'Phổ biến'),
    ('pháttriển', 'phát triển'), ('Pháttriển', 'Phát triển'),
    ('thựchiện', 'thực hiện'), ('Thựchiện', 'Thực hiện'),
    ('xâydựng', 'xây dựng'), ('Xâydựng', 'Xây dựng'),
    ('nhiệmvụ', 'nhiệm vụ'), ('Nhiệmvụ', 'Nhiệm vụ'),
    ('bảnthân', 'bản thân'), ('bảnsắc', 'bản sắc'),
    ('côngtác', 'công tác'), ('Côngtác', 'Công tác'),
    ('cánbộ', 'cán bộ'), ('Cánbộ', 'Cán bộ'),
    ('đảngviên', 'đảng viên'), ('Đảngviên', 'Đảng viên'),
    ('quầnchúng', 'quần chúng'), ('nhândân', 'nhân dân'),
    ('kinhtế', 'kinh tế'), ('xãhội', 'xã hội'),
    ('quốcphòng', 'quốc phòng'), ('anninh', 'an ninh'),
    ('toàndiện', 'toàn diện'), ('toànthể', 'toàn thể'),
    ('đầyđủ', 'đầy đủ'), ('kịpthời', 'kịp thời'),
    ('nghiêmtúc', 'nghiêm túc'), ('hiệuquả', 'hiệu quả'),
    ('chấtlượng', 'chất lượng'), ('thườngxuyên', 'thường xuyên'),
    ('BộChính', 'Bộ Chính'), ('Trungương', 'Trung ương'),
    ('BanThường', 'Ban Thường'), ('Thườngvụ', 'Thường vụ'),
    ('Thườngtrực', 'Thường trực'), ('Đảnguỷ', 'Đảng uỷ'), ('Đảngbộ', 'Đảng bộ'),
    ('Tổquốc', 'Tổ quốc'), ('UBNDxã', 'UBND xã'), ('HĐNDxã', 'HĐND xã'), ('MTTQxã', 'MTTQ xã'),
    ('KhánhHòa', 'Khánh Hoà'), ('KhánhHoà', 'Khánh Hoà'), ('CôngHải', 'Công Hải'),
    ('ThuậnBắc', 'Thuận Bắc'), ('PhướcChiến', 'Phước Chiến'),

    # 3. Cụm từ dính ngữ cảnh cụ thể
    ('BộChính trịvà', 'Bộ Chính trị và'),
    ('Bộ Chính trịvà', 'Bộ Chính trị và'),
    ('BộChính trịvề', 'Bộ Chính trị về'),
    ('Bộ Chính trịvề', 'Bộ Chính trị về'),
    ('Bộ Chính trịkhóa', 'Bộ Chính trị khóa'),
    ('BộChính trịkhóa', 'Bộ Chính trị khóa'),
    ('vềtiếp tục', 'về tiếp tục'),
    ('vềxây dựng', 'về xây dựng'),
    ('vềphát triển', 'về phát triển'),
    ('vềvai trò', 'về vai trò'),
    ('vềlĩnh vực', 'về lĩnh vực'),
    ('vềthực hiện', 'về thực hiện'),
    ('vềmình', 'về mình'),
    ('vềquản lý', 'về quản lý'),
    ('vềkinh tế', 'về kinh tế'),
    ('vềxã hội', 'về xã hội'),
    ('tronglãnh đạo', 'trong lãnh đạo'),
    ('trongthực hiện', 'trong thực hiện'),
    ('trongtuyên truyền', 'trong tuyên truyền'),
    ('trongquản lý', 'trong quản lý'),
    ('trongxây dựng', 'trong xây dựng'),
    ('vàphát triển', 'và phát triển'),
    ('vàtriển khai', 'và triển khai'),
    ('vàthực hiện', 'và thực hiện'),
    ('vàquản lý', 'và quản lý'),
    ('vàNhân dân', 'và Nhân dân'),
    ('vàcác', 'và các'),
    ('vớicác', 'với các'),
    ('đốivới', 'đối với'),
    ('đối vớisự', 'đối với sự'),
    ('hiệuquảcác', 'hiệu quả các'),
    ('hiệu quảcác', 'hiệu quả các'),
    ('hiệu quảKết', 'hiệu quả Kết'),
    ('nhiệm vụđược', 'nhiệm vụ được'),
    ('nhiệm vụxây', 'nhiệm vụ xây'),
    ('toàn Đảng bộlãnh đạo', 'toàn Đảng bộ lãnh đạo'),
    ('toàn thểcán', 'toàn thể cán'),
    ('thực sựtrở', 'thực sự trở'),
    ('giá trịvăn', 'giá trị văn'),
    ('giá trị“chân', 'giá trị “chân'),
    ('bảo vệnền', 'bảo vệ nền'),
    ('vấn đềphức', 'vấn đề phức'),
    ('phổbiến', 'phổ biến'),
    ('đơn vịtrong', 'đơn vị trong'),
    ('cơ quan, đơn vịtrong', 'cơ quan, đơn vị trong'),
    ('đồng bộvới', 'đồng bộ với'),
    ('căn cứtình', 'căn cứ tình'),
    ('tổchức chính trị- xã hội', 'tổ chức chính trị - xã hội'),
    ('chính trị- xã hội', 'chính trị - xã hội'),
    ('trênđịa bàn', 'trên địa bàn'),
    ('địa bànxã', 'địa bàn xã'),

    # 4. Chuẩn hoá chính tả khối Đảng bắt buộc
    ('văn hóa', 'văn hoá'), ('Văn hóa', 'Văn hoá'), ('VĂN HÓA', 'VĂN HOÁ'),
    ('hòa bình', 'hoà bình'), ('hài hòa', 'hài hoà'), ('cộng hòa', 'cộng hoà'),
    ('Hòa', 'Hoà'), ('HÒA', 'HOÀ'), ('hòa', 'hoà'),
    ('Ủy', 'Uỷ'), ('ỦY', 'UỶ'), ('ủy', 'uỷ'),
    ('Úy', 'Uý'), ('ÚY', 'UÝ'), ('úy', 'uý'),
    ('Thùy', 'Thuỳ'), ('THÙY', 'THUỲ'), ('thùy', 'thuỳ'),
]


def clean_markdown_document(text: str) -> str:
    parts = text.split('---', 2)
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = parts[2]
        has_frontmatter = True
    else:
        frontmatter = ''
        body = text
        has_frontmatter = False

    # Xử lý thân bài
    for pat, repl in EXACT_REPLACEMENTS:
        if pat.startswith('(?i)'):
            body = re.sub(pat, repl, body)
        else:
            body = body.replace(pat, repl)

    # Xoá dòng rác số trang OCR (dòng chỉ có 1-2 chữ số)
    body = re.sub(r'(?m)^\s*\d{1,2}\s*$\n', '', body)

    # Dọn dẹp khoảng trắng thừa
    cleaned_lines = []
    for line in body.splitlines():
        l_clean = re.sub(r'[ \t]+', ' ', line).strip()
        cleaned_lines.append(l_clean)
    body = '\n'.join(cleaned_lines)
    body = re.sub(r'\n{3,}', '\n\n', body)

    # Xử lý frontmatter (chỉ chuẩn hoá chính tả khối Đảng)
    if has_frontmatter:
        fm_clean = frontmatter.replace('Hòa', 'Hoà').replace('HÒA', 'HOÀ').replace('hòa', 'hoà')
        fm_clean = fm_clean.replace('Ủy', 'Uỷ').replace('ỦY', 'UỶ').replace('ủy', 'uỷ')
        fm_clean = fm_clean.replace('Thùy', 'Thuỳ').replace('THÙY', 'THUỲ').replace('thùy', 'thuỳ')
        fm_clean = fm_clean.replace('Thuận Bắc', 'xã Công Hải')  # Trừ lịch sử
        return f"---{fm_clean}---\n\n{body}\n"
    else:
        return f"{body}\n"


def main():
    files = glob.glob(os.path.join(CORPUS_DIR, "*.md"))
    print(f"Bắt đầu làm sạch kho văn bản số hoá: {len(files)} tệp...")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    count = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        bpath = os.path.join(BACKUP_DIR, fname)
        if not os.path.exists(bpath):
            shutil.copy2(fpath, bpath)

        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
            orig = fp.read()

        cleaned = clean_markdown_document(orig)

        if cleaned != orig:
            count += 1
            with open(fpath, 'w', encoding='utf-8') as fp:
                fp.write(cleaned)

    print(f" Hoàn tất! Đã làm sạch và chuẩn hoá thành công {count}/{len(files)} tệp.")


if __name__ == "__main__":
    main()
