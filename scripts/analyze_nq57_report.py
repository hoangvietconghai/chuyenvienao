# -*- coding: utf-8 -*-
"""
scripts/analyze_nq57_report.py
Phân tích toàn diện kho văn bản NQ57:
"""
import os
import sys
import json
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
manifest_path = os.path.join(BASE_DIR, "van_ban_den", "NQ57_manifest.json")

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

out_report_path = os.path.join(BASE_DIR, "van_ban_den", "NQ57_detailed_analysis.txt")

with open(out_report_path, "w", encoding="utf-8") as out:
    out.write("====================================================================\n")
    out.write("BÁO CÁO PHÂN TÍCH TỔNG QUAN VĂN BẢN CHỈ ĐẠO NQ57 & LỌC NHIỄU\n")
    out.write("====================================================================\n\n")

    # 1. TRUNG ƯƠNG
    out.write("### I. VĂN BẢN CỦA TRUNG ƯƠNG (10 tệp)\n")
    for f in manifest.get("VB CỦA TW", []):
        fname = f["filename"]
        snip = f.get("text_snippet", "").replace("\n", " ")
        so = f.get("so_hieu", "")
        ty = f.get("trich_yeu", "")
        out.write(f"- Tệp: {fname} ({f['size_kb']} KB)\n")
        out.write(f"  + Số hiệu: {so} | Trích yếu: {ty}\n")
        out.write(f"  + Đoạn đầu: {snip[:250]}...\n\n")

    # 2. TỈNH KHÁNH HOÀ
    out.write("\n### II. VĂN BẢN CỦA TỈNH KHÁNH HOÀ (110 tệp)\n")
    tinh_docs = manifest.get("VB CỦA TỈNH", [])
    out.write(f"Tổng số văn bản Tỉnh: {len(tinh_docs)}\n")
    # Phân nhóm tỉnh
    for f in tinh_docs:
        fname = f["filename"]
        snip = f.get("text_snippet", "").replace("\n", " ")
        so = f.get("so_hieu", "")
        ty = f.get("trich_yeu", "")
        out.write(f"- Tệp: {fname} ({f['size_kb']} KB)\n")
        if so or ty:
            out.write(f"  + Số hiệu: {so} | Trích yếu: {ty}\n")
        out.write(f"  + Đoạn đầu: {snip[:200]}...\n\n")

    # 3. CẤP XÃ
    out.write("\n### III. VĂN BẢN CỦA XÃ CÔNG HẢI (44 tệp)\n")
    xa_docs = manifest.get("VB CỦA XÃ", [])
    out.write(f"Tổng số văn bản Xã: {len(xa_docs)}\n")
    for f in xa_docs:
        fname = f["filename"]
        snip = f.get("text_snippet", "").replace("\n", " ")
        so = f.get("so_hieu", "")
        ty = f.get("trich_yeu", "")
        out.write(f"- Tệp: {fname} ({f['size_kb']} KB)\n")
        if so or ty:
            out.write(f"  + Số hiệu: {so} | Trích yếu: {ty}\n")
        out.write(f"  + Đoạn đầu: {snip[:250]}...\n\n")

print(f"Báo cáo phân tích đã được ghi vào: {out_report_path}")
