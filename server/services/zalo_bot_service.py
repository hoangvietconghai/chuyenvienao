# -*- coding: utf-8 -*-
"""
server/services/zalo_bot_service.py
===================================
Quản lý vòng đời và phương thức kết nối Zalo Bot Platform:
- Tự động kiểm tra danh tính Bot (getMe).
- Thiết lập và duy trì Webhook trên VPS/Domain công khai.
- Chế độ Long Polling (getUpdates) tự động kích hoạt khi chạy Local hoặc khi Webhook chưa sẵn sàng.
- Tích hợp trực tiếp vào FastAPI startup event, loại bỏ hoàn toàn việc phải chạy script thủ công.
"""

import asyncio
import os
import requests
from typing import Any, Dict, Optional

from server.config import (
    SERVER_DOMAIN,
    SERVER_HOST,
    ZALO_API_TOKEN,
    ZALO_WEBHOOK_SECRET,
)
from server.logger import get_logger
from server.routers.zalo_webhook import process_zalo_event

logger = get_logger("zalo_bot_service")

# Biến cờ theo dõi trạng thái background polling task
_polling_task: Optional[asyncio.Task] = None
_is_polling_active: bool = False


def get_bot_info() -> Optional[Dict[str, Any]]:
    """Kiểm tra danh tính bot từ máy chủ Zalo."""
    if not ZALO_API_TOKEN:
        return None
    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/getMe"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("ok"):
            return data.get("result")
        logger.warning(f"Zalo getMe phản hồi lỗi: {data}")
    except Exception as ex:
        logger.error(f"Lỗi kết nối Zalo API getMe: {ex}")
    return None


def get_webhook_info() -> Optional[Dict[str, Any]]:
    """Lấy thông tin webhook hiện tại từ máy chủ Zalo."""
    if not ZALO_API_TOKEN:
        return None
    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/getWebhookInfo"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("ok"):
            return data.get("result")
    except Exception as ex:
        logger.error(f"Lỗi kiểm tra Zalo getWebhookInfo: {ex}")
    return None


def register_webhook(webhook_url: str, secret_token: str = "") -> bool:
    """Đăng ký URL Webhook với Zalo Bot Platform."""
    if not ZALO_API_TOKEN:
        return False
    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/setWebhook"
    payload = {"url": webhook_url}
    if secret_token:
        payload["secret_token"] = secret_token
    try:
        res = requests.post(url, json=payload, timeout=15)
        data = res.json()
        if data.get("ok"):
            logger.info(f"✅ Đăng ký Zalo Webhook thành công: {webhook_url}")
            return True
        logger.warning(f"Đăng ký Zalo Webhook thất bại: {data}")
    except Exception as ex:
        logger.error(f"Lỗi gọi setWebhook Zalo: {ex}")
    return False


def delete_webhook() -> bool:
    """Gỡ Webhook để chuyển sang chế độ Long Polling (getUpdates)."""
    if not ZALO_API_TOKEN:
        return False
    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/deleteWebhook"
    try:
        res = requests.post(url, timeout=10)
        data = res.json()
        if data.get("ok"):
            logger.info("Đã gỡ Webhook trên Zalo Platform.")
            return True
    except Exception as ex:
        logger.error(f"Lỗi khi gỡ Webhook: {ex}")
    return False


