# -*- coding: utf-8 -*-
import sys
import docx
sys.stdout.reconfigure(encoding='utf-8')
import os
sys.path.insert(0, os.path.abspath("."))
from server.plan_registry import verify_draft_against_indicators, build_appraisal_grounding_context

doc = docx.Document("ĐU-KH triển khai thực hiện Nghị quyết số 19 của BCH Trung ương Đảng khoá XIV.docx")
full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

res = verify_draft_against_indicators(full_text)
print("--- VERIFIED MATCHES ---")
for m in res['verified_matches']:
    print(f"{m['ma_chi_tieu']}: {m['ten_chi_tieu']} -> {m['gia_tri']}")

print("\n--- DISCREPANCIES FOUND ---")
for d in res['discrepancies']:
    print(f"[{d['ma_chi_tieu']}] {d['muc_van_ban']}: {d['van_de']}")

print("\n--- GROUNDING CONTEXT SAMPLE ---")
print(build_appraisal_grounding_context(full_text)[:800])
