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

from server.logger import get_logger

logger = get_logger("ai_connector")


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
    """
    Bộ điều phối AI đa tầng thông minh (Multi-Provider AI Orchestrator):
    - Động cơ chính (Primary Engine): Google Gemini (Gemini 3.5 Flash Lite / 2.5 Flash) — Siêu tốc, 1M context, miễn phí 500 RPD.
    - Động cơ dự phòng (Fallback Engine): DeepSeek Cloud (deepseek-chat / 671B) — Tự động kích hoạt khi Gemini chạm hạn ngạch hoặc quá tải.
    - Động cơ nội bộ (Local Offline Engine): Ollama Local (Qwen 2.5 / DeepSeek-R1) — Bảo mật 100% khi không có Internet.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 180.0,
    ):
        from server.config import (
            ACTIVE_PROVIDER,
            DEEPSEEK_API_KEY,
            DEEPSEEK_BASE_URL,
            DEEPSEEK_MODEL,
            DEEPSEEK_REASONER_MODEL,
            GEMINI_API_KEY,
            GEMINI_BASE_URL,
            DEFAULT_GEMINI_MODEL,
            CLOUD_DEEPSEEK_API_KEY,
            CLOUD_DEEPSEEK_BASE_URL,
            CLOUD_DEEPSEEK_MODEL,
            CLOUD_DEEPSEEK_REASONER_MODEL,
            OLLAMA_BASE_URL,
            DEFAULT_LOCAL_MODEL,
        )

        self.provider = ACTIVE_PROVIDER
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = (base_url or DEEPSEEK_BASE_URL).rstrip("/")
        self.model = model or DEEPSEEK_MODEL
        self.timeout = timeout

        # Cấu hình cụ thể cho từng nhà cung cấp
        self.gemini_key = GEMINI_API_KEY
        self.gemini_base_url = GEMINI_BASE_URL.rstrip("/")
        self.gemini_model = DEFAULT_GEMINI_MODEL

        self.deepseek_key = CLOUD_DEEPSEEK_API_KEY
        self.deepseek_base_url = CLOUD_DEEPSEEK_BASE_URL.rstrip("/")
        self.deepseek_model = CLOUD_DEEPSEEK_MODEL
        self.deepseek_reasoner_model = CLOUD_DEEPSEEK_REASONER_MODEL

        self.ollama_base_url = OLLAMA_BASE_URL.rstrip("/")
        self.ollama_model = DEFAULT_LOCAL_MODEL

    def _has_valid_key(self, key: Optional[str]) -> bool:
        """Kiểm tra tính hợp lệ của API Key."""
        return bool(key and len(key.strip()) > 5 and not key.strip().startswith("your_"))

    def is_local(self) -> bool:
        """Kiểm tra xem đang kết nối với máy chủ Local (Ollama/vLLM) hay Cloud."""
        url = self.base_url.lower()
        return self.provider == "local" or "11434" in url or "localhost" in url or "127.0.0.1" in url

    def is_gemini(self) -> bool:
        """Kiểm tra xem mô hình hiện tại có thuộc Google Gemini hay không."""
        return (
            self.provider == "gemini"
            or "gemini" in self.model.lower()
            or "generativelanguage" in self.base_url.lower()
        )

    def is_configured(self) -> bool:
        """Kiểm tra xem hệ thống đã có ít nhất một mô hình AI sẵn sàng (Gemini, DeepSeek hoặc Local Ollama)."""
        if self.is_local():
            return True
        if self.is_gemini():
            if self._has_valid_key(self.api_key or self.gemini_key):
                return True
            return self._has_valid_key(self.deepseek_key)
        # DeepSeek Cloud
        if self._has_valid_key(self.api_key or self.deepseek_key):
            return True
        return self._has_valid_key(self.gemini_key)

    def switch_model(self, model_id: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Chuyển đổi mô hình đang chạy động ngay trong thời gian thực."""
        from server.config import (
            OLLAMA_BASE_URL,
            CLOUD_DEEPSEEK_BASE_URL as CLOUD_URL,
            CLOUD_DEEPSEEK_API_KEY as CLOUD_KEY,
            GEMINI_BASE_URL,
            GEMINI_API_KEY,
        )

        self.model = model_id
        mid = model_id.lower()

        if provider == "gemini" or (provider is None and "gemini" in mid):
            self.provider = "gemini"
            self.base_url = GEMINI_BASE_URL.rstrip("/")
            self.api_key = GEMINI_API_KEY or self.gemini_key
        elif provider == "local" or (provider is None and ("qwen" in mid or "r1" in mid or "oss" in mid or "ollama" in mid)):
            self.provider = "local"
            self.base_url = OLLAMA_BASE_URL.rstrip("/")
            self.api_key = "ollama"
        else:
            self.provider = "cloud"
            self.base_url = CLOUD_URL.rstrip("/")
            self.api_key = CLOUD_KEY or self.deepseek_key

        logger.info(f"Đã chuyển đổi sang mô hình: {self.model} (Provider: {self.provider}, Base URL: {self.base_url})")
        return {
            "model": self.model,
            "provider": self.provider,
            "base_url": self.base_url,
            "is_local": self.is_local(),
            "is_gemini": self.is_gemini(),
        }

    async def _execute_openai_call(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> Tuple[str, Dict[str, Any], Optional[str]]:
        """Gửi request chuẩn OpenAI-compatible tới endpoint `/chat/completions`."""
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = await client.post(endpoint, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            choice = data["choices"][0]
            raw_content = choice["message"]["content"] or ""
            finish_reason = choice.get("finish_reason")
            usage = data.get("usage", {})
            return raw_content, usage, finish_reason

        raise httpx.HTTPStatusError(
            message=f"HTTP {response.status_code}: {response.text[:300]}",
            request=response.request,
            response=response,
        )

    async def call_chat_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 8192,
        json_mode: bool = True,
        use_reasoner: bool = False,
    ) -> Dict[str, Any]:
        """
        Gọi AI API bất đồng bộ với cơ chế Failover Động cơ Kép (Dual-Engine):
        1. Ưu tiên gọi mô hình đã chọn (mặc định Gemini Flash Lite).
        2. Nếu gặp lỗi quá tải / chạm hạn ngạch (429, 503, timeout), tự động chuyển sang Động cơ dự phòng (DeepSeek Cloud).
        """
        if not self.is_configured():
            raise ValueError(
                "Chưa cấu hình API Key cho Chuyên viên Ảo. "
                "Đồng chí vui lòng điền GEMINI_API_KEY hoặc DEEPSEEK_API_KEY trong tệp .env."
            )

        selected_model = (
            self.deepseek_reasoner_model if (use_reasoner and not self.is_gemini()) else self.model
        )

        # ----------------------------------------------------------------------
        # LUỒNG 1: MÔ HÌNH CỤC BỘ LOCAL (OLLAMA / GPU RTX 3060)
        # ----------------------------------------------------------------------
        if self.is_local():
            endpoint = self.base_url.replace("/v1", "").rstrip("/") + "/api/chat"
            model_lower = selected_model.lower()

            if "14b" in model_lower or "20b" in model_lower:
                max_model_ctx = 8192
                pred_tokens = min(3072, max_tokens)
            elif "7b" in model_lower or "8b" in model_lower:
                max_model_ctx = 16384
                pred_tokens = min(4096, max_tokens)
            else:
                max_model_ctx = 32768
                pred_tokens = max_tokens

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
            if json_mode and "r1" not in selected_model.lower():
                payload["format"] = "json"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(endpoint, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_content = data.get("message", {}).get("content", "") or ""
                    finish_reason = data.get("done_reason", "stop")
                    usage = {
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    }
                    if json_mode:
                        parsed = repair_and_parse_json(raw_content)
                        return {
                            "success": True,
                            "data": parsed,
                            "raw_content": raw_content,
                            "model": selected_model,
                            "provider": "local",
                            "usage": usage,
                        }
                    return {
                        "success": True,
                        "content": raw_content,
                        "model": selected_model,
                        "provider": "local",
                        "usage": usage,
                    }
                raise RuntimeError(f"Ollama trả mã lỗi {resp.status_code}: {resp.text[:300]}")

        # ----------------------------------------------------------------------
        # LUỒNG 2: MÔ HÌNH ĐÁM MÂY (GEMINI CHÍNH HOẶC DEEPSEEK CLOUD DỰ PHÒNG)
        # ----------------------------------------------------------------------
        primary_provider = "gemini" if self.is_gemini() else "cloud"
        active_key = self.api_key if self._has_valid_key(self.api_key) else (
            self.gemini_key if primary_provider == "gemini" else self.deepseek_key
        )
        active_base = self.base_url

        # Danh sách model thử nghiệm cho Gemini (nếu model mới 3.5 chưa sẵn sàng thì thử 3.1, 2.5, 2.0)
        gemini_candidate_models = [selected_model]
        if primary_provider == "gemini":
            for alt in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
                if alt not in gemini_candidate_models:
                    gemini_candidate_models.append(alt)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            last_error = None
            success = False
            raw_content, usage, finish_reason = "", {}, None

            # Thử gọi Động cơ chính (Primary)
            for attempt_model in (gemini_candidate_models if primary_provider == "gemini" else [selected_model]):
                try:
                    raw_content, usage, finish_reason = await self._execute_openai_call(
                        client=client,
                        base_url=active_base,
                        api_key=active_key,
                        model=attempt_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        json_mode=json_mode,
                    )
                    selected_model = attempt_model
                    success = True
                    break
                except httpx.HTTPStatusError as http_err:
                    status_code = http_err.response.status_code
                    last_error = f"HTTP {status_code}"
                    if status_code == 404 and primary_provider == "gemini":
                        # Tên model chưa kích hoạt trên key này -> thử model Gemini tiếp theo
                        logger.info(f"Mô hình {attempt_model} chưa khả dụng (404), thử chuyển sang {gemini_candidate_models}...")
                        continue
                    if status_code in (429, 500, 502, 503, 504):
                        logger.warning(f"Động cơ chính {primary_provider} ({attempt_model}) trả mã {status_code}. Thử phương án dự phòng...")
                        break
                    # Lỗi 401 hoặc 402
                    break
                except Exception as ex:
                    last_error = str(ex)
                    logger.warning(f"Lỗi khi kết nối động cơ chính {primary_provider}: {ex}")
                    break

            # ------------------------------------------------------------------
            # CƠ CHẾ TỰ ĐỘNG CHUYỂN SANG ĐỘNG CƠ DỰ PHÒNG (FAILOVER FALLBACK)
            # ------------------------------------------------------------------
            fallback_used = False
            fallback_provider = None

            if not success:
                # Nếu Gemini gặp sự cố -> Chuyển sang DeepSeek Cloud
                if primary_provider == "gemini" and self._has_valid_key(self.deepseek_key):
                    logger.warning(
                        f"⚠️ Động cơ chính Gemini không khả dụng ({last_error}). "
                        f"🔄 ĐANG TỰ ĐỘNG KÍCH HOẠT ĐỘNG CƠ DỰ PHÒNG: DeepSeek Cloud ({self.deepseek_model})..."
                    )
                    try:
                        raw_content, usage, finish_reason = await self._execute_openai_call(
                            client=client,
                            base_url=self.deepseek_base_url,
                            api_key=self.deepseek_key,
                            model=self.deepseek_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            json_mode=json_mode,
                        )
                        selected_model = self.deepseek_model
                        primary_provider = "cloud"
                        success = True
                        fallback_used = True
                        fallback_provider = "DeepSeek Cloud (671B)"
                        logger.info("✅ Động cơ dự phòng DeepSeek đã phản hồi thành công!")
                    except Exception as fb_err:
                        last_error = f"Cả Gemini và DeepSeek đều gặp lỗi: {fb_err}"

                # Nếu DeepSeek gặp sự cố -> Chuyển sang Google Gemini
                elif primary_provider == "cloud" and self._has_valid_key(self.gemini_key):
                    logger.warning(
                        f"⚠️ Động cơ DeepSeek không khả dụng ({last_error}). "
                        f"🔄 ĐANG TỰ ĐỘNG KÍCH HOẠT ĐỘNG CƠ DỰ PHÒNG: Google Gemini ({self.gemini_model})..."
                    )
                    try:
                        raw_content, usage, finish_reason = await self._execute_openai_call(
                            client=client,
                            base_url=self.gemini_base_url,
                            api_key=self.gemini_key,
                            model=self.gemini_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            json_mode=json_mode,
                        )
                        selected_model = self.gemini_model
                        primary_provider = "gemini"
                        success = True
                        fallback_used = True
                        fallback_provider = "Google Gemini Flash"
                        logger.info("✅ Động cơ dự phòng Gemini đã phản hồi thành công!")
                    except Exception as fb_err:
                        last_error = f"Cả DeepSeek và Gemini đều gặp lỗi: {fb_err}"

            if not success:
                raise RuntimeError(
                    f"Không thể kết nối với máy chủ AI ({primary_provider}): {last_error}. "
                    "Đồng chí vui lòng kiểm tra kết nối mạng hoặc khoá API trong tệp .env."
                )

            # Xử lý kết quả trả về
            if json_mode:
                try:
                    parsed_data = repair_and_parse_json(raw_content)
                    return {
                        "success": True,
                        "data": parsed_data,
                        "raw_content": raw_content,
                        "model": selected_model,
                        "provider": primary_provider,
                        "fallback_used": fallback_used,
                        "fallback_provider": fallback_provider,
                        "usage": usage,
                    }
                except Exception as parse_err:
                    if finish_reason == "length":
                        raise RuntimeError(
                            f"Văn bản gửi kèm quá dài khiến mô hình AI ({selected_model}) chưa kịp hoàn tất toàn bộ nội dung JSON. "
                            "Đồng chí vui lòng gửi lại lệnh hoặc gửi từng tệp để Chuyên viên Ảo thẩm định sâu hơn."
                        )
                    raise parse_err

            return {
                "success": True,
                "content": raw_content,
                "model": selected_model,
                "provider": primary_provider,
                "fallback_used": fallback_used,
                "fallback_provider": fallback_provider,
                "usage": usage,
            }

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
