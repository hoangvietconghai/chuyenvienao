#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run.py
======
Trình khởi chạy chính thức Hệ thống Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải.
- Đảm bảo thư mục làm việc đúng gốc dự án
- Tự động mở trình duyệt web sau khi server sẵn sàng
- Khởi chạy FastAPI qua Uvicorn
"""

import os
import sys
import time
import threading
import webbrowser

# Đảm bảo mã hoá UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Chuyển CWD về thư mục chứa file run.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)


def open_browser():
    """Mở trình duyệt web sau 1.5 giây khi server đã lắng nghe cổng 8000."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[THÀNH CÔNG] Đang mở trình duyệt tại: {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    print("=" * 72)
    print("   🏛️ HỆ THỐNG CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI")
    print("   Mô hình chính quyền 3 cấp (Trung ương - Tỉnh Khánh Hoà - Xã Công Hải)")
    print("   Chuẩn thể thức Hướng dẫn số 05-HD/VPTW ngày 12/01/2026")
    print("=" * 72)
    print("\nĐang khởi động máy chủ Web Local tại http://127.0.0.1:8000 ...")
    print("Để dừng hệ thống, nhấn phím tổ hợp: Ctrl + C\n")

    # Mở trình duyệt song song
    threading.Thread(target=open_browser, daemon=True).start()

    # Chạy uvicorn
    import uvicorn
    uvicorn.run("server.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
