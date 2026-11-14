# -*- coding: utf-8 -*-
"""
scripts/reindex_gemini_embeddings.py
====================================
Quét toàn bộ bảng van_ban_chunks và sinh Vector Embedding bằng Google Gemini API (gemini-embedding-001).
Lưu trữ vector nhị phân float32 BLOB vào CSDL SQLite WAL chuyen_vien_ao.db.
"""

import sys
import time
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.services import db_service, embedding_service
from server.logger import get_logger

logger = get_logger("reindex_embeddings")


def reindex_all_chunks():
    with db_service.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.chunk_id, c.doc_id, vb.so_hieu_vb, vb.trich_yeu, c.context_header, c.chunk_text, c.embedding
            FROM van_ban_chunks c
            JOIN so_van_ban vb ON c.doc_id = vb.doc_id
            ORDER BY c.chunk_id ASC
        """)
        rows = cursor.fetchall()
        total = len(rows)
        print(f"Tổng số chunks trong CSDL: {total}")

        success_count = 0
        skip_count = 0
        fail_count = 0

        for idx, r in enumerate(rows, 1):
            chunk_id = r["chunk_id"]
            so_hieu = r["so_hieu_vb"]
            trich_yeu = r["trich_yeu"]
            context_header = r["context_header"] or ""
            chunk_text = r["chunk_text"] or ""

            # Nội dung dùng để nhúng: Header + Trích yếu + Đoạn đầu/toàn văn
            emb_text = f"{context_header}\nTrích yếu: {trich_yeu}\n\n{chunk_text}"[:7000]

            print(f"[{idx}/{total}] Đang sinh embedding cho {so_hieu} (Chunk ID {chunk_id})...", end=" ", flush=True)
            t0 = time.time()
            blob = embedding_service.get_embedding(emb_text, timeout=15.0)
            dur = time.time() - t0

            if blob:
                cursor.execute(
                    "UPDATE van_ban_chunks SET embedding = ? WHERE chunk_id = ?",
                    (blob, chunk_id)
                )
                conn.commit()
                success_count += 1
                print(f"OK ({dur:.2f}s, {len(blob)} bytes)")
            else:
                fail_count += 1
                print(f"THẤT BẠI!")

            # Nghỉ nhẹ 0.3s để tránh rate limit
            time.sleep(0.3)

        print("\n" + "=" * 50)
        print(f"HOÀN TẤT REINDEX EMBEDDING:")
        print(f"- Thành công: {success_count}/{total}")
        print(f"- Thất bại:   {fail_count}/{total}")
        print("=" * 50)


if __name__ == "__main__":
    reindex_all_chunks()
