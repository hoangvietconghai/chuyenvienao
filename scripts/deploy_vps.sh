#!/bin/bash
# ==============================================================================
# KỊCH BẢN TRIỂN KHAI TỰ ĐỘNG CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI
# Dành cho VPS Ubuntu (Hỗ trợ Ubuntu 22.04 LTS / 24.04 LTS)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   BẮT ĐẦU TRIỂN KHAI HỆ THỐNG CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI   ${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# 1. Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[LỖI] Kịch bản này bắt buộc phải chạy dưới quyền root (sudo su)!${NC}"
  exit 1
fi

APP_DIR="/opt/chuyenvienao"
REPO_URL="https://github.com/hoangvietconghai/chuyenvienao.git"

# 2. Dọn sạch và xoá trắng toàn bộ dịch vụ cũ (Caddy, Apache, uvicorn cũ)
echo -e "${YELLOW}[DỌN SẠCH] Xoá trắng cấu hình cũ, dừng dịch vụ xung đột (Caddy, Apache, uvicorn)...${NC}"
systemctl stop chuyenvienao caddy apache2 nginx 2>/dev/null || true
systemctl disable caddy apache2 2>/dev/null || true
pkill -9 -f uvicorn 2>/dev/null || true
pkill -9 -f caddy 2>/dev/null || true
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" /tmp/.env.backup 2>/dev/null || true
fi
rm -rf "$APP_DIR"
rm -f /etc/nginx/sites-enabled/* /etc/nginx/sites-available/chuyenvienao /etc/nginx/sites-available/default
rm -f /etc/systemd/system/chuyenvienao.service
systemctl daemon-reload

# 3. Cập nhật hệ điều hành và cài đặt các gói phụ thuộc
echo -e "${BLUE}[1/7] Cập nhật Ubuntu & cài đặt các gói hệ thống cần thiết...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git nginx ufw curl libmagic1 sqlite3

# 4. Clone hoặc cập nhật mã nguồn từ GitHub
echo -e "${BLUE}[2/7] Tải mã nguồn mới nhất từ GitHub...${NC}"
if [ -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}Thư mục $APP_DIR đã tồn tại. Đang đồng bộ phiên bản mới nhất...${NC}"
    cd "$APP_DIR"
    git fetch origin main
    git reset --hard origin/main
else
    echo -e "${GREEN}Clone mới toàn bộ dự án vào $APP_DIR...${NC}"
    mkdir -p /opt
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# 5. Khởi tạo môi trường ảo Python & cài đặt thư viện
echo -e "${BLUE}[3/7] Khởi tạo môi trường ảo Python (.venv) và cài đặt thư viện...${NC}"
cd "$APP_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 6. Thiết lập tệp cấu hình môi trường (.env)
echo -e "${BLUE}[4/7] Thiết lập cấu hình hệ thống (.env)...${NC}"
if [ -f "/tmp/.env.backup" ]; then
    echo -e "${GREEN}Khôi phục cấu hình .env (Keys & Zalo tokens) từ bản sao lưu...${NC}"
    cp /tmp/.env.backup .env
elif [ -f "/tmp/.env" ]; then
    echo -e "${GREEN}Áp dụng cấu hình .env đã truyền qua SFTP...${NC}"
    cp /tmp/.env .env
elif [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        touch .env
    fi
fi

# Đảm bảo các tham số máy chủ chuẩn hoá trên VPS
sed -i 's/^SERVER_HOST=.*/SERVER_HOST=127.0.0.1/' .env || echo "SERVER_HOST=127.0.0.1" >> .env
sed -i 's/^SERVER_PORT=.*/SERVER_PORT=8000/' .env || echo "SERVER_PORT=8000" >> .env
sed -i 's/^DEBUG=.*/DEBUG=False/' .env || echo "DEBUG=False" >> .env