async def run_polling_loop():
    """Vòng lặp Long Polling lắng nghe tin nhắn từ Zalo Bot trong background."""
    global _is_polling_active
    _is_polling_active = True
    get_updates_url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/getUpdates"
    offset = 0

    logger.info("🚀 Zalo Bot Polling Worker đã bắt đầu lắng nghe tin nhắn...")

    # Gỡ Webhook trước để Zalo chuyển sự kiện sang hàng đợi getUpdates
    delete_webhook()

    def _fetch_updates(p):
        return requests.get(get_updates_url, params=p, timeout=25)

    while _is_polling_active:
        try:
            loop = asyncio.get_event_loop()
            params = {"timeout": 20, "limit": 10}
            if offset > 0:
                params["offset"] = offset

            resp = await loop.run_in_executor(None, _fetch_updates, dict(params))

            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    results = data.get("result", [])
                    if isinstance(results, dict):
                        results = [results]
                    if results:
                        logger.info(f"📩 Tiếp nhận {len(results)} sự kiện mới từ Zalo Bot!")
                    for item in results:
                        update_id = item.get("update_id")
                        if update_id:
                            offset = max(offset, update_id + 1)
                        # Đẩy xử lý sự kiện qua chat_engine
                        asyncio.create_task(process_zalo_event(item))
                elif data.get("error_code") != 408 and "timeout" not in str(data.get("description", "")).lower():
                    logger.warning(f"Zalo getUpdates phản hồi: {data}")
            elif resp.status_code != 200:
                logger.warning(f"Zalo getUpdates HTTP {resp.status_code}: {resp.text}")
                await asyncio.sleep(2)

            await asyncio.sleep(0.3)

        except asyncio.CancelledError:
            logger.info("Zalo Bot Polling Worker nhận lệnh dừng.")
            break
        except Exception as ex:
            if "Read timed out" not in str(ex):
                logger.error(f"Lỗi trong vòng lặp Polling Zalo: {ex}")
            await asyncio.sleep(2)

    _is_polling_active = False


async def init_zalo_bot():
    """Khởi tạo toàn diện Zalo Bot khi ứng dụng khởi động."""
    global _polling_task
    if not ZALO_API_TOKEN:
        logger.warning("ZALO_API_TOKEN chưa cấu hình trong .env. Zalo Bot tạm ngưng.")
        return

    bot_info = get_bot_info()
    if not bot_info:
        logger.error("❌ Không thể kết nối với Zalo Bot Platform (Token không hợp lệ hoặc lỗi mạng).")
        return

    bot_name = bot_info.get("display_name", "Zalo Bot")
    bot_id = bot_info.get("id", "")
    logger.info(f"🤖 Đã kết nối Zalo Bot: {bot_name} (ID: {bot_id})")

    # Mặc định sử dụng Long Polling (getUpdates) vì tính ổn định 100%,
    # hoàn toàn độc lập với cấu hình tên miền, tường lửa, F5 proxy và chứng chỉ SSL.
    # Chỉ bật Webhook khi cấu hình rõ ràng ZALO_MODE=webhook.
    zalo_mode = os.getenv("ZALO_MODE", "polling").lower()

    if zalo_mode == "webhook":
        target_webhook_url = os.getenv("ZALO_WEBHOOK_URL", "")
        if not target_webhook_url:
            if SERVER_DOMAIN and SERVER_DOMAIN.startswith("http"):
                target_webhook_url = f"{SERVER_DOMAIN.rstrip('/')}/webhook/zalo"
            else:
                target_webhook_url = f"http://{SERVER_HOST}/webhook/zalo"

        webhook_info = get_webhook_info()
        current_url = webhook_info.get("url", "") if webhook_info else ""

        if target_webhook_url and target_webhook_url != current_url:
            logger.info(f"Cập nhật Zalo Webhook tới: {target_webhook_url}")
            success = register_webhook(target_webhook_url, ZALO_WEBHOOK_SECRET)
            if not success:
                logger.warning("Đăng ký Webhook không thành công, tự động chuyển sang chế độ Long Polling dự phòng.")
                _polling_task = asyncio.create_task(run_polling_loop())
        elif current_url:
            logger.info(f"✅ Zalo Webhook đang hoạt động tại: {current_url}")
        else:
            logger.info("Chưa có Webhook URL công khai, kích hoạt Long Polling tự động.")
            _polling_task = asyncio.create_task(run_polling_loop())
    else:
        # Mặc định: Long Polling (Khuyên dùng, hoạt động tức thì mọi môi trường)
        logger.info("🚀 Kích hoạt Zalo Bot ở chế độ: LONG POLLING (getUpdates — Ổn định 100%, nhận tin tức thì).")
        _polling_task = asyncio.create_task(run_polling_loop())


def stop_zalo_bot():
    """Dừng background polling task nếu đang chạy."""
    global _polling_task, _is_polling_active
    _is_polling_active = False
    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
        logger.info("Đã gửi tín hiệu dừng Zalo Polling Task.")

