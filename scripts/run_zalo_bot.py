# -*- coding: utf-8 -*-
"""
scripts/run_zalo_bot.py
=======================
Runner lắng nghe tin nhắn Zalo Bot qua cơ chế getUpdates (Long Polling).
Thích hợp chạy thử nghiệm trực tiếp trên máy tính cá nhân (localhost)
mà không cần mở port mạng hay cấu hình Webhook domain.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
import requests

# Thêm đường dẫn gốc dự án vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from server.config import ZALO_API_TOKEN
from server.logger import get_logger
from server.routers.zalo_webhook import process_zalo_event

logger = get_logger("zalo_polling")


async def main():
    if not ZALO_API_TOKEN:
        print("[!] LỖI: Chưa cấu hình ZALO_API_TOKEN trong tệp .env.")
        sys.exit(1)

    print("=" * 60)
    print("🤖 CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI - ZALO BOT")
    print("🚀 Chế độ: Long Polling (Chạy trực tiếp trên Localhost)")
    print("=" * 60)

    # 1. Gỡ Webhook cũ để tránh xung đột với getUpdates
    delete_url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/deleteWebhook"
    try:
        res = requests.post(delete_url, timeout=10)
        logger.info(f"Kết quả gỡ Webhook cũ: {res.text}")
    except Exception as ex:
        logger.warning(f"Lỗi khi gỡ Webhook cũ: {ex}")

    get_updates_url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/getUpdates"

    print("✅ Đang sẵn sàng lắng nghe tin nhắn từ Zalo... (Nhấn Ctrl + C để dừng)\n")

    while True:
        try:
            # Chạy request trong thread pool để không block asyncio event loop
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(get_updates_url, json={"timeout": 25}, timeout=30),
            )

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and data.get("ok") and data.get("result"):
                    update = data["result"]
                    # Xử lý sự kiện qua quy trình webhook chuẩn
                    await process_zalo_event(update)
            elif resp.status_code != 200:
                logger.warning(f"Zalo getUpdates HTTP {resp.status_code}: {resp.text}")
                await asyncio.sleep(2)

            await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print("\nĐã dừng Zalo Bot.")
            break
        except Exception as ex:
            if "Read timed out" not in str(ex):
                logger.error(f"Lỗi vòng lặp Polling: {ex}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
