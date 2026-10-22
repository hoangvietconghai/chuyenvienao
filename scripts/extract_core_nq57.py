# -*- coding: utf-8 -*-
"""
Đọc trích đoạn các văn bản xương sống cốt lõi
"""
import os
import sys
import pypdf

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NQ57_DIR = os.path.join(BASE_DIR, "van_ban_den", "NQ57")

def read_pages(rel_path, num_pages=2):
    full_path = os.path.join(NQ57_DIR, rel_path)
    if not os.path.exists(full_path):
        return f"File không tồn tại: {rel_path}"
    try:
        reader = pypdf.PdfReader(full_path)
        out = []
        for i in range(min(num_pages, len(reader.pages))):
            t = reader.pages[i].extract_text() or ""
            out.append(f"--- TRANG {i+1} ---\n" + t[:1500])
        return "\n".join(out)
    except Exception as e:
        return f"Lỗi đọc: {e}"

files_to_check = [
    ("VB CỦA XÃ/NQ triển khai thực hiện Nghị quyết 57.signed.signed.pdf", 2),
    ("VB CỦA XÃ/H32.227-KH-KH-0308-2026-001_dadongdau.pdf", 3),
    ("VB CỦA TỈNH/26 5 FILE KY Ke hoach Chuyen doi so tinh Khanh Hoa giai doan 2026 2030 FINAL 0162026 nnngoc 03061125 nnngoc 03060938 docx signed.signed.pdf", 2),
    ("VB CỦA TỈNH/05- kem theo Phụ lục I-II-III_M-20h.signed.pdf", 2)
]

with open(os.path.join(BASE_DIR, "van_ban_den", "NQ57_core_extracts.txt"), "w", encoding="utf-8") as f_out:
    for rel_path, pages in files_to_check:
        f_out.write(f"\n=========================================\nFILE: {rel_path}\n=========================================\n")
        f_out.write(read_pages(rel_path, pages))

print("Core extraction done!")
