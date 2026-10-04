#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/router.py
================
Module điều phối và phân luồng văn bản đến tự động.
- Tiếp nhận tệp upload (PDF, DOCX, DOC, TXT)
- Bóc tách nội dung sơ bộ qua doc_reader
- Tự động di chuyển / lưu trữ vào đúng thư mục nghiệp vụ van_ban_den/2026/...
- Gợi ý kích hoạt quy trình nghiệp vụ phù hợp (WF1, WF2, WF3, WF4)
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.doc_reader import extract_document_text
from server.config import (
    FOLDER_BAO_CAO_CO_SO,
    FOLDER_BIEN_BAN_HOP,
    FOLDER_CAP_TREN,
    FOLDER_DU_THAO_CQ,
    VAN_BAN_DEN_DIR,
)

WORKFLOW_MAP = {
    "wf1_tong_hop_bao_cao": {
        "name": "Tổng hợp Báo cáo Tuần / Tháng",
        "description": "Bóc tách các báo cáo cơ sở thành Báo cáo Tuần của Văn phòng Đảng uỷ",
        "folder": FOLDER_BAO_CAO_CO_SO,
        "output_type": "BC",
    },
    "wf2_thong_bao_ket_luan": {
        "name": "Thông báo Kết luận Họp Thường trực",
        "description": "Bóc tách ghi chép cuộc họp theo nguyên tắc 5 RÕ và sinh dự thảo Thông báo Kết luận",
        "folder": FOLDER_BIEN_BAN_HOP,
        "output_type": "TB",
    },
    "wf3_giao_viec": {
        "name": "Văn bản cấp trên -> Công văn Giao việc",
        "description": "Phân tích văn bản Tỉnh uỷ/UBND tỉnh, phân luồng cho 5 khối cơ quan cấp xã",
        "folder": FOLDER_CAP_TREN,
        "output_type": "CV",
    },
    "wf4_tham_dinh": {
        "name": "Thẩm định Dự thảo & Lấy ý kiến BTV",
        "description": "Thẩm định 2 tầng (Kỹ thuật và Nội dung) và xuất hồ sơ lấy ý kiến BTV",
        "folder": FOLDER_DU_THAO_CQ,
        "output_type": "BC_and_du_thao",
    },
}


def route_incoming_file(
    source_file_path: str,
    target_category: Optional[str] = None,
    custom_subfolder: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tiếp nhận file, đọc text, phân loại và lưu trữ vào kho văn bản đến.
    """
    if not os.path.exists(source_file_path):
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {source_file_path}")

    # 1. Trích xuất text và siêu dữ liệu
    doc_data = extract_document_text(source_file_path)
    metadata = doc_data.get("metadata", {})

    # 2. Xác định danh mục đích
    category = target_category or metadata.get("suggested_type", "cap_tren")
    suggested_wf = metadata.get("suggested_wf", "wf3_giao_viec")

    if category == "cap_tren":
        target_dir = FOLDER_CAP_TREN
    elif category == "du_thao_co_quan":
        target_dir = FOLDER_DU_THAO_CQ
    elif category == "bao_cao_co_so":
        target_dir = FOLDER_BAO_CAO_CO_SO
        if custom_subfolder:
            target_dir = target_dir / custom_subfolder
    elif category == "bien_ban_hop":
        target_dir = FOLDER_BIEN_BAN_HOP
    else:
        target_dir = FOLDER_CAP_TREN

    target_dir.mkdir(parents=True, exist_ok=True)

    # 3. Sao chép file vào thư mục đích
    file_name = os.path.basename(source_file_path)
    dest_path = target_dir / file_name

    # Tránh ghi đè nếu trùng tên
    counter = 1
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    while dest_path.exists() and os.path.abspath(source_file_path) != os.path.abspath(dest_path):
        dest_path = target_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    if os.path.abspath(source_file_path) != os.path.abspath(dest_path):
        shutil.copy2(source_file_path, dest_path)

    wf_info = WORKFLOW_MAP.get(suggested_wf, WORKFLOW_MAP["wf3_giao_viec"])

    return {
        "success": True,
        "saved_path": str(dest_path),
        "file_name": dest_path.name,
        "file_size": os.path.getsize(dest_path),
        "category": category,
        "suggested_workflow": suggested_wf,
        "workflow_info": wf_info,
        "metadata": metadata,
        "text_preview": doc_data["text"][:800],
        "full_text": doc_data["text"],
        "char_count": len(doc_data["text"]),
    }
