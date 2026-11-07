# -*- coding: utf-8 -*-
"""
server/routers/admin.py
=======================
Router quản trị hệ thống:
1. Trạng thái kết nối AI & chuyển đổi mô hình (Ollama Local / DeepSeek Cloud).
2. Xử lý phân tích và xuất tài liệu cho 4 quy trình nghiệp vụ (WF1 - WF4).
3. Quản lý Sổ Nhiệm vụ (Tasks CRUD).
4. Giám sát Chỉ tiêu Nghị quyết (KPIs).
5. Quản lý Danh bạ cán bộ, lãnh đạo, 08 thôn và 21 chi bộ.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from server.ai_connector import default_ai_client
from server.config import (
    BASE_DIR,
    CO_QUAN_BAN_HANH,
    CO_QUAN_CAP_TREN,
    NAM_HIEN_TAI,
    SUPPORTED_MODELS,
    VAN_BAN_DEN_DIR,
    VAN_BAN_DU_THAO_DIR,
    VAN_PHONG_NAME,
)
from server.logger import get_logger
from server.services import db_service
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

logger = get_logger("router_admin")
router = APIRouter(tags=["Admin & Workflows"])


# --- PYDANTIC SCHEMAS ---

class ModelSwitchRequest(BaseModel):
    model_id: str
    provider: Optional[str] = None


class WorkflowAnalyzeRequest(BaseModel):
    text: str
    sub_title: Optional[str] = ""
    extra_param: Optional[str] = ""


class WorkflowGenerateRequest(BaseModel):
    analysis_data: Dict[str, Any]
    user_confirmations: Optional[Dict[str, Any]] = None


class TaskCreateRequest(BaseModel):
    noi_dung_nhiem_vu: str
    co_quan_chu_tri: str
    co_quan_chu_tri_code: str
    so_hieu_vb: Optional[str] = None
    lanh_dao_chi_dao: Optional[str] = None
    cap_trinh: Optional[str] = None
    ngay_giao: Optional[str] = None
    deadline_date: str
    deadline_time: Optional[str] = "17:00"
    deadline_type: Optional[str] = "EXACT"
    muc_do_uu_tien: Optional[str] = "Bình thường"
    linh_vuc: Optional[str] = "Chung"
    co_quan_phoi_hop: Optional[List[str]] = None


class TaskStatusUpdateRequest(BaseModel):
    trang_thai: str
    ket_qua_bao_cao: Optional[str] = ""


class KpiUpdateRequest(BaseModel):
    gia_tri_hien_tai: float
    bieu_thuc_chi_tiet: Optional[str] = ""
    trang_thai_anh_sang: Optional[str] = "XANH"


# --- SYSTEM & MODEL STATUS ENDPOINTS ---

@router.get("/api/status")
async def get_system_status():
    """Kiểm tra tình trạng vận hành hệ thống và kết nối AI."""
    ai_configured = default_ai_client.is_configured()
    is_local = default_ai_client.is_local()
    current_model = default_ai_client.model

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


@router.get("/api/models")
async def list_available_models():
    """Liệt kê các mô hình khả dụng và kiểm tra trạng thái Ollama Local."""
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


@router.post("/api/models/switch")
async def switch_model(req: ModelSwitchRequest):
    """Chuyển đổi mô hình AI đang sử dụng (Local 3B/7B hoặc Cloud)."""
    res = default_ai_client.switch_model(req.model_id, req.provider)
    return {
        "success": True,
        "active_model": res["model"],
        "is_local": res["is_local"],
        "message": f"Đã chuyển sang mô hình: {res['model']}",
    }


# --- WORKFLOW ANALYSIS & GENERATION ---

@router.post("/api/workflow/{wf_name}/analyze")
async def handle_workflow_analysis(wf_name: str, payload: WorkflowAnalyzeRequest):
    """Kích hoạt phân tích văn bản theo từng quy trình nghiệp vụ (WF1 - WF4)."""
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
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích: {str(ex)}")


@router.post("/api/workflow/{wf_name}/generate")
async def handle_workflow_generation(wf_name: str, payload: WorkflowGenerateRequest):
    """Xuất các file Word chuẩn HD 05-HD/VPTW bằng worker thread non-blocking."""
    data = payload.analysis_data
    generated_files = []

    try:
        if wf_name == "wf1_tong_hop_bao_cao":
            doc_payload = data.get("document_payload", data)
            file_path = await run_in_threadpool(generate_weekly_report_docx, doc_payload)
            generated_files.append({"type": "Báo cáo Tuần (-BC/VPĐU)", "path": file_path, "name": Path(file_path).name})

        elif wf_name == "wf2_thong_bao_ket_luan":
            doc_payload = data.get("document_payload", data)
            file_path = await run_in_threadpool(generate_meeting_conclusion_docx, doc_payload)
            generated_files.append({"type": "Thông báo Kết luận (-TB/ĐU)", "path": file_path, "name": Path(file_path).name})

        elif wf_name == "wf3_giao_viec":
            doc_payload = data.get("document_payload", data)
            file_path = await run_in_threadpool(generate_dispatch_docx, doc_payload)
            generated_files.append({"type": "Công văn Giao việc (-CV/ĐU)", "path": file_path, "name": Path(file_path).name})

        elif wf_name == "wf4_tham_dinh":
            docs = await run_in_threadpool(generate_appraisal_documents, data)
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


# --- SỔ NHIỆM VỤ, CHỈ TIÊU & DANH BẠ ---

@router.get("/api/tasks")
async def list_tasks(
    trang_thai: Optional[str] = None,
    co_quan: Optional[str] = None,
    cap_trinh: Optional[str] = None,
    tu_ngay: Optional[str] = None,
    den_ngay: Optional[str] = None,
):
    """Truy vấn danh sách nhiệm vụ từ Sổ Nhiệm vụ (SQLite DB)."""
    tasks = await run_in_threadpool(
        db_service.get_tasks,
        trang_thai=trang_thai,
        co_quan_code=co_quan,
        cap_trinh=cap_trinh,
        tu_ngay=tu_ngay,
        den_ngay=den_ngay,
        limit=200,
    )
    return {"tasks": tasks, "total": len(tasks)}


@router.post("/api/tasks")
async def create_or_update_task_endpoint(req: TaskCreateRequest):
    """Thêm mới hoặc cập nhật nhiệm vụ (tự động khử trùng lặp)."""
    task_dict = req.dict()
    ok, task_id, action = await run_in_threadpool(db_service.add_or_update_task, task_dict)
    return {
        "success": ok,
        "task_id": task_id,
        "action": action,
        "message": "Đã tạo nhiệm vụ mới thành công" if action == "created" else "Nhiệm vụ đã được cập nhật/lùi hạn",
    }


@router.put("/api/tasks/{task_id}/status")
async def update_task_status_endpoint(task_id: str, req: TaskStatusUpdateRequest):
    """Cập nhật trạng thái thực hiện nhiệm vụ (Hoàn thành / Đang thực hiện...)."""
    ok = await run_in_threadpool(db_service.update_task_status, task_id, req.trang_thai, req.ket_qua_bao_cao or "")
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ yêu cầu.")
    return {"success": True, "task_id": task_id, "status": req.trang_thai}


@router.delete("/api/tasks/{task_id}")
async def delete_task_endpoint(task_id: str):
    """Xoá một nhiệm vụ theo ID."""
    ok = await run_in_threadpool(db_service.delete_task, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ.")
    return {"success": True, "message": f"Đã xoá nhiệm vụ {task_id}"}


@router.get("/api/kpis")
async def list_kpis(source: Optional[str] = None):
    """Lấy danh sách các chỉ tiêu KPI (Đại hội Đảng bộ khoá I và NQ57 CĐS)."""
    kpis = await run_in_threadpool(db_service.get_all_kpis, nguon_nghi_quyet=source)
    return {"kpis": kpis, "total": len(kpis)}


@router.put("/api/kpis/{kpi_id}")
async def update_kpi_endpoint(kpi_id: str, req: KpiUpdateRequest):
    """Cập nhật tiến độ số liệu của một chỉ tiêu KPI."""
    ok = await run_in_threadpool(
        db_service.update_kpi_progress,
        kpi_id,
        gia_tri=req.gia_tri_hien_tai,
        bieu_thuc=req.bieu_thuc_chi_tiet or "",
        trang_thai=req.trang_thai_anh_sang or "XANH",
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy chỉ tiêu KPI.")
    return {"success": True, "kpi_id": kpi_id}


@router.get("/api/directory")
async def list_directory():
    """Lấy danh bạ cán bộ, lãnh đạo, 08 thôn và 21 chi bộ xã Công Hải."""
    directory = await run_in_threadpool(db_service.get_all_can_bo, only_active=True)
    return {"directory": directory, "total": len(directory)}

