#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/backup_to_gdrive.py
===========================
Công cụ dòng lệnh và Cron Job Sao lưu CSDL SQLite Đêm lên Google Drive
dành cho Văn phòng Đảng uỷ xã Công Hải.

Cách dùng:
  python scripts/backup_to_gdrive.py
  python scripts/backup_to_gdrive.py --no-gdrive
  python scripts/backup_to_gdrive.py --retention 45

Trên Linux VPS (/opt/chuyenvienao):
  0 1 * * * /opt/chuyenvienao/venv/bin/python /opt/chuyenvienao/scripts/backup_to_gdrive.py >> /opt/chuyenvienao/logs/backup.log 2>&1
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import server modules
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from server.logger import get_logger
from server.services.backup_service import perform_full_backup

logger = get_logger("cli_backup")


def main():
    parser = argparse.ArgumentParser(
        description="Sao lưu Cơ sở Dữ liệu Đêm Tự động lên Google Drive - Văn phòng Đảng uỷ xã Công Hải"
    )
    parser.add_argument(
        "--no-gdrive",
        action="store_true",
        help="Chỉ sao lưu nén cục bộ, không tải lên Google Drive",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=30,
        help="Số ngày / số bản sao lưu tối đa cần lưu trữ (mặc định: 30)",
    )
    parser.add_argument(
        "--folder-id",
        type=str,
        default=None,
        help="Google Drive Folder ID tuỳ chọn để lưu bản sao",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Xuất kết quả dưới dạng chuỗi JSON cho automation scripts",
    )

    args = parser.parse_args()

    upload_gdrive = not args.no_gdrive
    print("=" * 70)
    print("  HỆ THỐNG SAO LƯU CƠ SỞ DỮ LIỆU ĐÊM TỰ ĐỘNG (OFFSITE BACKUP)")
    print("  VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI - TỈNH KHÁNH HOÀ")
    print("=" * 70)
    print(f"• Tải lên Google Drive: {'BẬT' if upload_gdrive else 'TẮT'}")
    print(f"• Chính sách duy trì: {args.retention} ngày")
    print("• Đang chụp snapshot CSDL SQLite WAL...")

    try:
        res = perform_full_backup(
            upload_gdrive=upload_gdrive,
            folder_id=args.folder_id,
            retention_days=args.retention,
        )

        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("\n✓ SAO LƯU THÀNH CÔNG!")
            print(f"  - Tệp nén: {res['filename']}")
            print(f"  - Đường dẫn: {res['local_path']}")
            print(f"  - Dung lượng: {res['size_mb']} MB ({res['size_bytes']:,} bytes)")
            print(f"  - Mã SHA256: {res['sha256']}")
            print(f"  - Đã dọn dẹp: {res['cleaned_count']} bản sao lưu cũ")
            if res.get("gdrive"):
                g = res["gdrive"]
                if g.get("success"):
                    print(f"  - Google Drive URL: {g.get('file_url')}")
                else:
                    print(f"  - Google Drive: {g.get('message') or g.get('error') or 'Chưa hoàn tất'}")
            print(f"  - Thời gian xử lý: {res['elapsed_seconds']} giây")
        sys.exit(0)
    except Exception as ex:
        logger.exception("Lỗi trong quá trình sao lưu CSDL")
        print(f"\n❌ LỖI SAO LƯU: {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
