# -*- coding: utf-8 -*-
"""
Package scripts: Bộ công cụ tự động hóa văn thư và thẩm định văn bản Đảng
Văn phòng Đảng uỷ xã Công Hải - HD 05-HD/VPTW.
"""

from .export_docx import (
    PartyDocumentBuilder,
    export_party_document,
    parse_markdown_runs,
    set_cell_margins,
    remove_table_borders,
    add_horizontal_line,
)

__all__ = [
    "PartyDocumentBuilder",
    "export_party_document",
    "parse_markdown_runs",
    "set_cell_margins",
    "remove_table_borders",
    "add_horizontal_line",
]
