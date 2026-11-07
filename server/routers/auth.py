# -*- coding: utf-8 -*-
"""
server/routers/auth.py
======================
Router xác thực cán bộ bằng số điện thoại Zalo (Passwordless / Zalo OTP Authentication).
Bảo vệ tuyệt đối thông tin cá nhân (Zero PII to AI):
- Toàn bộ thông tin định danh, số điện thoại, quyền hạn lưu trữ 100% tại CSDL SQLite cục bộ.
- Không gửi bất kỳ thông tin cá nhân nào lên các mô hình AI đám mây (Gemini/DeepSeek).
- Phân lập 2 chế độ:
  1. Cán bộ đăng nhập: Lưu lịch sử công tác vào CSDL SQLite WAL `nhat_ky_hoi_thoai`.
  2. Chế độ Khách (Guest / Ẩn danh): Lưu tạm trên RAM; đóng tab là xoá sạch không dấu vết.
"""

import hashlib
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from server import chat_engine
from server.logger import get_logger
from server.services import db_service
from server.services.zalo_api import send_message

logger = get_logger("router_auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

AUTH_SECRET = "cong_hai_party_office_auth_secret_2026"
ACTIVE_TOKENS: Dict[str, Dict[str, Any]] = {}


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str
    session_id: Optional[str] = None


class SessionCheckRequest(BaseModel):
    session_id: Optional[str] = None
    token: Optional[str] = None


def generate_auth_token(can_bo_id: str, phone: str) -> str:
    """Sinh token định danh phiên an toàn cho cán bộ."""
    raw = f"{can_bo_id}:{phone}:{time.time()}:{AUTH_SECRET}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


@router.post("/send-otp")
async def send_otp(req: SendOtpRequest):
    """Gửi mã xác thực OTP 6 số tới số điện thoại Zalo của cán bộ."""
    clean_phone = db_service.normalize_phone_number(req.phone)
    if not clean_phone or len(clean_phone) < 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 số di động."
        )

    can_bo = db_service.get_can_bo_by_phone(clean_phone)
    if not can_bo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Số điện thoại chưa có trong danh bạ cán bộ xã Công Hải. Vui lòng liên hệ Văn phòng Đảng uỷ để đăng ký."
        )

    otp_code, _ = db_service.create_zalo_otp(clean_phone)
    if not otp_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo mã xác thực. Vui lòng thử lại sau ít phút."
        )

    # Thử gửi qua Zalo Bot nếu cán bộ đã có zalo_chat_id hoặc zalo_user_id
    zalo_sent = False
    chat_target = can_bo.get("zalo_chat_id") or can_bo.get("zalo_user_id")
    if chat_target:
        msg_text = (
            f"🔐 **CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI**\n\n"
            f"Mã xác thực đăng nhập của đồng chí **{can_bo.get('ho_ten')}** là: **{otp_code}**\n\n"
            f"⏳ *Mã có hiệu lực trong vòng 5 phút. Tuyệt đối không chia sẻ mã này cho người khác.*"
        )
        zalo_sent = send_message(str(chat_target), msg_text)

    logger.info(f"Đã phát sinh OTP cho {clean_phone} (Zalo sent: {zalo_sent})")

    return {
        "success": True,
        "message": f"Đã gửi mã xác thực tới Zalo của đồng chí {can_bo.get('ho_ten')}.",
        "can_bo": {
            "can_bo_id": can_bo.get("can_bo_id"),
            "ho_ten": can_bo.get("ho_ten"),
            "chuc_vu": can_bo.get("chuc_vu"),
            "co_quan": can_bo.get("co_quan"),
            "vai_tro": can_bo.get("vai_tro", "can_bo"),
        },
        "zalo_sent": zalo_sent,
        # Trả về dev_otp để cán bộ đăng nhập ngay trên giao diện nội bộ khi chưa kích hoạt Zalo Webhook
        "dev_otp": otp_code,
    }


@router.post("/verify-otp")
async def verify_otp(req: VerifyOtpRequest):
    """Xác thực mã OTP 6 số và đăng nhập chính danh cán bộ."""
    clean_phone = db_service.normalize_phone_number(req.phone)
    ok, message, can_bo = db_service.verify_zalo_otp(clean_phone, req.otp)

    if not ok or not can_bo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Sinh token xác thực
    token = generate_auth_token(can_bo["can_bo_id"], clean_phone)
    can_bo_info = {
        "can_bo_id": can_bo["can_bo_id"],
        "ho_ten": can_bo["ho_ten"],
        "chuc_vu": can_bo["chuc_vu"],
        "co_quan": can_bo["co_quan"],
        "co_quan_code": can_bo["co_quan_code"],
        "so_dien_thoai": can_bo.get("so_dien_thoai"),
        "vai_tro": can_bo.get("vai_tro", "can_bo"),
    }
    ACTIVE_TOKENS[token] = {
        "can_bo": can_bo_info,
        "created_at": time.time(),
    }

    # Nếu có session_id gửi kèm -> Gắn danh tính cán bộ vào phiên chat backend
    if req.session_id:
        _, s = chat_engine.get_session(req.session_id)
        s["authenticated"] = True
        s["can_bo"] = can_bo_info

    logger.info(f"Cán bộ đăng nhập thành công: {can_bo['ho_ten']} ({can_bo.get('vai_tro')})")

    return {
        "success": True,
        "message": f"Xin chào đồng chí {can_bo['ho_ten']} ({can_bo['chuc_vu']})!",
        "token": token,
        "can_bo": can_bo_info,
    }


@router.post("/check")
async def check_auth_session(req: SessionCheckRequest):
    """Kiểm tra trạng thái đăng nhập của phiên hiện tại."""
    token = req.token
    if token and token in ACTIVE_TOKENS:
        return {
            "authenticated": True,
            "mode": "cadre",
            "can_bo": ACTIVE_TOKENS[token]["can_bo"],
        }

    if req.session_id and req.session_id in chat_engine.SESSIONS:
        s = chat_engine.SESSIONS[req.session_id]
        if s.get("authenticated") and s.get("can_bo"):
            return {
                "authenticated": True,
                "mode": "cadre",
                "can_bo": s["can_bo"],
            }

    return {
        "authenticated": False,
        "mode": "guest",
        "notice": "Đang ở Chế độ Khách (Phiên sẽ tự động xoá khi đóng tab trình duyệt).",
    }


@router.post("/logout")
async def logout(req: SessionCheckRequest):
    """Đăng xuất cán bộ và chuyển về Chế độ Khách (Ẩn danh)."""
    if req.token and req.token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[req.token]

    if req.session_id and req.session_id in chat_engine.SESSIONS:
        s = chat_engine.SESSIONS[req.session_id]
        s["authenticated"] = False
        s["can_bo"] = None

    return {"success": True, "message": "Đã đăng xuất thành công."}

