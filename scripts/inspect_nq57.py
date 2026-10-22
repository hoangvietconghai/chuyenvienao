# -*- coding: utf-8 -*-
"""
scripts/inspect_nq57.py
Quét và trích xuất thông tin toàn bộ văn bản trong thư mục van_ban_den/NQ57
"""
import os
import re
import sys
import json
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NQ57_DIR = os.path.join(BASE_DIR, "van_ban_den", "NQ57")

def extract_pdf_info(file_path):
    info = {
        "so_hieu": "",
        "ngay_ban_hanh": "",
        "co_quan": "",
        "trich_yeu": "",
        "text_snippet": "",
        "pages": 0,
        "is_scanned": False
    }
    try:
        reader = pypdf.PdfReader(file_path)
        info["pages"] = len(reader.pages)
        full_text = ""
        for i in range(min(3, len(reader.pages))):
            t = reader.pages[i].extract_text() or ""
            full_text += t + "\n"
        
        full_text = full_text.strip()
        if not full_text or len(full_text) < 50:
            info["is_scanned"] = True
            info["text_snippet"] = "[BẢN QUÉT SCAN - KHÔNG CÓ TEXT LAYER]"
            return info

        info["text_snippet"] = full_text[:1200]
        
        # Regex tìm số hiệu
        m_so = re.search(r'(Số\s*:\s*[0-9A-Za-z\/\-_]+|Số\s+[0-9A-Za-z\/\-_]+)', full_text, re.IGNORECASE)
        if m_so:
            info["so_hieu"] = m_so.group(0).strip()
            
        # Regex tìm cơ quan
        lines = [l.strip() for l in full_text.split("\n") if l.strip()]
        for l in lines[:10]:
            upper = l.upper()
            if any(k in upper for k in ["BỘ CHÍNH TRỊ", "BAN CHỈ ĐẠO", "TỈNH UỶ", "ĐẢNG UỶ", "UỶ BAN NHÂN DÂN", "VĂN PHÒNG"]):
                if not info["co_quan"]:
                    info["co_quan"] = l
                    break

        # Regex tìm trích yếu (sau V/v hoặc dòng in hoa KẾ HOẠCH, NGHỊ QUYẾT, BÁO CÁO...)
        for i, l in enumerate(lines[:25]):
            if any(l.startswith(k) for k in ["NGHỊ QUYẾT", "KẾ HOẠCH", "QUYẾT ĐỊNH", "THÔNG BÁO", "BÁO CÁO", "CHỈ THỊ", "TỜ TRÌNH"]):
                info["trich_yeu"] = l
                if i + 1 < len(lines) and not lines[i+1].startswith(("Căn cứ", "Thực hiện", "I.", "1.")):
                    info["trich_yeu"] += " " + lines[i+1]
                break
            elif "V/v" in l or "về việc" in l.lower():
                info["trich_yeu"] = l
                break

    except Exception as e:
        info["text_snippet"] = f"[LỖI ĐỌC: {str(e)}]"
    return info

def scan_all():
    results = {}
    for sub in ["VB CỦA TW", "VB CỦA TỈNH", "VB CỦA XÃ"]:
        sub_path = os.path.join(NQ57_DIR, sub)
        if not os.path.exists(sub_path):
            continue
        results[sub] = []
        for fname in sorted(os.listdir(sub_path)):
            fpath = os.path.join(sub_path, fname)
            if not os.path.isfile(fpath):
                continue
            item = {
                "filename": fname,
                "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                "ext": os.path.splitext(fname)[1].lower()
            }
            if item["ext"] == ".pdf":
                info = extract_pdf_info(fpath)
                item.update(info)
            else:
                item["text_snippet"] = f"[Tệp {item['ext']}]"
            results[sub].append(item)

    out_json = os.path.join(BASE_DIR, "van_ban_den", "NQ57_manifest.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Hoàn thành quét {sum(len(v) for v in results.values())} tệp. Lưu tại {out_json}")

if __name__ == "__main__":
    scan_all()
