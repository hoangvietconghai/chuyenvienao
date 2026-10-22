# -*- coding: utf-8 -*-
"""
scripts/extract_bcd57_reports.py
Trích xuất nội dung các Báo cáo CĐS của Ban Chỉ đạo 57 (cấp Tỉnh và cấp Xã)
để tạo file tổng hợp tri thức tong_hop_bao_cao_bcd57.md
"""
import os
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TINH_DIR = os.path.join(BASE_DIR, "van_ban_den", "NQ57", "VB CỦA TỈNH")
XA_DIR = os.path.join(BASE_DIR, "van_ban_den", "NQ57", "VB CỦA XÃ")

def extract_text_from_pdf(fpath, max_pages=5):
    if not os.path.exists(fpath):
        return f"File not found: {fpath}"
    try:
        reader = pypdf.PdfReader(fpath)
        out = []
        for i in range(min(max_pages, len(reader.pages))):
            t = reader.pages[i].extract_text() or ""
            out.append(f"--- TRANG {i+1} ---\n{t[:1200]}")
        return "\n".join(out)
    except Exception as e:
        return f"Error reading {fpath}: {e}"

files = {
    "TINH_BC05": os.path.join(TINH_DIR, "BC 05 BCĐ 57 TU kết quả thực hiện NQ 48 năm 2025.pdf"),
    "TINH_PL05": os.path.join(TINH_DIR, "PL kèm BC 05 BCĐ 57 TU chỉ tiêu CĐS đến 2030.pdf"),
    "TINH_BC175": os.path.join(TINH_DIR, "BC 175 TU giám sát thực hiện NQ 57 về CĐS.pdf"),
    "XA_BC2025": os.path.join(XA_DIR, "BC ĐU về CĐS các cơ quan Đảng xã năm 2025.pdf"),
    "XA_BCLD": os.path.join(XA_DIR, "BC ĐU về lãnh đạo chỉ đạo thực hiện NQ 57 về CĐS.pdf"),
    "XA_BCKH02": os.path.join(XA_DIR, "BC ĐU chuyên đề thực hiện KH 02 BCĐ 57 về CĐS.pdf")
}

out_data = {}
for key, p in files.items():
    out_data[key] = extract_text_from_pdf(p, 4)

with open(os.path.join(BASE_DIR, "van_ban_den", "raw_bcd57_reports.txt"), "w", encoding="utf-8") as f:
    for k, text in out_data.items():
        f.write(f"\n=========================================\nKEY: {k}\n=========================================\n")
        f.write(text)

print("EXTRACTION OF BCD57 REPORTS FINISHED.")
