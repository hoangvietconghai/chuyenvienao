# -*- coding: utf-8 -*-
"""
server/services/embedding_service.py
====================================
Dịch vụ sinh và tính toán Vector Embedding cục bộ cho Hybrid RAG.
- Mô hình mặc định: nomic-embed-text qua Ollama API (localhost:11434).
- Nén vector float32 thành byte BLOB lưu vào SQLite.
- Tính tương đồng Cosine cực nhanh trên RAM bằng NumPy / Python thuần.
- Chế độ Fallback thông minh: nếu Ollama chưa bật, hệ thống vẫn chạy FTS5 mượt mà.
"""

import struct
from typing import List, Optional, Tuple

import httpx

from server.config import OLLAMA_BASE_URL
from server.logger import get_logger

logger = get_logger("embedding_service")
EMBEDDING_MODEL = "nomic-embed-text"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def get_embedding(text: str, timeout: float = 8.0) -> Optional[bytes]:
    """
    Sinh vector nhúng cho 1 đoạn văn bản qua Ollama API.
    Trả về bytes (BLOB) để lưu vào cột embedding của bảng van_ban_chunks.
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()[:4000]
    try:
        url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
        payload = {"model": EMBEDDING_MODEL, "prompt": clean_text}
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                vec = resp.json().get("embedding", [])
                if vec and isinstance(vec, list):
                    # Nén danh sách float32 thành chuỗi byte nhị phân BLOB
                    return struct.pack(f"{len(vec)}f", *vec)
    except Exception as ex:
        logger.debug(f"Chưa kết nối được Ollama embedding ({EMBEDDING_MODEL}): {ex}")

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
