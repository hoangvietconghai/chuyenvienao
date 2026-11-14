#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/log_guinhan.py
======================
(Bản sao công cụ giám sát nhật ký gửi - nhận tại thư mục scripts/)
"""
import sys
from pathlib import Path

ROOT_SCRIPT = Path(__file__).resolve().parent.parent / "log_guinhan.py"
if ROOT_SCRIPT.exists():
    with open(ROOT_SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code)
