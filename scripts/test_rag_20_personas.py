#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/test_rag_20_personas.py
===============================
Bộ kiểm thử 20 tình huống thực tế đa vai trò, đa tầng lớp nhận thức,
đa ngữ cảnh và đa cách diễn đạt cho Hệ thống Truy xuất RAG Đảng uỷ xã Công Hải.
"""

import os
import sys
import types
import logging
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Stub nhẹ các thư viện tùy chọn nếu chạy ngoài virtualenv
if "dotenv" not in sys.modules:
    m_dotenv = types.ModuleType("dotenv")
    m_dotenv.load_dotenv = lambda *a, **kw: None
    sys.modules["dotenv"] = m_dotenv

if "httpx" not in sys.modules:
    m_httpx = types.ModuleType("httpx")
    sys.modules["httpx"] = m_httpx

from server.services.query_analyzer import analyze_query
from server.services import db_service, rag_service
from scripts.doc_reader import check_secret_document


def _run_rag_pipeline(query: str, history=None):
    """Mô phỏng chính xác luồng định tuyến & truy xuất RAG trong chat_engine.py."""
    analysis = analyze_query(query, history=history or [])
    qtype = analysis["type"]
    result_text = ""
    citations = []

    if qtype == "DIRECT_HIT":
        res = rag_service.retrieve_direct_hit(analysis["entities"])
        if res.get("context_text"):
            result_text = res["context_text"]
            citations = res.get("citations", [])
        elif res.get("not_found"):
            hyb = rag_service.retrieve_hybrid_context(analysis["enriched_query"], max_slots=6)
            result_text = hyb.get("context_text", "")
            citations = hyb.get("citations", [])
    elif qtype == "AGGREGATE":
        stats = rag_service.check_and_get_aggregate_stats(query)
        result_text = (stats or {}).get("stats_text", "")
    else:
        hyb = rag_service.retrieve_hybrid_context(analysis["enriched_query"], max_slots=6)
        result_text = hyb.get("context_text", "")
        citations = hyb.get("citations", [])

    return analysis, result_text, citations


def run_20_tests():
    tests = [
        # 1. Bí thư Đảng uỷ: ngắn gọn, định hướng lớn
        {
            "id": 1,
            "role": "Bí thư Đảng uỷ (Hỏi ngắn gọn chiến lược)",
            "query": "Đảng uỷ xã đã ban hành các văn bản nào về đột phá phát triển giáo dục và đào tạo",
            "expect_type": "THEMATIC",
            "expect_any": ["38-KH/ĐU", "08-NQ/ĐU", "161a-BC/ĐU"],
        },
        # 2. Phó Chánh VPĐU: hỏi dài chuẩn hành chính, kèm số hiệu cấp trên TW & TU
        {
            "id": 2,
            "role": "Phó Chánh VPĐU (Hỏi dài kèm số hiệu TW/TU)",
            "query": "cho tôi biết đảng uỷ xã công hải đã ban văn bản lãnh đạo quán triệt, tuyên truyền và triển khai thực hiện Nghị quyết số 71-NQ/TW, ngày 22/8/2025 của Bộ Chính trị về đột phá phát triển giáo dục và đào tạo và Nghị quyết số 01-NQ/TU, ngày 03/10/2025 của Ban Chấp hành Đảng bộ tỉnh về Chiến lược phát triển bền vững giáo dục và đào tạo tỉnh Khánh Hòa đến năm 2035, tầm nhìn đến năm 2045",
            "expect_type": "THEMATIC",
            "expect_any": ["38-KH/ĐU", "08-NQ/ĐU", "161a-BC/ĐU"],
        },
        # 3. Chuyên viên mới: hỏi đích danh 1 văn bản xã
        {
            "id": 3,
            "role": "Chuyên viên mới (Hỏi đích danh văn bản xã)",
            "query": "Nội dung chính của Nghị quyết 08-NQ/ĐU là gì?",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["08-NQ/ĐU"],
        },
        # 4. Cán bộ thôn vùng ĐBDTTS: gõ điện thoại không dấu tiếng Việt
        {
            "id": 4,
            "role": "Cán bộ thôn (Gõ không dấu trên điện thoại)",
            "query": "nghi quyet 08 ve giao duc xa cong hai",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["08-NQ/ĐU"],
        },
        # 5. Cán bộ không nhớ số hiệu, hỏi bằng từ đồng nghĩa/tự nhiên
        {
            "id": 5,
            "role": "Cán bộ cơ sở (Hỏi tự nhiên bằng từ đồng nghĩa)",
            "query": "Xã mình có chủ trương gì nâng cao chất lượng dạy học và trường học không?",
            "expect_type": "THEMATIC",
            "expect_any": ["08-NQ/ĐU", "38-KH/ĐU", "giáo dục"],
        },
        # 6. Bí thư Chi bộ trường học: hỏi về sắp xếp chi bộ trường học
        {
            "id": 6,
            "role": "Bí thư Chi bộ trường học (Hỏi chuyên đề tổ chức Đảng)",
            "query": "Việc sắp xếp, giải thể và thành lập mới các chi bộ trường học thực hiện theo đề án nào?",
            "expect_type": "THEMATIC",
            "expect_any": ["05-ĐA/ĐU", "giáo dục công lập"],
        },
        # 7. Công chức UBND xã: hỏi Nghị quyết chuyển đổi số (Named Alias)
        {
            "id": 7,
            "role": "Công chức UBND xã (Hỏi Named Alias CĐS)",
            "query": "Đảng uỷ xã đã có nghị quyết nào về chuyển đổi số?",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["02-NQ/ĐU"],
        },
        # 8. Thành viên BCĐ 57: hỏi Kế hoạch làm sạch dữ liệu ĐV (Named Alias)
        {
            "id": 8,
            "role": "Thành viên BCĐ 57 (Hỏi Named Alias Dữ liệu ĐV)",
            "query": "Kế hoạch rà soát, làm sạch dữ liệu đảng viên là văn bản nào?",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["144-KH/ĐU", "dữ liệu"],
        },
        # 9. Phó Chủ tịch HĐND xã: hỏi chỉ tiêu Đại hội (Named Alias)
        {
            "id": 9,
            "role": "Phó Chủ tịch HĐND (Hỏi chỉ tiêu Nghị quyết Đại hội)",
            "query": "Chỉ tiêu Nghị quyết Đại hội Đảng bộ xã lần thứ I về tăng trưởng kinh tế và hộ nghèo đến 2030",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["01-NQ/ĐH"],
        },
        # 10. Cán bộ UBKT Đảng uỷ: hỏi kiểm tra giám sát theo NQ 05-NQ/TW
        {
            "id": 10,
            "role": "Cán bộ UBKT (Hỏi văn bản triển khai NQ TW kiểm tra)",
            "query": "Đảng uỷ xã ban hành văn bản nào triển khai thực hiện Nghị quyết số 05-NQ/TW về công tác kiểm tra, giám sát?",
            "expect_type": "THEMATIC",
            "expect_any": ["84-KH/ĐU", "kiểm tra, giám sát"],
        },
        # 11. Hỏi nối tiếp đại từ (Anaphora Resolution)
        {
            "id": 11,
            "role": "Hội thoại nối tiếp (Dùng đại từ 'nghị quyết đó')",
            "query": "Mục tiêu cụ thể của nghị quyết đó đến năm 2030 là gì?",
            "history": [
                {"role": "user", "content": "Cho tôi xem Nghị quyết 08-NQ/ĐU"},
                {"role": "assistant", "content": "Nghị quyết số 08-NQ/ĐU ngày 16/04/2026 về nâng cao chất lượng giáo dục và đào tạo."}
            ],
            "expect_type": "DIRECT_HIT",
            "expect_any": ["08-NQ/ĐU"],
        },
        # 12. Văn thư tổng hợp: hỏi thống kê số lượng văn bản (AGGREGATE)
        {
            "id": 12,
            "role": "Văn thư (Hỏi thống kê số lượng văn bản)",
            "query": "Thống kê tổng số lượng nghị quyết và kế hoạch hiện có trong kho văn bản",
            "expect_type": "AGGREGATE",
            "expect_any": ["Thống kê", "tổng", "Nghị quyết", "văn bản"],
        },
        # 13. Cán bộ gõ sai dấu thanh kiểu cũ (òa, ủy, úy)
        {
            "id": 13,
            "role": "Cán bộ gõ chính tả kiểu cũ (ủy, hòa)",
            "query": "Nghị quyết của Đảng ủy xã về phát triển kinh tế xã hội năm 2026",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["05-NQ/ĐU"],
        },
        # 14. Chuyên viên hỏi Báo cáo 185-BC/ĐU (trong Sổ đăng ký so_van_ban)
        {
            "id": 14,
            "role": "Chuyên viên tổng hợp (Tra cứu Sổ bộ so_van_ban)",
            "query": "Báo cáo tình hình thực hiện nhiệm vụ 9 tháng đầu năm 2026 số 185-BC/ĐU",
            "expect_type": "DIRECT_HIT",
            "expect_any": ["185-BC/ĐU"],
        },
        # 15. Cán bộ tổ chức: hỏi Đề án sắp xếp chi bộ thôn
        {
            "id": 15,
            "role": "Cán bộ Ban Xây dựng Đảng (Hỏi sắp xếp chi bộ thôn)",
            "query": "Đề án sắp xếp kết thúc hoạt động chi bộ thôn cũ và thành lập chi bộ thôn mới",
            "expect_type": "THEMATIC",
            "expect_any": ["03-ĐA/ĐU", "04-ĐA/ĐU", "chi bộ thôn"],
        },
        # 16. Cán bộ MTTQ/Dân vận: hỏi không dấu + từ khoá thực tiễn
        {
            "id": 16,
            "role": "Cán bộ Mặt trận (Hỏi không dấu về phong trào/dân vận)",
            "query": "ke hoach thuc hien chuong trinh hanh dong 11-CTr/TU phat trien kinh te xa hoi",
            "expect_type": "THEMATIC",
            "expect_any": ["66-KH/ĐU", "129-KH/ĐU", "11-CTr/TU"],
        },
        # 17. Kiểm tra Gatekeeper Độ mật 1 (TỐI MẬT)
        {
            "id": 17,
            "role": "Bảo mật Gatekeeper (Văn bản TỐI MẬT)",
            "gatekeeper_text": "ĐẢNG CỘNG SẢN VIỆT NAM\nTỐI MẬT\nBáo cáo tình hình an ninh chính trị nội bộ...",
            "expect_secret": True,
        },
        # 18. Kiểm tra Gatekeeper Độ mật 2 (ĐỘ MẬT: MẬT)
        {
            "id": 18,
            "role": "Bảo mật Gatekeeper (Độ mật: MẬT)",
            "gatekeeper_text": "Số 12-CV/ĐU\nĐỘ MẬT: MẬT\nNội dung chỉ đạo tuyệt đối giữ bí mật...",
            "expect_secret": True,
        },
        # 19. Câu hỏi ngoài phạm vi kho (Anti-hallucination)
        {
            "id": 19,
            "role": "Người dân/Cán bộ (Hỏi ngoài phạm vi kho tri thức)",
            "query": "Quy định giá đền bù đất khu công nghiệp vũ trụ năm 2099 tại xã Công Hải",
            "expect_type": "THEMATIC",
            "expect_not_crash": True,
        },
        # 20. Kiểm tra chống trùng lặp số hiệu văn bản (Deduplication)
        {
            "id": 20,
            "role": "Kiểm tra kỹ thuật (Chống trùng lặp so_hieu_vb trong slots)",
            "query": "Kế hoạch quán triệt tuyên truyền nghị quyết 71-NQ/TW đột phá phát triển giáo dục đào tạo",
            "expect_type": "THEMATIC",
            "check_dedup": True,
        },
    ]

    passed = 0
    failed = 0

    print("=" * 80)
    print("CHẠY BỘ KIỂM THỬ 20 TÌNH HUỐNG ĐA VAI TRÒ & ĐA NGỮ CẢNH HỆ THỐNG RAG")
    print("=" * 80)

    for tc in tests:
        tid = tc["id"]
        role = tc["role"]

        if "gatekeeper_text" in tc:
            is_sec, msg = check_secret_document(tc["gatekeeper_text"])
            ok = (is_sec == tc["expect_secret"])
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] #{tid:02d} ({role}) -> Blocked={is_sec}")
            if ok:
                passed += 1
            else:
                failed += 1
            continue

        analysis, text, citations = _run_rag_pipeline(tc["query"], tc.get("history"))
        ok = True
        reasons = []

        if "expect_type" in tc and analysis["type"] != tc["expect_type"]:
            ok = False
            reasons.append(f"Type={analysis['type']} != {tc['expect_type']}")

        if "expect_any" in tc:
            combined = (text + " " + " ".join(c.get("so_hieu", "") for c in citations)).lower()
            if not any(kw.lower() in combined for kw in tc["expect_any"]):
                ok = False
                reasons.append(f"Không tìm thấy từ khoá kỳ vọng {tc['expect_any']}")

        if tc.get("check_dedup"):
            so_list = [c.get("so_hieu", "").strip().upper() for c in citations if c.get("so_hieu")]
            if len(so_list) != len(set(so_list)):
                ok = False
                reasons.append(f"Trùng số hiệu trong citations: {so_list}")

        status = "PASS" if ok else "FAIL"
        found_so = [c.get("so_hieu") for c in citations[:4]]
        print(f"[{status}] #{tid:02d} ({role}) | Type={analysis['type']} | Citations={found_so}")
        if not ok:
            print(f"       -> Lý do: {'; '.join(reasons)}")
            failed += 1
        else:
            passed += 1

    print("=" * 80)
    print(f"TỔNG KẾT: {passed}/20 ĐẠT | {failed}/20 THẤT BẠI")
    print("=" * 80)
    return failed == 0


if __name__ == "__main__":
    success = run_20_tests()
    sys.exit(0 if success else 1)
