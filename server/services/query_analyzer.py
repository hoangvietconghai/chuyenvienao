# -*- coding: utf-8 -*-
"""
server/services/query_analyzer.py
=================================
Bộ Phân tích Ý định & Thực thể Hành chính (Administrative Entity & Intent Analyzer)
cho Hệ thống Hybrid RAG Văn phòng Đảng uỷ xã Công Hải:
1. Trích xuất Thực thể Số hiệu Văn bản: NQ 11, 11-NQ/ĐU, Kế hoạch 69, QĐ 05, v.v.
2. Giải quyết Tham chiếu Ngữ cảnh Hội thoại (Anaphora Resolution):
   Phát hiện "đó", "này", "văn bản trên", "nghị quyết đó" -> Quét lịch sử hội thoại
   để khôi phục số hiệu văn bản đang bàn thảo.
3. Phân loại Định tuyến Truy vấn:
   - DIRECT_HIT: Hỏi đích danh 1 hoặc nhiều văn bản cụ thể.
   - AGGREGATE: Hỏi thống kê, đếm số lượng văn bản trong kho.
   - THEMATIC: Hỏi theo chủ đề, nội dung, tìm kiếm ngữ nghĩa tự nhiên.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from server.logger import get_logger

logger = get_logger("query_analyzer")

# Bản đồ chuẩn hoá loại văn bản tiếng Việt sang mã ký hiệu
DOC_TYPE_MAP = {
    "nghị quyết": "NQ", "nghi quyet": "NQ", "nq": "NQ",
    "kế hoạch": "KH", "ke hoach": "KH", "kh": "KH",
    "báo cáo": "BC", "bao cao": "BC", "bc": "BC",
    "quyết định": "QĐ", "quyet dinh": "QĐ", "qđ": "QĐ", "qd": "QĐ",
    "công văn": "CV", "cong van": "CV", "cv": "CV",
    "thông báo": "TB", "thong bao": "TB", "tb": "TB",
    "kết luận": "KL", "ket luan": "KL", "kl": "KL",
    "chỉ thị": "CT", "chi thi": "CT", "ct": "CT",
    "tờ trình": "TTr", "to trinh": "TTr", "ttr": "TTr",
    "chương trình": "CTr", "chuong trinh": "CTr", "ctr": "CTr",
    "hướng dẫn": "HD", "huong dan": "HD", "hd": "HD",
    "quy định": "QĐi", "quyet dinh": "QĐi", "qđi": "QĐi", "qdi": "QĐi",
    "quy chế": "QC", "quy che": "QC", "qc": "QC",
}

# Các dấu hiệu đại từ chỉ thị / tham chiếu ngữ cảnh tiếp nối
ANAPHORA_MARKERS = [
    "đó", "này", "ấy", "trên", "nói trên", "vừa nêu", "vừa rồi",
    "văn bản đó", "nghị quyết đó", "kế hoạch đó", "báo cáo đó",
    "nội dung đó", "văn bản này", "văn bản trên", "nghị quyết trên",
    "đồng chí vừa nói", "ở trên", "vừa trích dẫn", "văn bản ấy"
]

# Từ khoá nhận diện câu hỏi thống kê / đếm số lượng
STATS_PATTERNS = [
    r'có\s+bao\s+nhiêu\s+(văn\s+bản|nghị\s+quyết|kế\s+hoạch|báo\s+cáo|quyết\s+định|công\s+văn)',
    r'thống\s+kê\s+(các|toàn\s+bộ|số\s+lượng)?\s*(văn\s+bản|nghị\s+quyết|kế\s+hoạch|báo\s+cáo)',
    r'đếm\s+số\s+lượng\s+(văn\s+bản|nghị\s+quyết|kế\s+hoạch)',
    r'danh\s+sách\s+(tất\s+cả\s+|toàn\s+bộ\s+)?(nghị\s+quyết|kế\s+hoạch|văn\s+bản)',
    r'tổng\s+số\s+(văn\s+bản|nghị\s+quyết|kế\s+hoạch)'
]


# Các danh xưng văn bản đặc biệt / không ghi số hiệu cụ thể (Named Document Aliases)
NAMED_DOCUMENT_ALIASES = [
    {
        "patterns": [
            r'nghị\s*quyết\s*đại\s*hội',
            r'nq\s*đại\s*hội',
            r'đại\s*hội\s*(?:đại\s*biểu\s*)?đảng\s*bộ\s*xã',
            r'đại\s*hội\s*lần\s*thứ\s*i\b',
            r'đại\s*hội\s*i\b',
            r'nq\s*[-/]?\s*đh\b',
            r'01\s*[-/]?\s*nq\s*[-/]?\s*đh\b',
            r'chỉ\s*tiêu\s*đại\s*hội',
        ],
        "the_loai": "NQ",
        "so": "01",
        "co_quan": "ĐH",
        "canonical": "01-NQ/ĐH",
        "search_patterns": ["01-NQ/ĐH%", "%01-NQ/ĐH%"]
    },
    {
        "patterns": [
            r'nghị\s*quyết\s*(?:về\s*)?(?:chuyển\s*đổi\s*số|cđs)',
            r'nq\s*(?:về\s*)?(?:chuyển\s*đổi\s*số|cđs)',
            r'nghị\s*quyết\s*57\s*(?:của\s*xã|xã|đảng\s*uỷ)',
        ],
        "the_loai": "NQ",
        "so": "02",
        "co_quan": "ĐU",
        "canonical": "02-NQ/ĐU",
        "search_patterns": ["02-NQ/ĐU%", "%02-NQ/ĐU%"]
    },
    {
        "patterns": [
            r'nghị\s*quyết\s*(?:nhiệm\s*vụ|phương\s*hướng)?\s*năm\s*2026',
            r'nq\s*(?:nhiệm\s*vụ|phương\s*hướng)?\s*năm\s*2026',
        ],
        "the_loai": "NQ",
        "so": "05",
        "co_quan": "ĐU",
        "canonical": "05-NQ/ĐU",
        "search_patterns": ["05-NQ/ĐU%", "%05-NQ/ĐU%"]
    },
    {
        "patterns": [
            r'kế\s*hoạch\s*(?:về\s*)?(?:chuẩn\s*hoá|rà\s*soát|làm\s*sạch)\s*dữ\s*liệu\s*(?:đảng\s*viên|đv)',
            r'kh\s*(?:về\s*)?(?:chuẩn\s*hoá|rà\s*soát|làm\s*sạch)\s*dữ\s*liệu\s*(?:đảng\s*viên|đv)',
        ],
        "the_loai": "KH",
        "so": "144",
        "co_quan": "ĐU",
        "canonical": "144-KH/ĐU",
        "search_patterns": ["144-KH/ĐU%", "%144-KH/ĐU%"]
    },
]


def _normalize_num(num_str: str) -> Tuple[str, str]:
    """Trả về cả dạng có số 0 đầu và dạng gốc: e.g. '1' -> ('01', '1'), '11' -> ('11', '11')"""
    num_str = num_str.strip()
    try:
        val = int(num_str)
        pad = f"{val:02d}"
        raw = str(val)
        return pad, raw
    except ValueError:
        return num_str, num_str


def extract_entities(query: str) -> List[Dict[str, Any]]:
    """
    Trích xuất các thực thể số hiệu văn bản trong câu hỏi.
    Ví dụ:
    - 'Nghị quyết số 11 của Đảng uỷ xã...' -> [{'the_loai': 'NQ', 'so': '11', 'search_patterns': ['11-NQ%', '%11-NQ%', '%11/NQ%']}]
    - '01-NQ/ĐH' -> [{'the_loai': 'NQ', 'so': '01', 'co_quan': 'ĐH', 'search_patterns': ['01-NQ/ĐH%']}]
    - 'NQ 11' -> [{'the_loai': 'NQ', 'so': '11', ...}]
    """
    if not query:
        return []

    results: List[Dict[str, Any]] = []
    seen_keys = set()

    # Mẫu 0: Nhận diện danh xưng văn bản đặc biệt / không ghi số hiệu cụ thể (Named Aliases)
    for alias in NAMED_DOCUMENT_ALIASES:
        for p in alias["patterns"]:
            if re.search(p, query, re.IGNORECASE):
                canon = alias["canonical"]
                if canon not in seen_keys:
                    seen_keys.add(canon)
                    results.append({
                        "the_loai": alias["the_loai"],
                        "so": alias["so"],
                        "co_quan": alias.get("co_quan"),
                        "canonical": canon,
                        "search_patterns": list(alias["search_patterns"])
                    })
                break

    # Mẫu 1: Dạng chuẩn đầy đủ: e.g. "11-NQ/ĐU", "01-NQ/ĐH", "69-KH/ĐU"
    pat1 = re.compile(r'(\d+)\s*[-–]\s*(NQ|KH|BC|QĐ|QD|CV|TB|KL|CT|TTr|CTr|HD|QĐi|QC)\s*/\s*([a-zA-ZđĐ]+)', re.IGNORECASE)
    for m in pat1.finditer(query):
        so_raw = m.group(1)
        loai_raw = m.group(2).upper()
        loai = "QĐ" if loai_raw == "QD" else loai_raw
        co_quan = m.group(3).upper()
        pad, raw = _normalize_num(so_raw)
        key = f"{loai}_{pad}_{co_quan}"
        if key not in seen_keys:
            seen_keys.add(key)
            patterns = [
                f"{pad}-{loai}/{co_quan}%",
                f"{raw}-{loai}/{co_quan}%",
                f"%{pad}-{loai}/{co_quan}%",
            ]
            results.append({
                "the_loai": loai,
                "so": pad,
                "co_quan": co_quan,
                "canonical": f"{pad}-{loai}/{co_quan}",
                "search_patterns": patterns
            })

    # Mẫu 2: Dạng rút gọn: e.g. "11-NQ", "69-KH"
    pat2 = re.compile(r'\b(\d+)\s*[-–]\s*(NQ|KH|BC|QĐ|QD|CV|TB|KL|CT|TTr|CTr|HD|QĐi|QC)\b', re.IGNORECASE)
    for m in pat2.finditer(query):
        so_raw = m.group(1)
        loai_raw = m.group(2).upper()
        loai = "QĐ" if loai_raw == "QD" else loai_raw
        pad, raw = _normalize_num(so_raw)
        key = f"{loai}_{pad}"
        if key not in seen_keys:
            seen_keys.add(key)
            patterns = [
                f"{pad}-{loai}%",
                f"{raw}-{loai}%",
                f"%{pad}-{loai}%",
            ]
            results.append({
                "the_loai": loai,
                "so": pad,
                "canonical": f"{pad}-{loai}",
                "search_patterns": patterns
            })

    # Mẫu 3: Dạng tên tiếng Việt: e.g. "Nghị quyết số 11", "Kế hoạch 69", "Báo cáo số 42"
    pat3 = re.compile(
        r'(nghị\s*quyết|kế\s*hoạch|báo\s*cáo|quyết\s*định|công\s*văn|thông\s*báo|kết\s*luận|chỉ\s*thị|tờ\s*trình|chương\s*trình|hướng\s*dẫn|quy\s*định|quy\s*chế)\s*(?:số\s*)?(\d+)',
        re.IGNORECASE
    )
    for m in pat3.finditer(query):
        ten_loai = re.sub(r'\s+', ' ', m.group(1).lower().strip())
        so_raw = m.group(2)
        loai = DOC_TYPE_MAP.get(ten_loai, "")
        if loai:
            pad, raw = _normalize_num(so_raw)
            key = f"{loai}_{pad}"
            if key not in seen_keys:
                seen_keys.add(key)
                patterns = [
                    f"{pad}-{loai}%",
                    f"{raw}-{loai}%",
                    f"%{pad}-{loai}%",
                ]
                results.append({
                    "the_loai": loai,
                    "so": pad,
                    "canonical": f"{pad}-{loai}",
                    "search_patterns": patterns
                })

    # Mẫu 4: Dạng viết tắt: e.g. "NQ 11", "NQ số 11", "KH69", "QĐ 05"
    pat4 = re.compile(r'\b(NQ|KH|BC|QĐ|QD|CV|TB|KL|CT|TTr|CTr|HD|QĐi|QC)\s*(?:số\s*)?(\d+)\b', re.IGNORECASE)
    for m in pat4.finditer(query):
        loai_raw = m.group(1).upper()
        loai = "QĐ" if loai_raw == "QD" else loai_raw
        so_raw = m.group(2)
        pad, raw = _normalize_num(so_raw)
        key = f"{loai}_{pad}"
        if key not in seen_keys:
            seen_keys.add(key)
            patterns = [
                f"{pad}-{loai}%",
                f"{raw}-{loai}%",
                f"%{pad}-{loai}%",
            ]
            results.append({
                "the_loai": loai,
                "so": pad,
                "canonical": f"{pad}-{loai}",
                "search_patterns": patterns
            })

    return results


def resolve_anaphora(query: str, history: Optional[List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    """
    Nếu câu hỏi chứa đại từ chỉ thị ('đó', 'này', 'trên'...),
    quét ngược lịch sử hội thoại gần nhất để tìm số hiệu văn bản đang bàn thảo.
    """
    if not history or not query:
        return []

    q_lower = query.lower()
    has_anaphora = any(m in q_lower for m in ANAPHORA_MARKERS)
    if not has_anaphora:
        return []

    # Quét ngược 4 lượt gần nhất (ưu tiên assistant messages vì trợ lý thường nhắc số hiệu chuẩn)
    recent_history = list(reversed(history[-4:]))
    for msg in recent_history:
        content = msg.get("content", "")
        # Tìm thực thể số hiệu trong nội dung tin nhắn cũ
        found_entities = extract_entities(content)
        if found_entities:
            logger.info(f"Đã giải quyết tham chiếu đại từ trong '{query}' -> Khôi phục: {[e['canonical'] for e in found_entities]}")
            return found_entities

    return []


def is_aggregate_query(query: str) -> bool:
    """Kiểm tra câu hỏi có phải dạng thống kê, đếm số lượng văn bản không."""
    if not query:
        return False
    q_lower = query.lower()
    for pat in STATS_PATTERNS:
        if re.search(pat, q_lower):
            return True
    return False


def analyze_query(query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Hàm phân tích toàn diện câu truy vấn:
    Trả về Dict:
    {
        "type": "DIRECT_HIT" | "AGGREGATE" | "THEMATIC",
        "entities": List[Dict],
        "resolved_from_anaphora": bool,
        "enriched_query": str,
        "primary_canonical": Optional[str]
    }
    """
    query_clean = (query or "").strip()
    
    # 1. Trích xuất thực thể trực tiếp từ câu hỏi
    direct_entities = extract_entities(query_clean)
    resolved_from_anaphora = False

    # 2. Nếu không có thực thể trực tiếp, thử giải quyết đại từ chỉ thị qua lịch sử
    entities = direct_entities
    if not entities and history:
        anaphora_entities = resolve_anaphora(query_clean, history)
        if anaphora_entities:
            entities = anaphora_entities
            resolved_from_anaphora = True

    # 3. Phân loại định tuyến
    if entities:
        canonical_str = " ".join(e["canonical"] for e in entities)
        enriched = f"{canonical_str} {query_clean}"
        return {
            "type": "DIRECT_HIT",
            "entities": entities,
            "resolved_from_anaphora": resolved_from_anaphora,
            "enriched_query": enriched,
            "primary_canonical": entities[0]["canonical"]
        }

    if is_aggregate_query(query_clean):
        return {
            "type": "AGGREGATE",
            "entities": [],
            "resolved_from_anaphora": False,
            "enriched_query": query_clean,
            "primary_canonical": None
        }

    return {
        "type": "THEMATIC",
        "entities": [],
        "resolved_from_anaphora": False,
        "enriched_query": query_clean,
        "primary_canonical": None
    }
