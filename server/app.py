#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/app.py
=============
FastAPI Application Hạt nhân cho Hệ thống Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải.
Quản lý cấu hình, middleware, định tuyến đa tầng thông qua các Router chuyên trách:
- server.routers.chat: Xử lý hội thoại, tải tệp, xuất dự thảo Word
- server.routers.knowledge: Quản trị kho RAG, bóc tách và đối soát văn bản
- server.routers.admin: Quản trị mô hình AI, workflows, nhiệm vụ, KPI và danh bạ
- server.routers.zalo_webhook: Tiếp nhận sự kiện và tương tác di động Zalo
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from server.config import (
    BASE_DIR,
    CORS_ORIGINS,
    DEBUG,
    SERVER_HOST,
    SERVER_PORT,
)
from server.logger import get_logger
from server.routers.admin import router as admin_router
from server.routers.auth import router as auth_router
from server.routers.chat import router as chat_router
from server.routers.knowledge import router as knowledge_router, search_router
from server.routers.zalo_webhook import router as zalo_router
from server.services import scheduler_service

logger = get_logger("app")

# Khởi tạo FastAPI app
app = FastAPI(
    title="Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải",
    description="Hệ thống Tham mưu Tổng hợp, Văn thư và Tự động hoá cấp uỷ (mô hình chính quyền địa phương 02 cấp)",
    version="2.1.0",
)

# Cấu hình CORS an toàn cho môi trường nội bộ / local
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Chuyên viên ảo khởi động thành công trên http://%s:%s", SERVER_HOST, SERVER_PORT)
    logger.info("Cấu hình CORS origins được phép: %s", CORS_ORIGINS)
    # Khởi động bộ lập lịch tự động và chạy khởi động bù
    scheduler_service.start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Chuyên viên ảo đang tắt hệ thống...")
    scheduler_service.stop_scheduler()


# Đường dẫn tĩnh phục vụ giao diện Web
STATIC_DIR = BASE_DIR / "server" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- ĐĂNG KÝ CÁC ROUTER CHUYÊN TRÁCH ---
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(search_router)
app.include_router(admin_router)
app.include_router(zalo_router)


# --- GIAO DIỆN CHÍNH ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Phục vụ giao diện người dùng chính."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h2>Chuyên viên Ảo đang khởi động giao diện...</h2>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host=SERVER_HOST, port=SERVER_PORT, reload=DEBUG)
