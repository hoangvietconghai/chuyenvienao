#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/app.py
=============
FastAPI Server cho Hệ thống Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải.
Cung cấp API xử lý văn bản, phân tích DeepSeek, thẩm định 2 tầng và xuất file Word.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from server.ai_connector import default_ai_client
from server.config import (
    BASE_DIR,
    CO_QUAN_BAN_HANH,
    CO_QUAN_CAP_TREN,
    DEBUG,
    DEEPSEEK_MODEL,
    NAM_HIEN_TAI,
    SERVER_HOST,
    SERVER_PORT,
    VAN_BAN_DEN_DIR,
    VAN_BAN_DU_THAO_DIR,
    VAN_PHONG_NAME,
)
from server.router import WORKFLOW_MAP, route_incoming_file
from server import chat_engine
from server.workflows.wf1_synthesizer import (
    analyze_weekly_reports,
    generate_weekly_report_docx,
)
from server.workflows.wf2_conclusions import (
    analyze_meeting_notes,
    generate_meeting_conclusion_docx,
)
from server.workflows.wf3_dispatch import (
    analyze_provincial_directive,
    generate_dispatch_docx,
)
from server.workflows.wf4_appraisal import (
    analyze_agency_draft,
    generate_appraisal_documents,
)

# Khởi tạo FastAPI app
app = FastAPI(
    title="Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải",
    description="Hệ thống Tham mưu Tổng hợp, Văn thư và Tự động hoá cấp uỷ địa phương 3 cấp",
    version="2.0.0",
)

# Cấu hình CORS để chạy mượt mà trên trình duyệt local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đường dẫn static
STATIC_DIR = BASE_DIR / "server" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- PYDANTIC SCHEMAS ---
class WorkflowAnalyzeRequest(BaseModel):
    text: str
    sub_title: Optional[str] = ""
    extra_param: Optional[str] = ""


class WorkflowGenerateRequest(BaseModel):
    analysis_data: Dict[str, Any]
    user_confirmations: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: Optional[str] = ""
    action: Optional[str] = ""


class SessionRequest(BaseModel):
    session_id: Optional[str] = None
    attachment_id: Optional[str] = None


# --- CHAT API (giao diện trò chuyện) ---

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Nhận lệnh của cán bộ, tự chọn nghiệp vụ và trả lời."""
    return await chat_engine.handle_chat(req.session_id, req.message or "", req.action or "")


@app.post("/api/chat/upload")
async def chat_upload(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """Đính kèm tệp vào cuộc trò chuyện (tự lưu đúng thư mục văn bản đến)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tệp được chọn.")
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / Path(file.filename).name
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        routing = route_incoming_file(str(tmp_path))
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


@app.post("/api/chat/attachment/remove")
async def chat_remove_attachment(req: SessionRequest):
    ok = chat_engine.remove_attachment(req.session_id or "", req.attachment_id or "")
    return {"success": ok}


@app.post("/api/chat/reset")
async def chat_reset(req: SessionRequest):
    return {"session_id": chat_engine.reset_session(req.session_id)}


# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Phục vụ giao diện người dùng chính."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h2>Chuyên viên Ảo đang khởi động giao diện...</h2>")


class ModelSwitchRequest(BaseModel):
    model_id: str
    provider: Optional[str] = None


@app.get("/api/status")
async def get_system_status():
    """Kiểm tra tình trạng vận hành hệ thống và kết nối AI."""
    ai_configured = default_ai_client.is_configured()
    is_local = default_ai_client.is_local()
    current_model = default_ai_client.model

    # Đếm số lượng văn bản trong hệ thống
    den_count = len(list(VAN_BAN_DEN_DIR.glob("**/*.*"))) if VAN_BAN_DEN_DIR.exists() else 0
    du_thao_count = len(list(VAN_BAN_DU_THAO_DIR.glob("**/*.docx"))) if VAN_BAN_DU_THAO_DIR.exists() else 0

    return {
        "status": "online",
        "app_name": "Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải",
        "model_in_use": current_model,
        "is_local": is_local,
        "ai_configured": ai_configured,
        "ai_notice": f"Sẵn sàng (Local {current_model})" if is_local else ("Đã sẵn sàng" if ai_configured else "Chưa cấu hình API Key"),
        "organization": {
            "cap_tren": CO_QUAN_CAP_TREN,
            "ban_hanh": CO_QUAN_BAN_HANH,
            "van_phong": VAN_PHONG_NAME,
            "year": NAM_HIEN_TAI,
        },
        "stats": {
            "incoming_docs": den_count,
            "generated_drafts": du_thao_count,
        },
    }


@app.get("/api/models")
async def list_available_models():
    """Liệt kê các mô hình khả dụng và kiểm tra trạng thái Ollama Local."""
    import httpx
    from server.config import SUPPORTED_MODELS

    installed_local_models = []
    ollama_online = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                ollama_online = True
                data = resp.json()
                for m in data.get("models", []):
                    installed_local_models.append(m.get("name"))
    except Exception:
        ollama_online = False

    models_info = []
    for m in SUPPORTED_MODELS:
        m_copy = dict(m)
        if m["provider"] == "local":
            m_copy["is_installed"] = any(m["id"] in ins or ins in m["id"] for ins in installed_local_models)
        else:
            m_copy["is_installed"] = True
        models_info.append(m_copy)

    return {
        "current_model": default_ai_client.model,
        "is_local": default_ai_client.is_local(),
        "ollama_online": ollama_online,
        "installed_local_models": installed_local_models,
        "models": models_info,
    }


