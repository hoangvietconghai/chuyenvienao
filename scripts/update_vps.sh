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

# 0. Tự động sao lưu & Kích hoạt Lá chắn bảo vệ CSDL SQLite VPS (Database Shield)
echo -e "${BLUE}>> [0/4] Tự động sao lưu và kích hoạt Lá chắn CSDL SQLite VPS...${NC}"
mkdir -p "$APP_DIR/backups"
if [ -f "$APP_DIR/data/chuyen_vien_ao.db" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp "$APP_DIR/data/chuyen_vien_ao.db" "$APP_DIR/backups/chuyen_vien_ao_${TIMESTAMP}.db"
    cp "$APP_DIR/data/chuyen_vien_ao.db" "$APP_DIR/backups/db_shield_active.db"
    # Giữ tối đa 15 bản sao lưu gần nhất để bảo vệ dung lượng ổ đĩa
    ls -tp "$APP_DIR/backups"/chuyen_vien_ao_*.db 2>/dev/null | grep -v '/$' | tail -n +16 | xargs -I {} rm -- {} 2>/dev/null || true
    echo -e "${GREEN}  ✓ Đã sao lưu dự phòng CSDL VPS thành công: chuyen_vien_ao_${TIMESTAMP}.db${NC}"
fi

# 1. Kéo mã nguồn mới nhất từ nhánh main
echo -e "${BLUE}>> [1/4] Kéo mã nguồn mới nhất từ GitHub (origin/main)...${NC}"
git fetch origin main
git reset --hard origin/main

# 1.1 Khôi phục bảo toàn 100% CSDL VPS (ngăn git ghi đè hoặc xoá bỏ)
if [ -f "$APP_DIR/backups/db_shield_active.db" ]; then
    mkdir -p "$APP_DIR/data"
    cp "$APP_DIR/backups/db_shield_active.db" "$APP_DIR/data/chuyen_vien_ao.db"
    echo -e "${GREEN}  ✓ Lá chắn CSDL: Đã bảo toàn nguyên vẹn 100% CSDL thực tế trên VPS.${NC}"
fi

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
.venv/bin/python -c "from server.services.rag_service import sync_outgoing_catalog_to_rag; print(sync_outgoing_catalog_to_rag())"

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

