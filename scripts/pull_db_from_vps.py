#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/pull_db_from_vps.py
===========================
Công cụ đồng bộ an toàn 1 chiều (VPS -> Local) CSDL SQLite WAL:
- Tải tệp CSDL thực tế đang chạy trên VPS (/opt/chuyenvienao/data/chuyen_vien_ao.db)
  về máy tính cục bộ để phân tích, báo cáo hoặc sao lưu.
- Tự động sao lưu tệp CSDL cục bộ hiện tại vào thư mục backups/ trước khi ghi đè.
- Tuyệt đối tuân thủ nguyên tắc: VPS là nguồn dữ liệu duy nhất (Single Source of Truth),
  chỉ kéo dữ liệu từ VPS về máy tính, KHÔNG đẩy đè dữ liệu máy tính lên VPS.

Chạy:
    python scripts/pull_db_from_vps.py
"""

import getpass
import os
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import paramiko
except ImportError:
    print("Đang cài đặt thư viện paramiko...")
    os.system(f"{sys.executable} -m pip install paramiko")
    import paramiko

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = BASE_DIR / "data" / "chuyen_vien_ao.db"
LOCAL_BACKUP_DIR = BASE_DIR / "backups"

VPS_IP = "45.119.82.227"
VPS_PORT = 22
VPS_USER = "root"
REMOTE_DB_PATH = "/opt/chuyenvienao/data/chuyen_vien_ao.db"


def main():
    print("=" * 76)
    print("   📥 ĐỒNG BỘ CSDL TỪ MÁY CHỦ VPS VỀ MÁY CỤC BỘ (PULL DATABASE)            ")
    print("=" * 76)
    print(f"🔹 Nguồn (VPS Production): {VPS_USER}@{VPS_IP}:{REMOTE_DB_PATH}")
    print(f"🔹 Đích (Local): {LOCAL_DB_PATH}")
    print("=" * 76)

    password = getpass.getpass(f"🔑 Nhập mật khẩu SSH cho {VPS_USER}@{VPS_IP}: ")
    if not password:
        print("❌ Chưa nhập mật khẩu. Huỷ tác vụ.")
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print("\n>> [1/3] Đang kết nối tới máy chủ VPS qua SSH/SFTP...")
        ssh.connect(
            hostname=VPS_IP,
            port=VPS_PORT,
            username=VPS_USER,
            password=password,
            timeout=15,
            banner_timeout=15,
        )
        sftp = ssh.open_sftp()
        print("  ✓ Kết nối SFTP thành công.")

        # Kiểm tra file trên VPS
        try:
            r_stat = sftp.stat(REMOTE_DB_PATH)
            size_mb = r_stat.st_size / (1024 * 1024)
            print(f"  ✓ Tìm thấy CSDL VPS: {size_mb:.2f} MB")
        except FileNotFoundError:
            print(f"❌ Không tìm thấy tệp {REMOTE_DB_PATH} trên VPS!")
            return

        # Sao lưu CSDL local hiện tại trước khi ghi đè
        print("\n>> [2/3] Sao lưu CSDL cục bộ hiện tại...")
        LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if LOCAL_DB_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = LOCAL_BACKUP_DIR / f"local_db_before_pull_{timestamp}.db"
            import shutil
            shutil.copy2(LOCAL_DB_PATH, backup_file)
            print(f"  ✓ Đã sao lưu bản cục bộ cũ vào: {backup_file.name}")

        # Tải tệp từ VPS về Local
        print("\n>> [3/3] Đang tải CSDL từ VPS về máy tính...")
        LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        sftp.get(REMOTE_DB_PATH, str(LOCAL_DB_PATH))
        
        # Cũng tải file wal nếu có
        try:
            sftp.get(REMOTE_DB_PATH + "-wal", str(LOCAL_DB_PATH) + "-wal")
        except Exception:
            pass

        print(f"\n{'=' * 76}")
        print(f"  ✅ ĐỒNG BỘ THÀNH CÔNG!                                              ")
        print(f"🔹 Toàn bộ dữ liệu thực tế từ VPS đã được nạp an toàn vào máy cục bộ.")
        print(f"🔹 Đường dẫn CSDL: {LOCAL_DB_PATH}")
        print(f"{'=' * 76}")

    except Exception as ex:
        print(f"\n❌ Lỗi trong quá trình đồng bộ: {ex}")
    finally:
        ssh.close()


if __name__ == "__main__":
    main()