@app.post("/api/models/switch")
async def switch_model(req: ModelSwitchRequest):
    """Chuyển đổi mô hình AI đang sử dụng (Local 3B/7B hoặc Cloud)."""
    res = default_ai_client.switch_model(req.model_id, req.provider)
    return {
        "success": True,
        "active_model": res["model"],
        "is_local": res["is_local"],
        "message": f"Đã chuyển sang mô hình: {res['model']}",
    }


@app.post("/api/upload")
async def handle_document_upload(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
):
    """
    Tiếp nhận tệp tài liệu tải lên từ cán bộ, tự động đọc nội dung và phân luồng.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tệp được chọn.")

    # Lưu tệp tạm để đọc
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        routing_result = route_incoming_file(tmp_path, target_category=category)
        return routing_result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý tệp: {str(ex)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/workflow/{wf_name}/analyze")
async def handle_workflow_analysis(wf_name: str, payload: WorkflowAnalyzeRequest):
    """
    Kích hoạt DeepSeek phân tích văn bản theo từng quy trình nghiệp vụ.
    Trả về dữ liệu đã bóc tách kèm danh sách cảnh báo số liệu (Human-in-the-Loop).
    """
    if not default_ai_client.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chưa cấu hình DEEPSEEK_API_KEY trong tệp .env. Vui lòng thêm key để kích hoạt AI.",
        )

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Nội dung văn bản đầu vào trống.")

    try:
        if wf_name == "wf1_tong_hop_bao_cao":
            result = await analyze_weekly_reports(text, week_number=payload.sub_title or "...")
        elif wf_name == "wf2_thong_bao_ket_luan":
            result = await analyze_meeting_notes(text, meeting_title=payload.sub_title or "Họp Thường trực Đảng uỷ")
        elif wf_name == "wf3_giao_viec":
            result = await analyze_provincial_directive(text)
        elif wf_name == "wf4_tham_dinh":
            result = await analyze_agency_draft(text, submitting_agency=payload.extra_param or "UBND xã")
        else:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy quy trình nghiệp vụ: {wf_name}")

        return {
            "success": True,
            "workflow": wf_name,
            "data": result,
            "has_warnings": bool(result.get("canh_bao_so_lieu")),
            "warning_count": len(result.get("canh_bao_so_lieu", [])),
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích DeepSeek: {str(ex)}")


@app.post("/api/workflow/{wf_name}/generate")
async def handle_workflow_generation(wf_name: str, payload: WorkflowGenerateRequest):
    """
    Sau khi cán bộ đã kiểm tra và duyệt trên giao diện (Human-in-the-Loop),
    hệ thống gọi engine PartyDocumentBuilder xuất các file Word chuẩn HD 05-HD/VPTW.
    """
    data = payload.analysis_data
    generated_files = []

    try:
        if wf_name == "wf1_tong_hop_bao_cao":
            doc_payload = data.get("document_payload", data)
            file_path = generate_weekly_report_docx(doc_payload)
            generated_files.append({"type": "Báo cáo Tuần (-BC/VPĐU)", "path": file_path, "name": Path(file_path).name})

        elif wf_name == "wf2_thong_bao_ket_luan":
            doc_payload = data.get("document_payload", data)
            file_path = generate_meeting_conclusion_docx(doc_payload)
            generated_files.append({"type": "Thông báo Kết luận (-TB/ĐU)", "path": file_path, "name": Path(file_path).name})

        elif wf_name == "wf3_giao_viec":
            doc_payload = data.get("document_payload", data)
            file_path = generate_dispatch_docx(doc_payload)
            generated_files.append({"type": "Công văn Giao việc (-CV/ĐU)", "path": file_path, "name": Path(file_path).name})

        elif wf_name == "wf4_tham_dinh":
            docs = generate_appraisal_documents(data)
            for k, p in docs.items():
                label = "Báo cáo Thẩm định (-BC/VPĐU)" if k == "bc_tham_dinh" else (
                    "Dự thảo hoàn chỉnh" if k == "du_thao_chuan_hoa" else "Công văn xin ý kiến BTV (-CV/ĐU)"
                )
                generated_files.append({"type": label, "path": p, "name": Path(p).name})
        else:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy quy trình: {wf_name}")

        return {
            "success": True,
            "generated_files": generated_files,
            "message": f"Đã xuất thành công {len(generated_files)} tệp Word chuẩn thể thức.",
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất file Word: {str(ex)}")


@app.get("/api/documents")
async def list_recent_documents():
    """Liệt kê các văn bản đến và văn bản dự thảo gần đây."""
    files = []
    # Quét các file Word trong van_ban_du_thao
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
    return {"documents": files[:30]}


@app.get("/api/download")
async def download_file(file_path: str):
    """Tải tệp Word đã xuất về máy tính của cán bộ."""
    full_path = (BASE_DIR / file_path).resolve()
    # Kiểm tra bảo mật: file phải nằm trong thư mục dự án
    if not str(full_path).startswith(str(BASE_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Đường dẫn không hợp lệ.")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp yêu cầu.")

    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host=SERVER_HOST, port=SERVER_PORT, reload=DEBUG)
