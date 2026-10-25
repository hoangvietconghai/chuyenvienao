# -*- coding: utf-8 -*-
"""
server/services/gdrive_service.py
=================================
Dịch vụ tải tệp lên Google Drive và tạo liên kết chia sẻ cho cán bộ qua Zalo.
Hỗ trợ:
1. Google Apps Script Web App (không cần tài khoản GCP, tải trực tiếp bằng HTTP POST)
2. Google Service Account / OAuth (qua google-api-python-client nếu có cấu hình)
3. Fallback an toàn về thư mục Google Drive dùng chung của cơ quan.
"""

import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote
import requests

from server.config import (
    BASE_DIR,
    GDRIVE_FOLDER_ID,
    GDRIVE_FOLDER_URL,
    GDRIVE_SERVICE_ACCOUNT_FILE,
    GDRIVE_WEB_APP_URL,
    SERVER_DOMAIN,
)
from server.logger import get_logger

logger = get_logger("gdrive_service")


def upload_via_apps_script(file_path: str, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Tải tệp lên Google Drive thông qua Google Apps Script Web App."""
    if not GDRIVE_WEB_APP_URL:
        return None

    path_obj = Path(file_path)
    if not path_obj.exists():
        logger.error(f"Tệp không tồn tại: {file_path}")
        return None

    name = filename or path_obj.name
    try:
        with open(path_obj, "rb") as f:
            encoded_bytes = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "folder_id": GDRIVE_FOLDER_ID,
            "filename": name,
            "base64": encoded_bytes,
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if name.endswith(".docx")
            else "application/octet-stream",
        }

        resp = requests.post(GDRIVE_WEB_APP_URL, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                file_url = data.get("file_url") or f"https://drive.google.com/file/d/{data.get('file_id')}/view?usp=sharing"
                return {
                    "success": True,
                    "file_id": data.get("file_id"),
                    "file_url": file_url,
                    "download_url": data.get("download_url", file_url),
                    "method": "apps_script",
                }
            else:
                logger.warning(f"Apps Script trả về lỗi: {data.get('message')}")
        else:
            logger.warning(f"Apps Script HTTP status: {resp.status_code} - {resp.text}")
    except Exception as ex:
        logger.error(f"Lỗi khi upload qua Apps Script: {ex}")
    return None


def upload_via_service_account(file_path: str, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Tải tệp lên Google Drive qua Service Account API nếu có tệp credentials."""
    creds_path = Path(GDRIVE_SERVICE_ACCOUNT_FILE)
    if not creds_path.is_absolute():
        creds_path = BASE_DIR / creds_path

    if not creds_path.exists():
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        credentials = service_account.Credentials.from_service_account_file(
            str(creds_path), scopes=SCOPES
        )
        service = build("drive", "v3", credentials=credentials)

        name = filename or Path(file_path).name
        file_metadata = {
            "name": name,
            "parents": [GDRIVE_FOLDER_ID],
        }
        media = MediaFileUpload(file_path, resumable=True)
        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink, webContentLink")
            .execute()
        )
        file_id = uploaded.get("id")
        file_url = uploaded.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

        # Cấp quyền xem cho bất kỳ ai có liên kết
        try:
            service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()
        except Exception:
            pass

        return {
            "success": True,
            "file_id": file_id,
            "file_url": file_url,
            "download_url": uploaded.get("webContentLink", file_url),
            "method": "service_account",
        }
    except ImportError:
        logger.debug("googleapiclient chưa cài đặt, bỏ qua upload Service Account.")
    except Exception as ex:
        logger.error(f"Lỗi upload qua Service Account: {ex}")
    return None


def upload_via_local_gdrive_sync(file_path: str, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Tải tệp vào thư mục Google Drive Desktop (G:) để ứng dụng Google Drive tự động đồng bộ lên đám mây."""
    candidate_paths = [
        Path(r"G:\My Drive\Du_thao_Chuyen_vien_ao"),
        Path(r"G:\My Drive"),
    ]
    name = filename or Path(file_path).name
    for base_p in candidate_paths:
        if base_p.exists() and base_p.is_dir():
            target_file = base_p / name
            try:
                import shutil
                shutil.copy2(file_path, target_file)
                logger.info(f"Đã sao chép '{name}' vào Google Drive Desktop: {target_file}")
                folder_url = GDRIVE_FOLDER_URL or f"https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}?usp=sharing"
                return {
                    "success": True,
                    "file_url": folder_url,
                    "local_sync_path": str(target_file),
                    "method": "google_drive_desktop",
                }
            except Exception as ex:
                logger.warning(f"Lỗi sao chép vào Google Drive Desktop: {ex}")
    return None


def upload_to_gdrive(file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Hàm tổng hợp để tải tệp lên Google Drive đám mây (Cloud Network Upload).
    Tự động thử các phương thức tải trực tuyến qua Internet:
    1. Google Apps Script Web App (nếu có GDRIVE_WEB_APP_URL)
    2. Google Service Account (nếu có credentials.json)
    3. Fallback: liên kết thư mục chung Google Drive của cơ quan.
    (Không dùng ổ đĩa ánh xạ theo yêu cầu của Cán bộ).
    """
    path_obj = Path(file_path)
    name = filename or path_obj.name

    # 1. Thử qua Google Apps Script Web App (Tải trực tiếp qua Internet)
    res = upload_via_apps_script(file_path, name)
    if res:
        logger.info(f"Đã upload trực tiếp '{name}' lên Google Drive Cloud (Apps Script): {res['file_url']}")
        return res

    # 2. Thử qua Google Cloud Service Account
    res = upload_via_service_account(file_path, name)
    if res:
        logger.info(f"Đã upload trực tiếp '{name}' lên Google Drive Cloud (Service Account): {res['file_url']}")
        return res

    # 3. Fallback: liên kết thư mục Google Drive của cơ quan
    folder_url = GDRIVE_FOLDER_URL or f"https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}?usp=sharing"
    server_link = None
    if SERVER_DOMAIN:
        try:
            rel_path = str(path_obj.resolve().relative_to(BASE_DIR.resolve())).replace("\\", "/")
            server_link = f"{SERVER_DOMAIN.rstrip('/')}/api/download?file_path={quote(rel_path)}"
        except Exception:
            pass

    return {
        "success": False,
        "file_url": folder_url,
        "folder_url": folder_url,
        "server_link": server_link,
        "method": "folder_link",
        "message": "Đã lưu tệp. Vui lòng mở thư mục Google Drive cơ quan để kiểm tra.",
    }
