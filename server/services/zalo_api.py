# -*- coding: utf-8 -*-
"""
server/services/zalo_api.py
===========================
Wrapper cho Zalo Bot Platform API.
Hỗ trợ gửi tin nhắn, typing action, làm sạch định dạng Markdown và tải tệp từ Zalo.
"""

import re
import requests
from typing import Any, Dict, List, Optional
from server.config import ZALO_API_TOKEN
from server.logger import get_logger

logger = get_logger("zalo_api")


def clean_markdown_for_zalo(text: str) -> str:
    """Chuyển đổi Markdown chuẩn sang định dạng phù hợp hiển thị trên Zalo."""
    if not text:
        return ""

    # 1. Bảo vệ URL: Mã hoá dấu '_' thành '%5F' để Zalo Markdown không nhận nhầm thành cú pháp in nghiêng (_italic_) rồi xoá mất dấu gạch dưới!
    def encode_url_underscores(match):
        url = match.group(0)
        return url.replace('_', '%5F')

    text = re.sub(r'https?://[^\s\)\]]+', encode_url_underscores, text)

    # 2. Chuyển đổi Markdown Link [text](url) -> text: url
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\1: \2', text)

    # 3. Loại bỏ code inline `code` -> code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 3. Loại bỏ code block ```code```
    text = re.sub(r'```[a-zA-Z]*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)

    # 4. Làm sạch heading #, ##, ### ở đầu dòng
    def replace_heading(match):
        heading_text = match.group(2).strip()
        return f"\n🔹 {heading_text.upper()}\n"

    text = re.sub(r'^(#+)\s*(.*)$', replace_heading, text, flags=re.MULTILINE)

    return text.strip()


def _split_message(text: str, max_len: int = 1900) -> List[str]:
    """Chia tin nhắn dài thành nhiều phần theo dòng để không vượt quá giới hạn Zalo (2000 ký tự)."""
    lines = text.split("\n")
    parts = []
    current: List[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_len and current:
            parts.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        parts.append("\n".join(current))

    return parts


def send_single_message(chat_id: str, text: str) -> Optional[Dict[str, Any]]:
    """Gửi một tin nhắn đơn qua Zalo Bot API."""
    if not ZALO_API_TOKEN:
        logger.error("ZALO_API_TOKEN chưa được cấu hình.")
        return None

    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        res_json = response.json()
        if not res_json.get("ok"):
            logger.warning(f"Zalo API gửi tin nhắn không thành công: {res_json}")
        return res_json
    except Exception as ex:
        logger.error(f"Lỗi gửi tin nhắn Zalo tới {chat_id}: {ex}")
        return None


def send_message(chat_id: str, text: str) -> Optional[Dict[str, Any]]:
    """
    Gửi tin nhắn văn bản qua Zalo Bot API.
    Tự động làm sạch Markdown và chia nhỏ tin nhắn nếu dài hơn 1900 ký tự.
    """
    if not text:
        return None

    cleaned_text = clean_markdown_for_zalo(text)
    if len(cleaned_text) <= 1900:
        return send_single_message(chat_id, cleaned_text)

    parts = _split_message(cleaned_text, max_len=1900)
    last_res = None
    for i, part in enumerate(parts):
        last_res = send_single_message(chat_id, part)
        logger.info(f"Đã gửi phần {i + 1}/{len(parts)} ({len(part)} ký tự) tới {chat_id}")
    return last_res


def send_typing_action(chat_id: str) -> None:
    """Gửi trạng thái đang soạn tin (typing action)."""
    if not ZALO_API_TOKEN:
        return
    try:
        url = f"https://bot-api.zaloplatforms.com/bot{ZALO_API_TOKEN}/sendChatAction"
        requests.post(
            url,
            json={"chat_id": str(chat_id), "action": "typing"},
            timeout=5,
        )
    except Exception:
        pass


def download_file_from_url(url: str, dest_path: str, timeout: int = 30) -> bool:
    """Tải tệp từ URL (máy chủ Zalo) về đường dẫn cục bộ."""
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
            return True
        logger.warning(f"Tải tệp từ URL thất bại, HTTP status: {response.status_code}")
    except Exception as ex:
        logger.error(f"Lỗi tải tệp từ {url}: {ex}")
    return False
