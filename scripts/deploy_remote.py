#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/deploy_remote.py
========================
Kịch bản hỗ trợ cán bộ tự động triển khai Chuyên viên Ảo lên VPS qua SSH.
Chạy trực tiếp từ máy tính cán bộ (Human-in-the-Loop):
- Sử dụng thư viện paramiko kết nối an toàn.
- Yêu cầu cán bộ nhập mật khẩu qua getpass (bảo mật, không lưu mật khẩu vào mã nguồn).
- Tự động đồng bộ tệp .env (Gemini & DeepSeek keys) sang VPS qua SFTP.
- Kích hoạt kịch bản cài đặt tự động deploy_vps.sh và theo dõi tiến trình trực tiếp.
"""

import getpass
import os
import sys
import time
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Đang cài đặt thư viện paramiko...")
    os.system(f"{sys.executable} -m pip install paramiko")
    import paramiko


VPS_IP = "45.119.82.227"
VPS_PORT = 22
VPS_USER = "root"
REMOTE_APP_DIR = "/opt/chuyenvienao"
LOCAL_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def print_banner():
    print("=" * 76)
    print("   TRIỂN KHAI TỰ ĐỘNG CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ LÊN VPS (UBUNTU)    ")
    print("=" * 76)
    print(f"🔹 Máy chủ đích: {VPS_USER}@{VPS_IP}:{VPS_PORT}")
    print(f"🔹 Thư mục ứng dụng trên VPS: {REMOTE_APP_DIR}")
    print("=" * 76)


def run_remote_command(ssh: paramiko.SSHClient, command: str, step_title: str) -> bool:
    print(f"\n>> {step_title}...")
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    # In trực tiếp output thời gian thực
    for line in iter(stdout.readline, ""):
        print(line, end="")
    
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        err = stderr.read().decode("utf-8", errors="replace")
        print(f"⚠️ Lỗi (mã {exit_status}): {err}")
        return False
    return True


def main():
    print_banner()

    # Nhập mật khẩu an toàn (không hiển thị trên màn hình)
    if len(sys.argv) > 1 and sys.argv[1]:
        password = sys.argv[1]
    else:
        password = getpass.getpass(f"Nhập mật khẩu SSH của tài khoản '{VPS_USER}' (ký tự sẽ ẩn): ")

    if not password:
        print("❌ Mật khẩu không được để trống!")
        sys.exit(1)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"\n[1/5] Đang kết nối tới máy chủ {VPS_IP}...")
    try:
        ssh.connect(
            hostname=VPS_IP,
            port=VPS_PORT,
            username=VPS_USER,
            password=password,
            timeout=15.0,
            allow_agent=False,
            look_for_keys=False,
        )
        print("✅ Kết nối SSH thành công!")
    except Exception as e:
        print(f"❌ Không thể kết nối tới VPS: {e}")
        sys.exit(1)

    try:
        # 1. Dọn dẹp và chuẩn bị môi trường
        run_remote_command(
            ssh,
            "apt-get update -y && apt-get install -y git curl",
            "[2/5] Cập nhật Ubuntu và kiểm tra công cụ Git/Curl",
        )

        # 2. Tải và chạy deploy_vps.sh
        deploy_cmd = (
            "curl -sSL https://raw.githubusercontent.com/hoangvietconghai/chuyenvienao/main/scripts/deploy_vps.sh "
            "-o /tmp/deploy_vps.sh && chmod +x /tmp/deploy_vps.sh && bash /tmp/deploy_vps.sh"
        )
        run_remote_command(ssh, deploy_cmd, "[3/5] Khởi chạy kịch bản cài đặt tự động trên VPS")

        # 3. Đồng bộ tệp .env nội bộ từ máy tính sang VPS qua SFTP (nếu có)
        if LOCAL_ENV_FILE.exists():
            print("\n>> [4/5] Đồng bộ cấu hình .env (Gemini & DeepSeek keys) sang VPS...")
            try:
                sftp = ssh.open_sftp()
                sftp.put(str(LOCAL_ENV_FILE), f"{REMOTE_APP_DIR}/.env")
                sftp.close()
                print("✅ Đã truyền file cấu hình .env an toàn sang VPS!")
                # Khởi động lại dịch vụ để nhận .env mới
                ssh.exec_command("systemctl restart chuyenvienao")
                time.sleep(2)
            except Exception as sftp_err:
                print(f"⚠️ Lưu ý SFTP: {sftp_err}")

        # 4. Kiểm tra dịch vụ
        print("\n>> [5/5] Kiểm tra phản hồi dịch vụ từ VPS...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/health")
        health_resp = stdout.read().decode("utf-8", errors="replace").strip()
        print(f"Kết quả Health Check nội bộ: {health_resp}")

        print("\n" + "=" * 76)
        print("🎉 CHÚC MỪNG ĐỒNG CHÍ! HỆ THỐNG ĐÃ ĐƯỢC TRIỂN KHAI HOÀN TẤT LÊN VPS!")
        print("=" * 76)
        print(f"🔹 Địa chỉ truy cập: http://{VPS_IP}")
        print("🔹 Tài khoản Admin:  0327777707 (Đồng chí Ngô Hoàng Việt)")
        print("=" * 76)

    finally:
        ssh.close()
        print("\nĐã đóng phiên kết nối SSH an toàn.")


if __name__ == "__main__":
    main()
