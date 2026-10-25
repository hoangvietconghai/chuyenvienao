#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/logger.py
================
Cấu hình hệ thống ghi log tập trung cho Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải.
Ghi đồng thời ra console và tệp xoay vòng (RotatingFileHandler) tại logs/chuyen_vien_ao.log.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from server.config import DEBUG, LOGS_DIR

_INITIALIZED = False
LOG_FILE_PATH = LOGS_DIR / "chuyen_vien_ao.log"


def setup_logging(
    log_file: Optional[Path] = None,
    level: Optional[int] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Khởi tạo hệ thống logging: console + rotating file handler.
    An toàn khi gọi nhiều lần (idempotent).
    """
    global _INITIALIZED
    if _INITIALIZED:
        return

    if log_file is None:
        log_file = LOG_FILE_PATH

    log_file.parent.mkdir(parents=True, exist_ok=True)

    if level is None:
        level = logging.DEBUG if DEBUG else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Xoá các handler mặc định cũ để tránh duplicate log
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Rotating File Handler (UTF-8, 10MB x 5 backups)
    try:
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as exc:
        print(f"[CẢNH BÁO] Không thể khởi tạo tệp log xoay vòng tại {log_file}: {exc}", file=sys.stderr)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """
    Lấy logger theo tên module và tự động cấu hình nếu chưa khởi tạo.
    """
    if not _INITIALIZED:
        setup_logging()
    return logging.getLogger(name)


# Tự động nạp cấu hình khi module được import
setup_logging()
