#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/ai_connector.py
======================
Bộ kết nối DeepSeek API chuyên sâu dành cho Văn phòng Đảng uỷ xã Công Hải.
Hỗ trợ:
- Gọi API chuẩn OpenAI-compatible (`https://api.deepseek.com/chat/completions`).
- Tự động bóc tách và sửa chữa cú pháp JSON đầu ra (JSON Repair).
- Nhiệt độ thấp (0.1) chống bịa đặt (Anti-Hallucination).
- Xử lý timeout và thử lại tự động (Retry).
- Báo lỗi rõ ràng khi chưa nhập API key hoặc API quá tải.
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Union

import httpx

from server.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_REASONER_MODEL,
)

logger = logging.getLogger("ai_connector")
logging.basicConfig(level=logging.INFO)


def extract_clean_json(text: str) -> str:
    """
    Bóc tách chuỗi JSON sạch từ phản hồi của LLM (loại bỏ thẻ suy luận <think>...</think> của DeepSeek-R1,
    markdown block ```json ... ```, khoảng trắng thừa hoặc văn bản giải thích ngoài lề).
    """
    text = text.strip()

    # 0. Loại bỏ khối suy luận <think>...</think> của mô hình Reasoning (DeepSeek-R1)
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()

    # 1. Bóc tách khỏi khối markdown ```json ... ``` hoặc ``` ... ```
    md_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if md_match:
        text = md_match.group(1).strip()

    # 2. Tìm điểm bắt đầu { và kết thúc } hoặc [ và ]
    start_brace = text.find("{")
    start_bracket = text.find("[")

    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = text.rfind("}")
        if end_brace != -1:
            text = text[start_brace : end_brace + 1]
    elif start_bracket != -1:
        end_bracket = text.rfind("]")
        if end_bracket != -1:
            text = text[start_bracket : end_bracket + 1]

    # 3. Sửa lỗi trailing commas phổ biến của LLM (ví dụ: {"a": 1, })
    text = re.sub(r",\s*([\}\]])", r"\1", text)

    return text


def auto_close_json(text: str) -> str:
    """Tự động đóng dấu ngoặc kép, ngoặc nhọn, ngoặc vuông nếu chuỗi JSON bị ngắt giữa chừng."""
    in_string = False
    escape = False
    stack = []
    
    for char in text:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in ("{", "["):
                stack.append("}" if char == "{" else "]")
            elif char in ("}", "]"):
                if stack and stack[-1] == char:
                    stack.pop()
    
    fixed = text
    if in_string:
        fixed += '"'
    while stack:
        fixed += stack.pop()
    return fixed


def repair_and_parse_json(text: str) -> Union[Dict[str, Any], List[Any]]:
    """Cố gắng phân tích chuỗi JSON, tự động sửa các lỗi cú pháp thông thường và đóng ngoặc thiếu."""
    clean_text = extract_clean_json(text)
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as err:
        logger.warning(f"Lần 1 decode JSON thất bại ({err}), tiến hành sửa sâu...")

        # Thử sửa dấu nháy đơn thành dấu nháy kép cho JSON keys
        fixed = re.sub(r"([{,]\s*)'([a-zA-Z0-9_]+)'\s*:", r'\1"\2":', clean_text)
        # Sửa các ký tự xuống dòng chưa được escape trong chuỗi
        fixed = re.sub(r"(?<!\\)\n", r"\\n", fixed)
        try:
            return json.loads(fixed)
        except Exception:
            pass

        # Thử tự động đóng ngoặc nếu bị cắt cụt
        try:
            closed = auto_close_json(fixed)
            return json.loads(closed)
        except Exception:
            raise ValueError(f"Không thể phân tích cú pháp phản hồi từ mô hình AI thành JSON: {text[:300]}...")


