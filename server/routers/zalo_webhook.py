# -*- coding: utf-8 -*-
"""
server/routers/zalo_webhook.py
==============================
Webhook tiếp nhận và xử lý tin nhắn, tệp đính kèm từ Zalo Bot Platform.
Điều phối trực tiếp vào server.chat_engine và tự động nạp/tải tệp lên Google Drive.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, unquote, urlparse

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from server import chat_engine
from server.config import (
    ADMIN_ZALO_IDS,
    BASE_DIR,
    GDRIVE_FOLDER_URL,
    ZALO_WEBHOOK_SECRET,
)
from server.logger import get_logger
from server.router import route_incoming_file
from server.services.gdrive_service import upload_to_gdrive
from server.services.zalo_api import (
    download_file_from_url,
    send_message,
    send_typing_action,
)

logger = get_logger("zalo_webhook")

router = APIRouter(prefix="/webhook", tags=["zalo"])


def _extract_local_file_path(download_url: str) -> Optional[Path]:
    """Phục hồi đường dẫn file cục bộ từ URL download của hệ thống."""
    try:
        parsed = urlparse(download_url)
        qs = parse_qs(parsed.query)
        rel_path = qs.get("file_path", [""])[0]
        if rel_path:
            clean_rel = unquote(rel_path).lstrip("/\\")
            full_path = (BASE_DIR / clean_rel).resolve()
            if full_path.exists():
                return full_path
    except Exception as ex:
        logger.warning(f"Lỗi phân giải đường dẫn từ URL '{download_url}': {ex}")
    return None


async def process_zalo_event(payload: Dict[str, Any]) -> None:
    """Xử lý sự kiện Zalo trong BackgroundTasks để không nghẽn phản hồi HTTP webhook."""
    try:
        event_name = payload.get("event_name", "")
        message_data = payload.get("message", payload)

        # 1. Trích xuất chat_id (ID hội thoại)
        chat_id = None
        if message_data.get("chat", {}).get("id"):
            chat_id = message_data["chat"]["id"]
        elif payload.get("sender", {}).get("id"):
            chat_id = payload["sender"]["id"]
        elif message_data.get("from", {}).get("id"):
            chat_id = message_data["from"]["id"]
        elif payload.get("sender_id"):
            chat_id = payload["sender_id"]
        elif payload.get("user_id"):
            chat_id = payload["user_id"]

        # 2. Trích xuất sender_id (người gửi cụ thể)
        sender_id = None
        if payload.get("sender", {}).get("id"):
            sender_id = payload["sender"]["id"]
        elif message_data.get("from", {}).get("id"):
            sender_id = message_data["from"]["id"]
        elif payload.get("sender_id"):
            sender_id = payload["sender_id"]
        elif payload.get("user_id"):
            sender_id = payload["user_id"]
        if not sender_id:
            sender_id = chat_id

        if not chat_id:
            logger.warning("Không tìm thấy chat_id trong payload Zalo.")
            return

        from_info = message_data.get("from", {})
        if from_info.get("is_bot", False):
            return

        display_name = from_info.get("display_name", "Đồng chí")
        session_id = f"zalo_{chat_id}"

        # 3. Xử lý khi người dùng gửi TỆP (user_send_file, message.file.received)
        is_file_event = event_name in ["user_send_file", "message.file.received"]
        attachments = message_data.get("attachments", [])

        if is_file_event or (attachments and attachments[0].get("type") in ["file", "document"]):
            file_payload = attachments[0].get("payload", {}) if attachments else {}
            file_url = file_payload.get("url")
            file_name = file_payload.get("name") or f"van_ban_{int(time.time())}.docx"

            if file_url:
                send_message(chat_id, f"📥 Đang tiếp nhận và phân tích tệp: **{file_name}**...")
                send_typing_action(chat_id)

                tmp_dir = Path(tempfile.mkdtemp())
                tmp_file = tmp_dir / Path(file_name).name

                try:
                    if download_file_from_url(file_url, str(tmp_file)):
                        # Phân luồng văn bản và bóc tách nội dung
                        routing = route_incoming_file(str(tmp_file))
                        if not routing.get("full_text", "").strip():
                            send_message(
                                chat_id,
                                f"⚠️ Đã nhận tệp **{file_name}** nhưng không trích xuất được văn bản (có thể là bản quét PDF không có lớp chữ).",
                            )
                            return

                        # Gắn tệp vào phiên chat hiện tại của người dùng Zalo
                        sid, att = chat_engine.add_attachment(session_id, routing)

                        # Tải tệp lên Google Drive để lưu trữ đồng bộ
                        gdrive_upload = upload_to_gdrive(routing.get("saved_path", str(tmp_file)), filename=file_name)

                        category_label = att.get("category_label", "Văn bản")
                        suggested_wf = att.get("suggested_workflow", "")
                        wf_title = chat_engine.WORKFLOWS.get(suggested_wf, suggested_wf)

                        msg_lines = [
                            f"✅ Đã tiếp nhận tệp: **{file_name}**",
                            f"📌 Thể loại: **{category_label}**",
                            f"⚙️ Gợi ý nghiệp vụ: **{wf_title}**",
                        ]

                        if gdrive_upload.get("success"):
                            msg_lines.append(f"🔗 Đã lưu trên Google Drive: {gdrive_upload.get('file_url')}")
                        elif GDRIVE_FOLDER_URL:
                            msg_lines.append(f"📁 Thư mục Google Drive cơ quan: {GDRIVE_FOLDER_URL}")

                        msg_lines.extend([
                            "",
                            "Đồng chí hãy nhập lệnh chỉ đạo (ví dụ: *'Giao việc'*, *'Soạn thông báo kết luận'*, *'Thẩm định'*, hoặc gõ yêu cầu cụ thể) để tôi xử lý ngay.",
                        ])

                        send_message(chat_id, "\n".join(msg_lines))
                    else:
                        send_message(chat_id, f"❌ Không thể tải tệp **{file_name}** từ máy chủ Zalo.")
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            return

        # 4. Xử lý tin nhắn CHỮ (văn bản hỏi đáp hoặc điều khiển nghiệp vụ)
        text = message_data.get("text", "").strip()
        if not text:
            return

        logger.info(f"[Zalo] Tin nhắn từ {display_name} ({chat_id}): {text[:60]}")
        send_typing_action(chat_id)

        # Chuyển vào chat_engine chính của Chuyên viên ảo
        chat_res = await chat_engine.handle_chat(session_id=session_id, message=text)
        reply_text = chat_res.get("reply", "")
        files_created = chat_res.get("files", [])
        actions = chat_res.get("actions", [])

        # 5. Nếu hệ thống đã sinh file Word (Duyệt xong văn bản): Upload lên Google Drive
        gdrive_links = []
        if files_created:
            for f in files_created:
                f_name = f.get("name", "")
                f_url = f.get("url", "")
                local_path = _extract_local_file_path(f_url)
                if local_path and local_path.exists():
                    up_res = upload_to_gdrive(str(local_path), filename=f_name)
                    link = up_res.get("file_url") or GDRIVE_FOLDER_URL
                    gdrive_links.append({"name": f_name, "link": link, "server_link": up_res.get("server_link")})

        # Định dạng câu trả lời hoàn chỉnh
        full_reply_parts = [reply_text]

        if gdrive_links:
            full_reply_parts.append("\n📁 **TỆP DỰ THẢO TRÊN GOOGLE DRIVE:**")
            for item in gdrive_links:
                full_reply_parts.append(f"• **{item['name']}**\n  🔗 Link Google Drive: {item['link']}")
                if item.get("server_link"):
                    full_reply_parts.append(f"  ⬇️ Link tải dự phòng: {item['server_link']}")

        # Nếu có hành động chờ duyệt (Human-in-the-Loop)
        if actions and not files_created:
            full_reply_parts.extend([
                "",
                "👉 *Đồng chí có thể gõ:* **'Duyệt'** *(xuất Word)*, **'Huỷ'** *(bỏ dự thảo)*, hoặc gõ chỉ đạo chỉnh sửa trực tiếp.",
            ])

        full_reply_parts.append("\n🤖 *Trợ lý Chuyên viên ảo — VP Đảng uỷ xã Công Hải*")

        send_message(chat_id, "\n".join(full_reply_parts))

    except Exception as ex:
        logger.exception(f"Lỗi xử lý sự kiện Zalo: {ex}")


@router.get("/zalo")
async def zalo_webhook_get():
    """Endpoint xác thực webhook (Health check)."""
    return {"status": "ok", "service": "Zalo Bot Webhook", "timestamp": int(time.time())}


@router.post("/zalo")
async def zalo_webhook_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_bot_api_secret_token: Optional[str] = Header(None, alias="X-Bot-Api-Secret-Token"),
):
    """
    Tiếp nhận Webhook từ Zalo Bot Platform.
    Kiểm tra Secret Token và đẩy việc xử lý vào BackgroundTasks.
    """
    try:
        # Kiểm tra token bảo mật nếu có cấu hình
        if ZALO_WEBHOOK_SECRET and x_bot_api_secret_token:
            if x_bot_api_secret_token != ZALO_WEBHOOK_SECRET:
                logger.warning("Secret token Zalo Webhook không khớp.")
                return JSONResponse(status_code=403, content={"status": "forbidden", "message": "Invalid secret token"})

        payload = await request.json()
        background_tasks.add_task(process_zalo_event, payload)
        return {"status": "received"}
    except Exception as ex:
        logger.error(f"Lỗi tiếp nhận payload webhook: {ex}")
        return JSONResponse(status_code=400, content={"status": "error", "message": str(ex)})
