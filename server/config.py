#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/config.py
================
Quản lý cấu hình toàn hệ thống Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải.
Tự động nạp thông số từ tệp .env tại thư mục gốc.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Xác định đường dẫn gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp file .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()

# --- CẤU HÌNH AI & OLLAMA LOCAL / CLOUD ---
AI_PROVIDER = os.getenv("AI_PROVIDER", "local").lower()  # "local" (Ollama) hoặc "cloud" (DeepSeek API)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_EXE_PATH = os.getenv("OLLAMA_EXE_PATH", r"C:\Users\Viet_Long\AppData\Local\Programs\Ollama\ollama.exe")
DEFAULT_LOCAL_MODEL = os.getenv("DEFAULT_LOCAL_MODEL", "qwen2.5:7b")

CLOUD_DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
CLOUD_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
CLOUD_DEEPSEEK_MODEL = "deepseek-chat"
CLOUD_DEEPSEEK_REASONER_MODEL = "deepseek-reasoner"

if AI_PROVIDER == "local":
    DEEPSEEK_API_KEY = "ollama"
    DEEPSEEK_BASE_URL = OLLAMA_BASE_URL
    DEEPSEEK_MODEL = DEFAULT_LOCAL_MODEL
    DEEPSEEK_REASONER_MODEL = "deepseek-r1:7b"
else:
    DEEPSEEK_API_KEY = CLOUD_DEEPSEEK_API_KEY
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", CLOUD_DEEPSEEK_BASE_URL)
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", CLOUD_DEEPSEEK_MODEL)
    DEEPSEEK_REASONER_MODEL = os.getenv("DEEPSEEK_REASONER_MODEL", CLOUD_DEEPSEEK_REASONER_MODEL)

# Danh mục các mô hình được tối ưu hoá cho Văn phòng Đảng uỷ xã Công Hải
SUPPORTED_MODELS = [
    {
        "id": "qwen2.5:3b",
        "name": "Qwen 2.5 (3B) — Siêu nhẹ",
        "provider": "local",
        "ram": "8GB RAM",
        "badge": "🟢 Local (RAM 8GB)",
        "desc": "Tốc độ nhanh nhất, phù hợp máy văn phòng không card đồ hoạ",
    },
    {
        "id": "qwen2.5:7b",
        "name": "Qwen 2.5 (7B) — Tiêu chuẩn",
        "provider": "local",
        "ram": "16GB RAM",
        "badge": "🔵 Local (RAM 16GB)",
        "desc": "Chất lượng văn phong hành chính xuất sắc, cân bằng nhất",
    },
    {
        "id": "deepseek-r1:7b",
        "name": "DeepSeek-R1 (7B) — Suy luận",
        "provider": "local",
        "ram": "16GB RAM",
        "badge": "🟣 Local (Thẩm định)",
        "desc": "Mô hình suy luận phản biện, cực mạnh phát hiện mâu thuẫn số liệu",
    },
    {
        "id": "qwen2.5:14b",
        "name": "Qwen 2.5 (14B) — Chuyên sâu",
        "provider": "local",
        "ram": "GPU 12GB / RAM 32GB",
        "badge": "🟠 Local (14B Khuyên dùng)",
        "desc": "Độ thông minh vượt trội, tư duy sắc bén, tối ưu hoàn hảo cho RTX 3060",
    },
    {
        "id": "deepseek-chat",
        "name": "DeepSeek Cloud (671B)",
        "provider": "cloud",
        "ram": "Mọi cấu hình",
        "badge": "☁️ Cloud API",
        "desc": "Siêu mô hình đám mây, dùng khi xử lý tài liệu công khai lớn",
    },
]

# --- CẤU HÌNH SERVER LOCAL ---
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# --- THÔNG TIN ĐƠN VỊ ĐẢNG BỘ XÃ CÔNG HẢI ---
CO_QUAN_CAP_TREN = os.getenv("CO_QUAN_CAP_TREN", "ĐẢNG BỘ TỈNH KHÁNH HOÀ")
CO_QUAN_BAN_HANH = os.getenv("CO_QUAN_BAN_HANH", "ĐẢNG UỶ XÃ CÔNG HẢI")
VAN_PHONG_NAME = os.getenv("VAN_PHONG_NAME", "VĂN PHÒNG")
DIA_DANH = os.getenv("DIA_DANH", "Công Hải")
NAM_HIEN_TAI = int(os.getenv("NAM_HIEN_TAI", "2026"))

# --- ĐƯỜNG DẪN THƯ MỤC LƯU TRỮ VĂN BẢN ---
VAN_BAN_DEN_DIR = BASE_DIR / "van_ban_den" / str(NAM_HIEN_TAI)
VAN_BAN_DU_THAO_DIR = BASE_DIR / "van_ban_du_thao" / str(NAM_HIEN_TAI)
DATA_DIR = BASE_DIR / "data"

# Các thư mục con của Văn bản đến
FOLDER_CAP_TREN = VAN_BAN_DEN_DIR / "cap_tren"
FOLDER_DU_THAO_CQ = VAN_BAN_DEN_DIR / "du_thao_co_quan"
FOLDER_BAO_CAO_CO_SO = VAN_BAN_DEN_DIR / "bao_cao_co_so"
FOLDER_BIEN_BAN_HOP = VAN_BAN_DEN_DIR / "bien_ban_hop"

# Đảm bảo các thư mục luôn sẵn sàng tồn tại
for folder in [
    VAN_BAN_DEN_DIR,
    VAN_BAN_DU_THAO_DIR,
    DATA_DIR,
    FOLDER_CAP_TREN,
    FOLDER_DU_THAO_CQ,
    FOLDER_BAO_CAO_CO_SO,
    FOLDER_BIEN_BAN_HOP,
    VAN_BAN_DU_THAO_DIR / "Cong_van",
    VAN_BAN_DU_THAO_DIR / "Ke_hoach",
    VAN_BAN_DU_THAO_DIR / "Bao_cao",
    VAN_BAN_DU_THAO_DIR / "Thong_bao",
    VAN_BAN_DU_THAO_DIR / "Nghi_quyet",
    VAN_BAN_DU_THAO_DIR / "Quyet_dinh",
    VAN_BAN_DU_THAO_DIR / "To_trinh",
]:
    folder.mkdir(parents=True, exist_ok=True)
