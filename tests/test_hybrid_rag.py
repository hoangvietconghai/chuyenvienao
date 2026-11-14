# -*- coding: utf-8 -*-
"""
tests/test_hybrid_rag.py
========================
Bộ kiểm thử tự động toàn diện hệ thống True Hybrid RAG (6 Kịch bản Nghiệm thu):
1. Test Case 1: Hỏi đích danh số hiệu văn bản (Nghị quyết 11)
2. Test Case 2: Hỏi tiếp nối giải quyết tham chiếu đại từ (Tóm tắt Nghị quyết đó)
3. Test Case 3: Truy vấn ngữ nghĩa theo chủ đề (Chuyển đổi số & KHCN)
4. Test Case 4: Truy vấn thống kê số lượng văn bản trong kho
5. Test Case 5: Hỏi văn bản không tồn tại trong kho (Nghị quyết 99)
6. Test Case 6: Tra cứu theo dạng viết tắt (NQ 11)
"""

import asyncio
import sys
import unittest
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.services.query_analyzer import analyze_query, extract_entities
from server.services.rag_service import retrieve_direct_hit, retrieve_hybrid_context, check_and_get_aggregate_stats
from server.chat_engine import handle_chat, get_session


class TestHybridRAG(unittest.TestCase):

    def test_01_direct_hit_resolution(self):
        """Test Case 1: Hỏi đích danh số hiệu văn bản -> Bắt trúng NQ 11 ở vị trí số 1."""
        query = "Nghị quyết số 11 của Đảng uỷ xã nói về nội dung gì"
        analysis = analyze_query(query)
        self.assertEqual(analysis["type"], "DIRECT_HIT")
        self.assertEqual(analysis["primary_canonical"], "11-NQ")

        rag_res = retrieve_direct_hit(analysis["entities"])
        self.assertGreater(rag_res["total_slots"], 0)
        top_citation = rag_res["citations"][0]
        self.assertEqual(top_citation["so_hieu"], "11-NQ/ĐU")
        self.assertIn("cải cách hành chính", top_citation["trich_yeu"].lower())
        print("  [PASSED] Test 1: Direct Hit NQ 11 thành công 100%")

    def test_02_anaphora_multi_turn(self):
        """Test Case 2: Hỏi tiếp nối 'đó' -> Phục hồi được NQ 11 từ lịch sử hội thoại."""
        history = [
            {"role": "user", "content": "Nghị quyết số 11 của Đảng uỷ xã nói về nội dung gì"},
            {"role": "assistant", "content": "Nghị quyết số 11-NQ/ĐU (ngày 08/06/2026) của Đảng uỷ xã về cải cách hành chính..."}
        ]
        follow_up_query = "Tóm tắt nội dung của Nghị quyết đó"
        analysis = analyze_query(follow_up_query, history=history)

        self.assertEqual(analysis["type"], "DIRECT_HIT")
        self.assertTrue(analysis["resolved_from_anaphora"])
        self.assertIn("11-NQ", analysis["primary_canonical"])

        rag_res = retrieve_direct_hit(analysis["entities"])
        self.assertGreater(rag_res["total_slots"], 0)
        self.assertEqual(rag_res["citations"][0]["so_hieu"], "11-NQ/ĐU")
        print("  [PASSED] Test 2: Giải quyết đại từ 'đó' -> Khôi phục chính xác 11-NQ/ĐU")

    def test_03_thematic_semantic_retrieval(self):
        """Test Case 3: Hỏi ngữ nghĩa chuyển đổi số -> 02-NQ/ĐU (chuyển đổi số) xếp hạng #1."""
        query = "Đảng uỷ xã có chủ trương gì về đột phá chuyển đổi số và khoa học công nghệ?"
        analysis = analyze_query(query)
        self.assertEqual(analysis["type"], "THEMATIC")

        rag_res = retrieve_hybrid_context(analysis["enriched_query"], max_slots=4)
        self.assertGreater(rag_res["total_slots"], 0)
        top_doc = rag_res["citations"][0]
        self.assertEqual(top_doc["so_hieu"], "02-NQ/ĐU")
        self.assertIn("chuyển đổi số", top_doc["trich_yeu"].lower())
        print("  [PASSED] Test 3: Semantic Hybrid RAG kéo đúng 02-NQ/ĐU lên vị trí #1")

    def test_04_aggregate_query(self):
        """Test Case 4: Truy vấn thống kê số lượng văn bản trong kho."""
        query = "Trong kho hiện tại có bao nhiêu nghị quyết?"
        analysis = analyze_query(query)
        self.assertEqual(analysis["type"], "AGGREGATE")

        stats = check_and_get_aggregate_stats(query)
        self.assertIsNotNone(stats)
        self.assertTrue(stats.get("is_stats_query"))
        self.assertEqual(stats.get("total_docs"), 16)
        print("  [PASSED] Test 4: Thống kê chính xác 16 văn bản trong kho")

    def test_05_document_not_found(self):
        """Test Case 5: Hỏi văn bản không tồn tại trong kho (NQ 99)."""
        query = "Nội dung Nghị quyết 99 là gì?"
        analysis = analyze_query(query)
        self.assertEqual(analysis["type"], "DIRECT_HIT")

        rag_res = retrieve_direct_hit(analysis["entities"])
        self.assertEqual(rag_res["total_slots"], 0)
        self.assertIn("99-NQ", rag_res["not_found"])
        print("  [PASSED] Test 5: Bắt chính xác trạng thái chưa lưu trữ NQ 99")

    def test_06_abbreviation_query(self):
        """Test Case 6: Tra cứu theo dạng viết tắt 'NQ 11 nói gì'."""
        query = "NQ 11 nói gì"
        analysis = analyze_query(query)
        self.assertEqual(analysis["type"], "DIRECT_HIT")
        self.assertEqual(analysis["primary_canonical"], "11-NQ")

        rag_res = retrieve_direct_hit(analysis["entities"])
        self.assertGreater(rag_res["total_slots"], 0)
        self.assertEqual(rag_res["citations"][0]["so_hieu"], "11-NQ/ĐU")
        print("  [PASSED] Test 6: Tra cứu viết tắt 'NQ 11' thành công 100%")

    def test_07_congress_named_alias(self):
        """Test Case 7: Tra cứu Nghị quyết Đại hội (không ghi số) -> Nhận diện trúng 01-NQ/ĐH."""
        query = "Nghị quyết Đại hội Đảng bộ xã gồm bao nhiêu chỉ tiêu, bao nhiêu nhiệm vụ trọng tâm"
        analysis = analyze_query(query)
        self.assertEqual(analysis["type"], "DIRECT_HIT")
        self.assertEqual(analysis["primary_canonical"], "01-NQ/ĐH")

        rag_res = retrieve_direct_hit(analysis["entities"])
        self.assertGreater(rag_res["total_slots"], 0)
        self.assertEqual(rag_res["citations"][0]["so_hieu"], "01-NQ/ĐH")
        self.assertIn("nhiệm kỳ 2025 - 2030", rag_res["citations"][0]["trich_yeu"])
        print("  [PASSED] Test 7: Nhận diện danh xưng 'Nghị quyết Đại hội' -> DIRECT_HIT 01-NQ/ĐH thành công 100%")


if __name__ == "__main__":
    print("=" * 60)
    print("BẮT ĐẦU CHẠY BỘ KIỂM THỬ TRUE HYBRID RAG (6 KỊCH BẢN)")
    print("=" * 60)
    unittest.main(verbosity=2)
