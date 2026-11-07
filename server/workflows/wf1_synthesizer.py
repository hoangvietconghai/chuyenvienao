#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/workflows/wf1_synthesizer.py
===================================
Quy trình WF1: Tổng hợp Báo cáo Tuần của Văn phòng Đảng uỷ.
1. Nhận text từ các báo cáo ngành gửi về.
2. Gọi DeepSeek API với prompt chuyên biệt.
3. Trả về kết quả phân tích, cảnh báo số liệu bất thường để cán bộ duyệt (Human-in-the-Loop).
4. Xuất file Word chuẩn thể thức HD 05-HD/VPTW (-BC/VPĐU).
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.export_docx import export_party_document
from server.ai_connector import default_ai_client
from server.config import VAN_BAN_DU_THAO_DIR
from server.prompts.wf1_tong_hop_bao_cao import get_wf1_messages


async def analyze_weekly_reports(reports_text: str, week_number: str = "...") -> Dict[str, Any]:
    """Phân tích các báo cáo cơ sở bằng DeepSeek kết hợp dữ liệu thực chứng RAG."""
    messages = get_wf1_messages(reports_text, week_number)
    try:
        from server.services.rag_service import retrieve_hybrid_context
        query = f"báo cáo tuần {week_number} " + reports_text[:250]
        rag_res = retrieve_hybrid_context(query, max_slots=4)
        if rag_res.get("context_text"):
            messages.insert(1, {
                "role": "system",
                "content": f"Dữ liệu tra cứu thực chứng từ Kho văn bản cấp uỷ (RAG):\n{rag_res['context_text']}"
            })
    except Exception:
        pass

    result = await default_ai_client.call_chat_async(messages, temperature=0.1, json_mode=True)
    return result["data"]


def generate_weekly_report_docx(
    document_payload: Dict[str, Any], output_path: Optional[str] = None
) -> str:
    """Xuất file Word Báo cáo Tuần của Văn phòng Đảng uỷ."""
    if not output_path:
        out_dir = VAN_BAN_DU_THAO_DIR / "Bao_cao"
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(out_dir / f"BC_tong_hop_tuan_{timestamp}.docx")

    saved_path = export_party_document(document_payload, output_path)
    return saved_path
