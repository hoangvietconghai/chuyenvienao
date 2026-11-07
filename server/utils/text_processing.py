# -*- coding: utf-8 -*-
"""
server/utils/text_processing.py
===============================
Các hàm tiện ích xử lý văn bản, chuẩn hoá chính tả Khối Đảng,
bóc tách ngày tháng và chuẩn hoá thể loại văn bản dùng chung toàn hệ thống.
"""

import re
from datetime import datetime
from typing import Optional


# Bảng tra chuẩn hoá chính tả kiểu gõ Khối Đảng (oà, uỷ, uý)
PARTY_SPELLING_MAP = [
    # Nhóm dấu hoà / oà
    ("hòa", "hoà"), ("Hòa", "Hoà"), ("HÒA", "HOÀ"),
    ("hóa", "hoá"), ("Hóa", "Hoá"), ("HÓA", "HOÁ"),
    ("hỏa", "hoả"), ("Hỏa", "Hoả"), ("HỎA", "HOẢ"),
    ("hõa", "hoã"), ("Hõa", "Hoã"), ("HÕA", "HOÃ"),
    ("họa", "hoạ"), ("Họa", "Hoạ"), ("HỌA", "HOẠ"),
    ("tòa", "toà"), ("Tòa", "Toà"), ("TÒA", "TOÀ"),
    ("xóa", "xoá"), ("Xóa", "Xoá"), ("XÓA", "XOÁ"),
    ("tỏa", "toả"), ("Tỏa", "Toả"), ("TỎA", "TOẢ"),
    ("khóa", "khoá"), ("Khóa", "Khoá"), ("KHÓA", "KHOÁ"),
    ("thỏa", "thoả"), ("Thỏa", "Thoả"), ("THỎA", "THOẢ"),
    ("đóa", "đoá"), ("Đóa", "Đoá"), ("ĐÓA", "ĐOÁ"),
    ("lóa", "loá"), ("Lóa", "Loá"), ("LÓA", "LOÁ"),
    ("lòa", "loà"), ("Lòa", "Loà"), ("LÒA", "LOÀ"),
    ("chóa", "choá"), ("Chóa", "Choá"), ("CHÓA", "CHOÁ"),
    ("loạn", "loạn"), # giữ nguyên

    # Nhóm dấu uỷ / uý
    ("ủy", "uỷ"), ("Ủy", "Uỷ"), ("ỦY", "UỶ"),
    ("úy", "uý"), ("Úy", "Uý"), ("ÚY", "UÝ"),
    ("hủy", "huỷ"), ("Hủy", "Huỷ"), ("HỦY", "HUỶ"),
    ("thúy", "thuý"), ("Thúy", "Thuý"), ("THÚY", "THUÝ"),
    ("thủy", "thuỷ"), ("Thủy", "Thuỷ"), ("THỦY", "THUỶ"),
    ("thụy", "thuỵ"), ("Thụy", "Thuỵ"), ("THỤY", "THUỴ"),
    ("lũy", "luỹ"), ("Lũy", "Luỹ"), ("LŨY", "LUỸ"),
    ("quý", "quý"), ("Quý", "Quý"), ("QUÝ", "QUÝ"),
    ("quỳ", "quỳ"), ("quỹ", "quỹ"), ("quỵ", "quỵ"),

    # Địa danh & tổ chức đặc thù
    ("Khánh Hòa", "Khánh Hoà"),
    ("KHÁNH HÒA", "KHÁNH HOÀ"),
    ("Đảng ủy", "Đảng uỷ"),
    ("ĐẢNG ỦY", "ĐẢNG UỶ"),
    ("Ủy ban", "Uỷ ban"),
    ("ỦY BAN", "UỶ BAN"),
]


def correct_party_spelling(text: str) -> str:
    """
    Chuẩn hoá dấu tiếng Việt theo quy định của Khối Đảng (oà, uỷ, uý).
    """
    if not text:
        return ""
    res = text
    for old, new in PARTY_SPELLING_MAP:
        res = res.replace(old, new)
    return res


def parse_vietnamese_date(text: str) -> Optional[str]:
    """
    Bóc tách ngày tháng năm tiếng Việt từ chuỗi và trả về định dạng chuẩn ISO 'YYYY-MM-DD'.
    Hỗ trợ:
      - 'dd/mm/yyyy' hoặc 'dd-mm-yyyy'
      - 'ngày dd tháng mm năm yyyy'
    """
    if not text:
        return None

    # Dạng 1: ngày dd tháng mm năm yyyy
    m1 = re.search(r'ngày\s*([0-9]{1,2})\s*tháng\s*([0-9]{1,2})\s*năm\s*([0-9]{4})', text, re.IGNORECASE)
    if m1:
        d, m, y = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}"

    # Dạng 2: dd/mm/yyyy hoặc dd-mm-yyyy
    m2 = re.search(r'\b([0-9]{1,2})[\/\-]([0-9]{1,2})[\/\-]([0-9]{4})\b', text)
    if m2:
        d, m, y = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}"

    return None


def normalize_party_doc_type(raw: str) -> str:
    """
    Chuẩn hoá mã thể loại văn bản của cấp uỷ và chính quyền:
    CV, KH, TB, KL, BC, TTr, QD, NQ, CT, CTR.
    """
    r = (raw or "").upper().strip()
    if "CV" in r or "CÔNG VĂN" in r or "GIAO VIỆC" in r:
        return "CV"
    if "KH" in r or "KẾ HOẠCH" in r:
        return "KH"
    if "TB" in r or "THÔNG BÁO" in r:
        return "TB"
    if "KL" in r or "KẾT LUẬN" in r:
        return "KL"
    if "BC" in r or "BÁO CÁO" in r:
        return "BC"
    if "TTR" in r or "TỜ TRÌNH" in r:
        return "TTr"
    if "QĐ" in r or "QD" in r or "QUYẾT ĐỊNH" in r:
        return "QD"
    if "NQ" in r or "NGHỊ QUYẾT" in r:
        return "NQ"
    if "CT" in r or "CHỈ THỊ" in r:
        return "CT"
    if "CTR" in r or "CHƯƠNG TRÌNH" in r:
        return "CTR"
    return "CV"