class DeepSeekClient:
    """Khách hàng kết nối AI chuyên trách (Hỗ trợ cả DeepSeek Cloud và Ollama Local)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 180.0,
    ):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = (base_url or DEEPSEEK_BASE_URL).rstrip("/")
        self.model = model or DEEPSEEK_MODEL
        self.timeout = timeout

    def is_local(self) -> bool:
        """Kiểm tra xem đang kết nối với máy chủ Local (Ollama/vLLM) hay Cloud."""
        url = self.base_url.lower()
        return "11434" in url or "localhost" in url or "127.0.0.1" in url

    def is_configured(self) -> bool:
        """Kiểm tra xem API key hoặc Local Ollama đã sẵn sàng hoạt động chưa."""
        if self.is_local():
            return True
        return bool(self.api_key and len(self.api_key.strip()) > 5 and not self.api_key.startswith("your_"))

    def switch_model(self, model_id: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Chuyển đổi mô hình đang chạy động ngay trong thời gian thực."""
        from server.config import OLLAMA_BASE_URL, CLOUD_DEEPSEEK_BASE_URL as CLOUD_URL, CLOUD_DEEPSEEK_API_KEY as CLOUD_KEY

        self.model = model_id
        if provider == "local" or (provider is None and ("qwen" in model_id or "r1" in model_id or "oss" in model_id or "ollama" in model_id)):
            self.base_url = OLLAMA_BASE_URL.rstrip("/")
            if not self.api_key:
                self.api_key = "ollama"
        elif provider == "cloud" or "deepseek-chat" in model_id:
            self.base_url = CLOUD_URL.rstrip("/")
            self.api_key = CLOUD_KEY

        logger.info(f"Đã chuyển đổi sang mô hình: {self.model} (Base URL: {self.base_url})")
        return {
            "model": self.model,
            "base_url": self.base_url,
            "is_local": self.is_local(),
        }

    async def call_chat_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 8192,
        json_mode: bool = True,
        use_reasoner: bool = False,
    ) -> Dict[str, Any]:
        """Gọi DeepSeek API bất đồng bộ (dùng trong FastAPI endpoint)."""
        if not self.is_configured():
            raise ValueError(
                "Máy chủ AI cục bộ (Ollama) chưa sẵn sàng hoặc chưa cấu hình DEEPSEEK_API_KEY. "
                "Vui lòng khởi động Ollama hoặc điền API key trong tệp .env."
            )

        auth_token = self.api_key.strip() if self.api_key else ("ollama" if self.is_local() else "")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        selected_model = DEEPSEEK_REASONER_MODEL if use_reasoner else self.model

        if self.is_local():
            # Sử dụng Ollama native API (/api/chat) để hỗ trợ đầy đủ options.num_ctx
            endpoint = self.base_url.replace("/v1", "").rstrip("/") + "/api/chat"
            model_lower = selected_model.lower()

            # Cân chỉnh giới hạn context thích ứng với bộ nhớ GPU (RTX 3060 12GB)
            # Đối với 14B: Cần 8.2GB VRAM cho weights, giới hạn an toàn tuyệt đối là 8,192 (KV cache 1.5GB)
            # Đối với 7B/8B: Cần 4.2GB VRAM cho weights, giới hạn an toàn là 16,384
            # Đối với 3B: Cần 1.8GB VRAM, có thể dùng tới 32,768
            if "14b" in model_lower or "20b" in model_lower:
                max_model_ctx = 8192
                pred_tokens = min(3072, max_tokens)
            elif "7b" in model_lower or "8b" in model_lower:
                max_model_ctx = 16384
                pred_tokens = min(4096, max_tokens)
            else:
                max_model_ctx = 32768
                pred_tokens = max_tokens

            # Đảm bảo tổng độ dài văn bản đầu vào không làm tràn context window
            max_input_chars = int((max_model_ctx - pred_tokens - 512) * 3.0)

            processed_messages = []
            for m in messages:
                content = m.get("content", "")
                if len(content) > max_input_chars:
                    half = max_input_chars // 2
                    content = (
                        content[:half]
                        + "\n\n... [Văn phòng Đảng uỷ: Nội dung giữa đã được lược bớt để đảm bảo dung lượng xử lý] ...\n\n"
                        + content[-half:]
                    )
                processed_messages.append({"role": m.get("role", "user"), "content": content})

            total_chars = sum(len(m.get("content", "")) for m in processed_messages)
            estimated_input_tokens = int(total_chars / 3.2)
            needed_ctx = min(max_model_ctx, max(4096, estimated_input_tokens + pred_tokens + 256))

            payload = {
                "model": selected_model,
                "messages": processed_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": needed_ctx,
                    "num_predict": pred_tokens,
                },
            }
            # Đối với Qwen thì hỗ trợ format: json, riêng DeepSeek-R1 thì không truyền format: json để không chặn <think>
            if json_mode and "r1" not in selected_model.lower():
                payload["format"] = "json"
        else:
            endpoint = f"{self.base_url}/chat/completions"
            payload = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode and not use_reasoner:
                payload["response_format"] = {"type": "json_object"}

        max_retries = 3
        last_error = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.post(endpoint, headers=headers, json=payload)
                except httpx.TimeoutException:
                    logger.warning(f"Quá thời gian kết nối AI ({self.timeout}s). Lần {attempt}/{max_retries}...")
                    last_error = "Quá thời gian chờ máy chủ AI (Timeout)."
                    await asyncio.sleep(2 * attempt)
                    continue
                except httpx.HTTPError as ex:
                    last_error = f"Lỗi mạng khi kết nối máy chủ AI: {ex}"
                    await asyncio.sleep(2 * attempt)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    if self.is_local() and "message" in data:
                        raw_content = data.get("message", {}).get("content", "") or ""
                        finish_reason = data.get("done_reason", "stop")
                        usage = {
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                        }
                    else:
                        choice = data["choices"][0]
                        raw_content = choice["message"]["content"] or ""
                        finish_reason = choice.get("finish_reason")
                        usage = data.get("usage", {})

                    if json_mode:
                        try:
                            parsed_data = repair_and_parse_json(raw_content)
                            return {
                                "success": True,
                                "data": parsed_data,
                                "raw_content": raw_content,
                                "model": selected_model,
                                "usage": usage,
                            }
                        except Exception as parse_err:
                            if finish_reason == "length":
                                provider_name = f"mô hình AI cục bộ ({selected_model})" if self.is_local() else "DeepSeek"
                                raise RuntimeError(
                                    f"Văn bản gửi kèm quá dài khiến {provider_name} chưa kịp hoàn tất toàn bộ nội dung JSON. "
                                    "Đồng chí vui lòng gửi lại lệnh hoặc gửi từng tệp để Chuyên viên Ảo thẩm định sâu hơn."
                                )
                            raise parse_err

                    return {
                        "success": True,
                        "content": raw_content,
                        "model": selected_model,
                        "usage": usage,
                    }

                if response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"DeepSeek API trả mã {response.status_code}. Thử lại lần {attempt}/{max_retries}...")
                    last_error = f"Máy chủ DeepSeek đang bận ({response.status_code})."
                    await asyncio.sleep(2 * attempt)
                    continue

                # Lỗi không thể thử lại
                if response.status_code == 401:
                    raise RuntimeError("DEEPSEEK_API_KEY không hợp lệ. Vui lòng kiểm tra lại key trong tệp .env.")
                if response.status_code == 402:
                    raise RuntimeError("Tài khoản DeepSeek đã hết số dư. Vui lòng nạp thêm tiền tại platform.deepseek.com.")
                raise RuntimeError(f"DeepSeek API trả mã lỗi {response.status_code}: {response.text[:300]}")

        raise RuntimeError(f"Không thể kết nối với DeepSeek sau {max_retries} lần thử: {last_error}")

    def call_chat_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        json_mode: bool = True,
        use_reasoner: bool = False,
    ) -> Dict[str, Any]:
        """Gọi DeepSeek API đồng bộ (dùng trong test script hoặc command line)."""
        import asyncio

        return asyncio.run(
            self.call_chat_async(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                use_reasoner=use_reasoner,
            )
        )


# Singleton client dùng chung
default_ai_client = DeepSeekClient()
