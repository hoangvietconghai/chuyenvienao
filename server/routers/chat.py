# -*- coding: utf-8 -*-
"""
server/routers/chat.py
======================
Router xử lý hội thoại chính, tiếp nhận lệnh chỉ đạo, đính kèm tệp và tải văn bản dự thảo.
Áp dụng cơ chế bất đồng bộ non-blocking (run_in_threadpool) và bảo mật đường dẫn.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from server import chat_engine
from server.config import BASE_DIR, VAN_BAN_DU_THAO_DIR
from server.logger import get_logger
from server.router import route_incoming_file

logger = get_logger("router_chat")
router = APIRouter(tags=["Chat & Files"])

ALLOWED_DOWNLOAD_DIR = VAN_BAN_DU_THAO_DIR.resolve()
ALLOWED_EXTENSIONS = {".docx", ".pdf"}


# --- PYDANTIC SCHEMAS ---

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: Optional[str] = ""
    action: Optional[str] = ""


class SessionRequest(BaseModel):
    session_id: Optional[str] = None
    attachment_id: Optional[str] = None


# --- CHAT ENDPOINTS ---

@router.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Nhận lệnh của cán bộ, tự chọn nghiệp vụ và phản hồi."""
    return await chat_engine.handle_chat(req.session_id, req.message or "", req.action or "")


@router.post("/api/chat/upload")
async def chat_upload(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """Đính kèm tệp vào phiên hội thoại (tự lưu đúng thư mục văn bản đến)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tệp được chọn.")

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / Path(file.filename).name

    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        # Chạy hàm đọc và phân luồng file đồng bộ trong worker thread
        routing = await run_in_threadpool(route_incoming_file, str(tmp_path))

        if not routing.get("full_text", "").strip():
            raise HTTPException(status_code=422, detail="Không đọc được chữ trong tệp (có thể là PDF dạng ảnh scan).")

        sid, att = chat_engine.add_attachment(session_id, routing)
        return {
            "session_id": sid,
            "attachment": {
                "id": att["id"],
                "name": att["name"],
                "category_label": att["category_label"],
                "char_count": len(att["text"]),
            },
        }
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc tệp: {ex}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/api/chat/attachment/remove")
async def chat_remove_attachment(req: SessionRequest):
    """Xoá tệp đính kèm khỏi phiên làm việc."""
    ok = chat_engine.remove_attachment(req.session_id or "", req.attachment_id or "")
    return {"success": ok}


@router.post("/api/chat/reset")
async def chat_reset(req: SessionRequest):
    """Làm mới phiên làm việc."""
    return {"session_id": chat_engine.reset_session(req.session_id)}


@router.post("/api/upload")
async def handle_document_upload(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
):
    """Tiếp nhận tệp tài liệu tải lên từ cán bộ, tự động đọc nội dung và phân luồng."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tệp được chọn.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        routing_result = await run_in_threadpool(route_incoming_file, tmp_path, target_category=category)
        return routing_result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý tệp: {str(ex)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _scan_recent_documents_sync() -> List[Dict[str, Any]]:
    """Hàm quét đĩa đồng bộ để lấy danh sách file dự thảo gần đây."""
    files = []
    if VAN_BAN_DU_THAO_DIR.exists():
        for f in VAN_BAN_DU_THAO_DIR.glob("**/*.docx"):
            if not f.name.startswith("~$"):
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "relative_path": str(f.relative_to(BASE_DIR)).replace("\\", "/"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                    "type": "du_thao",
                })
    files.sort(key=lambda x: x["created_at"], reverse=True)
    return files[:30]


@router.get("/api/documents")
async def list_recent_documents():
    """Liệt kê các văn bản dự thảo gần đây (non-blocking)."""
    files = await run_in_threadpool(_scan_recent_documents_sync)
    return {"documents": files}


@router.get("/api/download")
async def download_file(file_path: str):
    """Tải tệp văn bản dự thảo đã tạo, có chốt chặn bảo mật chống Path Traversal."""
    target_path = (BASE_DIR / file_path).resolve() if not Path(file_path).is_absolute() else Path(file_path).resolve()

    # Chốt chặn 1: Bắt buộc nằm trong thư mục van_ban_du_thao/
    if not str(target_path).startswith(str(ALLOWED_DOWNLOAD_DIR)):
        logger.warning(f"Cảnh báo bảo mật: Truy cập tệp ngoài phạm vi cho phép: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Truy cập bị từ chối: Chỉ được phép tải tệp từ thư mục dự thảo.",
        )

    # Chốt chặn 2: Bắt buộc đuôi tệp phải là .docx hoặc .pdf
    if target_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Định dạng tệp không được phép tải về.",
        )

    if not target_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tệp yêu cầu.")

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if target_path.suffix.lower() == ".docx"
        else "application/pdf"
    )

    return FileResponse(
        path=str(target_path),
        filename=target_path.name,
        media_type=media_type,
    )

