#!/bin/bash
# ==============================================================================
# KỊCH BẢN CẬP NHẬT NHANH (CI/CD) CHO CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ
# Không xoá dữ liệu, không ghi đè .env, hoàn tất chỉ trong 3 - 5 giây.
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_DIR="/opt/chuyenvienao"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}  🚀 BẮT ĐẦU CẬP NHẬT TỰ ĐỘNG MÃ NGUỒN CHUYÊN VIÊN ẢO (CI/CD)        ${NC}"
echo -e "${BLUE}======================================================================${NC}"

if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}[LỖI] Không tìm thấy thư mục $APP_DIR trên máy chủ!${NC}"
    exit 1
fi

cd "$APP_DIR"

# 1. Kéo mã nguồn mới nhất từ nhánh main
echo -e "${BLUE}>> [1/4] Kéo mã nguồn mới nhất từ GitHub (origin/main)...${NC}"
git fetch origin main
git reset --hard origin/main

# 2. Cài đặt các thư viện mới nếu có thay đổi trong requirements.txt
echo -e "${BLUE}>> [2/4] Kiểm tra và cập nhật các gói thư viện Python...${NC}"
if [ -d ".venv" ]; then
    .venv/bin/pip install -r requirements.txt --quiet
else
    echo -e "${YELLOW}Chưa có .venv, khởi tạo môi trường ảo mới...${NC}"
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 3. Đồng bộ cơ sở dữ liệu (Database Migration & WAL setup)
echo -e "${BLUE}>> [3/4] Kiểm tra và đối soát cơ sở dữ liệu SQLite WAL...${NC}"
.venv/bin/python -c "from server.services.db_service import init_database; init_database()"

# 4. Khởi động lại dịch vụ hệ thống
echo -e "${BLUE}>> [4/4] Khởi động lại dịch vụ hệ thống chuyenvienao.service...${NC}"
systemctl daemon-reload
systemctl restart chuyenvienao

# Chờ 2 giây và kiểm tra sức khoẻ hệ thống
sleep 2
HEALTH=$(curl -s http://127.0.0.1:8000/health || echo '{"status":"error"}')

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  ✅ CẬP NHẬT THÀNH CÔNG!                                             ${NC}"
echo -e "🔹 Trạng thái dịch vụ: ${YELLOW}$HEALTH${NC}"
echo -e "🔹 Thời gian hoàn tất: Khoảng 3 giây"
echo -e "${GREEN}======================================================================${NC}"

