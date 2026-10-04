#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/workflows/wf3_dispatch.py
================================
Quy trình WF3: Tiếp nhận văn bản Tỉnh uỷ/UBND tỉnh -> Công văn Giao việc (-CV/ĐU).
1. Nhận văn bản cấp trên.
2. Gọi DeepSeek API bóc tách mục tiêu và phân luồng Dynamic Routing.
3. Trả về bảng phân công nhiệm vụ và cảnh báo để cán bộ duyệt (Human-in-the-Loop).
4. Xuất file Word Công văn giao việc (-CV/ĐU).
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.export_docx import export_party_document
from server.ai_connector import default_ai_client
from server.config import VAN_BAN_DU_THAO_DIR
from server.prompts.wf3_giao_viec import get_wf3_messages


async def analyze_provincial_directive(doc_text: str) -> Dict[str, Any]:
    """Phân tích văn bản chỉ đạo của Tỉnh uỷ và phân luồng 5 khối cơ quan xã."""
    messages = get_wf3_messages(doc_text)
    result = await default_ai_client.call_chat_async(messages, temperature=0.1, json_mode=True)
    return result["data"]


def generate_dispatch_docx(
    document_payload: Dict[str, Any], output_path: Optional[str] = None
) -> str:
    """Xuất file Word Công văn giao việc của Ban Thường vụ Đảng uỷ."""
    if not output_path:
        out_dir = VAN_BAN_DU_THAO_DIR / "Cong_van"
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(out_dir / f"CV_giao_viec_{timestamp}.docx")

    saved_path = export_party_document(document_payload, output_path)
    return saved_path