# Nếu chưa có GEMINI_API_KEY hoặc DEEPSEEK_API_KEY trong .env, nhắc cán bộ nhập (tự động bỏ qua sau 5 giây nếu không nhập)
if ! grep -q "^GEMINI_API_KEY=AIza" .env; then
    echo -e "${YELLOW}----------------------------------------------------------------------${NC}"
    echo -e "${YELLOW}Chưa phát hiện Google Gemini API Key trong .env.${NC}"
    read -t 5 -p ">> Nhập GEMINI_API_KEY (hoặc nhấn Enter để bỏ qua): " input_gemini_key || true
    echo ""
    if [ -n "$input_gemini_key" ]; then
        sed -i "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=$input_gemini_key/" .env || echo "GEMINI_API_KEY=$input_gemini_key" >> .env
    fi
fi

if ! grep -q "^DEEPSEEK_API_KEY=sk-" .env; then
    read -t 5 -p ">> Nhập DEEPSEEK_API_KEY (hoặc nhấn Enter để bỏ qua): " input_deepseek_key || true
    echo ""
    if [ -n "$input_deepseek_key" ]; then
        sed -i "s/^DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=$input_deepseek_key/" .env || echo "DEEPSEEK_API_KEY=$input_deepseek_key" >> .env
    fi
fi

# 7. Khởi tạo CSDL SQLite & nạp dữ liệu danh bạ
echo -e "${BLUE}[5/7] Khởi tạo cơ sở dữ liệu SQLite WAL và tài khoản cán bộ...${NC}"
mkdir -p "$APP_DIR/data"
.venv/bin/python -c "from server.services.db_service import init_database; init_database()"

# 8. Cấu hình dịch vụ chạy nền Systemd
echo -e "${BLUE}[6/7] Cấu hình dịch vụ nền Systemd (tự động khởi động cùng VPS)...${NC}"
cat << 'EOF' > /etc/systemd/system/chuyenvienao.service
[Unit]
Description=Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chuyenvienao
ExecStart=/opt/chuyenvienao/.venv/bin/uvicorn server.app:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=3
EnvironmentFile=/opt/chuyenvienao/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chuyenvienao
systemctl restart chuyenvienao

# 9. Cấu hình Nginx Reverse Proxy (Cổng 80)
echo -e "${BLUE}[7/7] Cấu hình Nginx Reverse Proxy và Tường lửa UFW...${NC}"

# Dừng và giải phóng cổng 80 nếu có dịch vụ web cũ (Caddy, Apache) đang chiếm
echo -e "${BLUE}Giải phóng cổng 80 (dừng Caddy, Apache nếu có)...${NC}"
systemctl stop caddy apache2 2>/dev/null || true
systemctl disable caddy apache2 2>/dev/null || true
pkill -9 -f caddy 2>/dev/null || true

cat << 'EOF' > /etc/nginx/sites-available/chuyenvienao
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/chuyenvienao /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Mở cổng tường lửa an toàn
ufw allow 22/tcp > /dev/null 2>&1 || true
ufw allow 80/tcp > /dev/null 2>&1 || true
ufw allow 443/tcp > /dev/null 2>&1 || true
ufw --force enable > /dev/null 2>&1 || true

# 10. Kiểm tra sức khỏe dịch vụ
echo -e "${BLUE}Đang đối soát tình trạng hoạt động...${NC}"
sleep 3
HEALTH_STATUS=$(curl -s http://127.0.0.1:8000/health || echo "error")

echo ""
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 TRIỂN KHAI THÀNH CÔNG HỆ THỐNG LÊN MÁY CHỦ VPS!                          ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "🔹 Trạng thái Health Check: ${YELLOW}$HEALTH_STATUS${NC}"
echo -e "🔹 Địa chỉ truy cập Web:     ${GREEN}http://45.119.82.227${NC}"
echo -e "🔹 Đăng nhập Admin:         Số điện thoại ${GREEN}0327777707${NC} (Đồng chí Ngô Hoàng Việt)"
echo -e "🔹 Quản lý dịch vụ:         ${YELLOW}systemctl status chuyenvienao${NC}"
echo -e "🔹 Xem log hệ thống:        ${YELLOW}journalctl -u chuyenvienao -f${NC}"
echo -e "${GREEN}==============================================================================${NC}"

