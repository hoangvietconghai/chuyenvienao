# -*- coding: utf-8 -*-
"""
server/services/backup_service.py
=================================
Dịch vụ Sao lưu Cơ sở Dữ liệu Đêm Tự động (Automated Offsite Backup Engine)
dành cho Văn phòng Đảng uỷ xã Công Hải.

Tính năng:
1. Snapshot an toàn 100% CSDL SQLite đang ở chế độ WAL bằng SQLite Online Backup API (không khoá bảng, không gây xung đột ghi).
2. Nén tệp sao lưu bằng Gzip (.db.gz) tiết kiệm 70-85% dung lượng đĩa và băng thông.
3. Tự động kiểm tra tính toàn vẹn dữ liệu bằng mã băm SHA256.
4. Tải tệp bản sao lên Google Drive (Offsite Cloud Storage).
5. Áp dụng chính sách duy trì (Retention Policy): Giữ 30 bản sao lưu gần nhất, tự động dọn dẹp các tệp quá hạn.
"""

import gzip
import hashlib
import os
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from server.config import (
    BACKUP_DIR,
    BASE_DIR,
    DATA_DIR,
    GDRIVE_BACKUP_FOLDER_ID,
)
from server.logger import get_logger
from server.services import gdrive_service

logger = get_logger("backup_service")
DB_FILE = DATA_DIR / "chuyen_vien_ao.db"


def compute_sha256(file_path: Path) -> str:
    """Tính mã băm SHA256 để xác thực tính toàn vẹn của tệp sao lưu."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_database_snapshot(dest_db_path: Path) -> Path:
    """
    Tạo bản chụp (snapshot) an toàn của SQLite CSDL đang chạy chế độ WAL.
    Sử dụng SQLite Online Backup API để đảm bảo không bị lỗi dữ liệu dở dang.
    """
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp CSDL nguồn: {DB_FILE}")

    dest_db_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_db_path.exists():
        dest_db_path.unlink()

    src_conn = sqlite3.connect(str(DB_FILE), timeout=30.0)
    dst_conn = sqlite3.connect(str(dest_db_path))

    try:
        # Sao chép theo từng khối 100 trang để không làm nghẽn tiến trình ghi của Web/Zalo
        src_conn.backup(dst_conn, pages=100)
    finally:
        dst_conn.close()
        src_conn.close()

    logger.info(f"Đã tạo snapshot SQLite WAL an toàn: {dest_db_path}")
    return dest_db_path


def compress_database_snapshot(db_path: Path) -> Path:
    """Nén tệp CSDL .db thành định dạng nén .db.gz và xoá file .db gốc để tiết kiệm dung lượng."""
    gz_path = db_path.with_suffix(".db.gz")
    with open(db_path, "rb") as f_in:
        with gzip.open(gz_path, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

    if db_path.exists():
        db_path.unlink()

    logger.info(f"Đã nén tệp CSDL sang Gzip: {gz_path}")
    return gz_path


def clean_old_backups(backup_dir: Path, retention_days: int = 30) -> int:
    """
    Chính sách duy trì (Retention Policy):
    Xoá các bản sao lưu cũ hơn `retention_days` ngày hoặc giữ lại tối đa `retention_days` bản mới nhất.
    """
    if not backup_dir.exists():
        return 0

    backup_files = sorted(
        backup_dir.glob("chuyen_vien_ao_backup_*.db.gz"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    deleted_count = 0
    now = time.time()
    max_age_seconds = retention_days * 86400

    for idx, p in enumerate(backup_files):
        # Giữ lại tối thiểu 7 bản mới nhất dù thời gian có thế nào
        if idx < 7:
            continue
        file_age = now - p.stat().st_mtime
        if idx >= retention_days or file_age > max_age_seconds:
            try:
                p.unlink()
                deleted_count += 1
                logger.info(f"Đã xoá bản sao lưu cũ theo chính sách duy trì: {p.name}")
            except Exception as del_err:
                logger.warning(f"Không thể xoá bản sao lưu {p.name}: {del_err}")

    return deleted_count


def perform_full_backup(
    upload_gdrive: bool = True,
    folder_id: Optional[str] = None,
    retention_days: int = 30,
) -> Dict[str, Any]:
    """
    Thực thi toàn bộ quy trình sao lưu CSDL:
    1. Tạo thư mục sao lưu cục bộ (backups/db_nightly/).
    2. Snapshot an toàn từ SQLite WAL.
    3. Nén Gzip (.db.gz).
    4. Kiểm tra mã SHA256.
    5. Tải lên Google Drive Offsite.
    6. Dọn dẹp bản sao lưu cũ.
    """
    start_time = time.time()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    temp_db_name = f"chuyen_vien_ao_backup_{timestamp_str}.db"
    temp_db_path = BACKUP_DIR / temp_db_name

    # 1. Tạo snapshot SQLite WAL
    create_database_snapshot(temp_db_path)

    # 2. Nén Gzip
    gz_path = compress_database_snapshot(temp_db_path)
    file_size_bytes = gz_path.stat().st_size
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    sha256_hash = compute_sha256(gz_path)

    # 3. Tải lên Google Drive
    gdrive_res = None
    target_folder = folder_id or GDRIVE_BACKUP_FOLDER_ID
    if upload_gdrive:
        try:
            gdrive_res = gdrive_service.upload_to_gdrive(
                file_path=str(gz_path),
                filename=gz_path.name,
                folder_id=target_folder,
            )
        except Exception as up_ex:
            logger.error(f"Lỗi khi tải bản sao lưu lên Google Drive: {up_ex}")
            gdrive_res = {"success": False, "error": str(up_ex)}

    # 4. Dọn dẹp bản sao lưu cũ
    cleaned_count = clean_old_backups(BACKUP_DIR, retention_days=retention_days)
    elapsed_seconds = round(time.time() - start_time, 2)

    result = {
        "success": True,
        "timestamp": timestamp_str,
        "filename": gz_path.name,
        "local_path": str(gz_path),
        "size_bytes": file_size_bytes,
        "size_mb": file_size_mb,
        "sha256": sha256_hash,
        "gdrive": gdrive_res,
        "cleaned_count": cleaned_count,
        "elapsed_seconds": elapsed_seconds,
    }

    logger.info(
        f"[BACKUP_SUCCESS] Tệp: {gz_path.name} | Dung lượng: {file_size_mb} MB | "
        f"SHA256: {sha256_hash[:12]}... | Thời gian: {elapsed_seconds}s | Google Drive: {gdrive_res.get('success') if gdrive_res else 'Bỏ qua'}"
    )
    return result
