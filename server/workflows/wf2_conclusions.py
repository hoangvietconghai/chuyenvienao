#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/workflows/wf2_conclusions.py
===================================
Quy trình WF2: Thông báo Kết luận Họp Thường trực Đảng uỷ.
1. Nhận ghi chép / biên bản họp giao ban.
2. Gọi DeepSeek API bóc tách theo nguyên tắc 5 RÕ.
3. Trả về bảng 5 RÕ và cảnh báo để cán bộ duyệt (Human-in-the-Loop).
4. Xuất file Word Thông báo Kết luận (-TB/ĐU).
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.export_docx import export_party_document
from server.ai_connector import default_ai_client
from server.config import VAN_BAN_DU_THAO_DIR
from server.prompts.wf2_thong_bao_ket_luan import get_wf2_messages


async def analyze_meeting_notes(meeting_notes: str, meeting_title: str = "Họp giao ban Thường trực") -> Dict[str, Any]:
    """Bóc tách ý kiến cuộc họp bằng DeepSeek theo nguyên tắc 5 RÕ."""
    messages = get_wf2_messages(meeting_notes, meeting_title)
    result = await default_ai_client.call_chat_async(messages, temperature=0.1, json_mode=True)
    return result["data"]


def generate_meeting_conclusion_docx(
    document_payload: Dict[str, Any], output_path: Optional[str] = None
) -> str:
    """Xuất file Word Thông báo Kết luận họp Thường trực."""
    if not output_path:
        out_dir = VAN_BAN_DU_THAO_DIR / "Thong_bao"
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(out_dir / f"TB_ket_luan_hop_TTDU_{timestamp}.docx")

    saved_path = export_party_document(document_payload, output_path)
    return saved_path
