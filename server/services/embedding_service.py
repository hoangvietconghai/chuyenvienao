# -*- coding: utf-8 -*-
"""
server/services/embedding_service.py
====================================
Dịch vụ sinh và tính toán Vector Embedding cho True Hybrid RAG:
- Động cơ chính: Google Gemini Embedding API (gemini-embedding-001, 3072 chiều) tốc độ cao.
- Động cơ dự phòng: Ollama API cục bộ (nomic-embed-text) nếu có cấu hình.
- Nén vector float32 thành byte BLOB lưu vào SQLite.
- Tính tương đồng Cosine cực nhanh trên RAM bằng NumPy / Python thuần.
- Chế độ Fallback thông minh: nếu mất mạng hoặc lỗi API, hệ thống vẫn chạy mượt mà bằng FTS5 BM25.
"""

import struct
from typing import List, Optional, Tuple

import httpx

from server.config import (
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
)
from server.logger import get_logger

logger = get_logger("embedding_service")
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _get_gemini_embedding(clean_text: str, timeout: float = 10.0) -> Optional[List[float]]:
    """Gọi Google Gemini API để lấy vector embedding (3072 chiều)."""
    if not GEMINI_API_KEY or len(GEMINI_API_KEY.strip()) < 5:
        return None

    model_name = GEMINI_EMBEDDING_MODEL
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:embedContent?key={GEMINI_API_KEY.strip()}"
    payload = {
        "content": {
            "parts": [{"text": clean_text}]
        }
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                values = resp.json().get("embedding", {}).get("values", [])
                if values and isinstance(values, list):
                    return values
            else:
                logger.debug(f"Gemini embedding API trả HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as ex:
        logger.debug(f"Lỗi khi kết nối Gemini embedding: {ex}")

    return None


def _get_ollama_embedding(clean_text: str, timeout: float = 5.0) -> Optional[List[float]]:
    """Dự phòng: Gọi Ollama API cục bộ nếu Gemini không khả dụng."""
    try:
        base = OLLAMA_BASE_URL.replace("/v1", "").rstrip("/")
        url = f"{base}/api/embeddings"
        payload = {"model": OLLAMA_EMBEDDING_MODEL, "prompt": clean_text}
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                vec = resp.json().get("embedding", [])
                if vec and isinstance(vec, list):
                    return vec
    except Exception:
        pass
    return None


def get_embedding(text: str, timeout: float = 10.0) -> Optional[bytes]:
    """
    Sinh vector nhúng cho 1 đoạn văn bản (ưu tiên Gemini, dự phòng Ollama).
    Trả về bytes (BLOB) để lưu vào cột embedding của bảng van_ban_chunks.
    """
    if not text or not text.strip():
        return None

    # Giới hạn an toàn độ dài đoạn text cần nhúng
    clean_text = text.strip()[:8000]

    # 1. Thử qua Gemini API (Chính)
    vec = _get_gemini_embedding(clean_text, timeout=timeout)

    # 2. Dự phòng qua Ollama nếu Gemini không trả về
    if not vec:
        vec = _get_ollama_embedding(clean_text, timeout=timeout)

    if vec:
        # Nén danh sách float32 thành chuỗi byte nhị phân BLOB
        return struct.pack(f"{len(vec)}f", *vec)

    return None


def unpack_embedding(blob: Optional[bytes]) -> List[float]:
    """Giải nén byte BLOB từ SQLite thành danh sách float32."""
    if not blob:
        return []
    try:
        num_floats = len(blob) // 4
        return list(struct.unpack(f"{num_floats}f", blob))
    except Exception:
        return []


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Tính độ tương đồng Cosine giữa 2 vector."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    if HAS_NUMPY:
        arr1 = np.array(v1, dtype=np.float32)
        arr2 = np.array(v2, dtype=np.float32)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(arr1, arr2) / (norm1 * norm2))

    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)
