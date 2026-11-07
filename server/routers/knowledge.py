# -*- coding: utf-8 -*-
"""
server/routers/knowledge.py
===========================
Router quản trị kho tri thức RAG có kiểm soát (Human-in-the-Loop RAG Ingestion).
Hỗ trợ: xem trước (preview), đối soát, nạp chính thức (commit), thống kê, xoá, và tìm kiếm FTS5.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from server.config import VAN_BAN_DEN_DIR
from server.logger import get_logger
from server.services import db_service, rag_service

logger = get_logger("router_knowledge")
router = APIRouter(prefix="/api/rag", tags=["Knowledge & RAG"])


# --- PYDANTIC SCHEMAS ---

class ThematicCreateRequest(BaseModel):
    ten_chuyen_de: str
    ma_chuyen_de: Optional[str] = None
    mo_ta: Optional[str] = ""
    tu_khoa: Optional[str] = ""


class RagCommitRequest(BaseModel):
    file_path: Optional[str] = ""
    so_hieu_vb: str
    ngay_ban_hanh: str
    co_quan_ban_hanh: str
    co_quan_ban_hanh_code: str
    the_loai_vb: str
    nhom_vong_doi: str
    ma_chuyen_de: Optional[str] = "VAN_PHONG_THI_DUA"
    trich_yeu: str
    thay_the_so_hieu: Optional[str] = ""
    full_text: Optional[str] = ""
    citations: Optional[List[Dict[str, Any]]] = None


class RagUpdateRequest(BaseModel):
    so_hieu_vb: Optional[str] = None
    ngay_ban_hanh: Optional[str] = None
    co_quan_ban_hanh: Optional[str] = None
    co_quan_ban_hanh_code: Optional[str] = None
    the_loai_vb: Optional[str] = None
    nhom_vong_doi: Optional[str] = None
    ma_chuyen_de: Optional[str] = None
    trich_yeu: Optional[str] = None
    trang_thai_hieu_luc: Optional[str] = None
    bi_thay_the_boi_so_hieu: Optional[str] = None


# --- RAG ENDPOINTS ---

@router.get("/thematics")
async def list_thematics_endpoint():
    """Lấy danh mục các chuyên đề công tác."""
    cats = await run_in_threadpool(db_service.get_all_chuyen_de)
    return {"thematics": cats, "total": len(cats)}


@router.post("/thematics")
async def create_thematic_endpoint(req: ThematicCreateRequest):
    """Cán bộ tự thêm chuyên đề mới vào CSDL."""
    if not req.ten_chuyen_de.strip():
        raise HTTPException(status_code=400, detail="Tên chuyên đề không được để trống.")

    res = await run_in_threadpool(
        db_service.add_chuyen_de,
        ten_chuyen_de=req.ten_chuyen_de,
        ma_chuyen_de=req.ma_chuyen_de,
        mo_ta=req.mo_ta or "",
        tu_khoa=req.tu_khoa or "",
    )
    return {"success": True, "message": f"Đã thêm chuyên đề '{res['ten_chuyen_de']}'", "thematic": res}


@router.post("/clear")
async def clear_rag_endpoint():
    """Xoá sạch toàn bộ dữ liệu RAG trong CSDL để nạp lại từ đầu."""
    return await run_in_threadpool(rag_service.clear_rag_data)


@router.get("/stats")
async def get_rag_stats_endpoint():
    """Lấy số liệu thống kê tổng thể kho RAG."""
    return await run_in_threadpool(rag_service.get_rag_stats)


@router.get("/documents")
async def list_rag_documents_endpoint(limit: int = 100):
    """Liệt kê các văn bản đã được kiểm duyệt và nạp vào kho RAG."""
    docs = await run_in_threadpool(rag_service.list_rag_documents, limit=limit)
    return {"documents": docs, "total": len(docs)}


@router.get("/documents/{doc_id:path}")
async def get_rag_document_endpoint(doc_id: str):
    """Lấy chi tiết 1 văn bản trong kho RAG kèm các đoạn trích chunks và liên kết."""
    detail = await run_in_threadpool(rag_service.get_document_detail, doc_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản yêu cầu.")
    return {"success": True, "document": detail}


@router.put("/documents/{doc_id:path}")
async def update_rag_document_endpoint(doc_id: str, req: RagUpdateRequest):
    """Cập nhật siêu dữ liệu văn bản đã nạp trong kho RAG."""
    updates = {k: v for k, v in req.dict().items() if v is not None}
    ok, msg, updated = await run_in_threadpool(rag_service.update_document_metadata, doc_id, updates)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg, "document": updated}


@router.delete("/documents/{doc_id:path}")
async def delete_rag_document_endpoint(doc_id: str):
    """Xoá 1 văn bản khỏi kho RAG."""
    ok = await run_in_threadpool(rag_service.delete_document_from_rag, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản để xoá.")
    return {"success": True, "message": f"Đã xoá văn bản {doc_id} khỏi kho RAG."}


@router.post("/preview")
async def preview_rag_upload_endpoint(file: UploadFile = File(...)):
    """
    Bước 1: Tiếp nhận tệp tải lên, phân tích bóc tách và trả về bản xem trước
    để cán bộ kiểm tra, chỉnh sửa (Human-in-the-Loop) TRƯỚC KHI nạp vào CSDL.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tệp được chọn.")

    dest_dir = VAN_BAN_DEN_DIR / "cap_tren"
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved_file_path = dest_dir / file.filename

    with open(saved_file_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    ok, msg, preview_data = await run_in_threadpool(rag_service.preview_document_for_review, str(saved_file_path))
    if not ok:
        if saved_file_path.exists():
            try:
                os.remove(saved_file_path)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=msg)

    resp = {
        "success": True,
        "message": msg,
        "preview": preview_data,
    }
    resp.update(preview_data)
    return resp


@router.post("/commit")
async def commit_rag_endpoint(req: RagCommitRequest):
    """
    Bước 2: Sau khi cán bộ đã kiểm tra và chỉnh sửa xong thông tin,
    bấm nút 'Phê duyệt & Nạp' để chính thức ghi vào kho CSDL SQLite RAG.
    """
    ok, msg, res_data = await run_in_threadpool(rag_service.commit_reviewed_document, req.dict())
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "data": res_data,
    }


# Router tìm kiếm ngoài prefix /api/rag để tương thích endpoint /api/search cũ
search_router = APIRouter(tags=["Search"])

@search_router.get("/api/search")
async def search_documents_endpoint(q: str):
    """Tìm kiếm nhanh toàn văn FTS5 BM25 trong kho văn bản."""
    results = await run_in_threadpool(db_service.search_fts_bm25, query=q, limit=20)
    return {"query": q, "results": results, "total": len(results)}

