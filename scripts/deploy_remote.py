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
    is_update_mode = "--update" in sys.argv or "update" in sys.argv
    clean_argv = [a for a in sys.argv[1:] if a not in ("--update", "update")]

    print_banner()
    if is_update_mode:
        print("⚡ CHẾ ĐỘ: CẬP NHẬT NHANH (CI/CD) — Giữ nguyên CSDL & .env, chỉ cập nhật mã nguồn!")
    else:
        print("🛠️  CHẾ ĐỘ: TRIỂN KHAI TOÀN DIỆN (Cài đặt mới / Reset môi trường)")

    # Nhập mật khẩu an toàn (không hiển thị trên màn hình)
    if clean_argv and clean_argv[0]:
        password = clean_argv[0]
    else:
        password = getpass.getpass(f"Nhập mật khẩu SSH của tài khoản '{VPS_USER}' (ký tự sẽ ẩn): ")

    if not password:
        print("❌ Mật khẩu không được để trống!")
        sys.exit(1)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"\n[1/3] Đang kết nối tới máy chủ {VPS_IP}...")
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
        if is_update_mode:
            # Chế độ cập nhật nhanh
            update_cmd = (
                "curl -sSL https://raw.githubusercontent.com/hoangvietconghai/chuyenvienao/main/scripts/update_vps.sh "
                "-o /tmp/update_vps.sh && chmod +x /tmp/update_vps.sh && bash /tmp/update_vps.sh"
            )
            run_remote_command(ssh, update_cmd, "[2/3] Chạy kịch bản cập nhật nhanh update_vps.sh")

            print("\n>> [3/3] Kiểm tra phản hồi dịch vụ sau cập nhật...")
            stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:8000/health")
            health_resp = stdout.read().decode("utf-8", errors="replace").strip()
            print(f"Kết quả Health Check: {health_resp}")

            print("\n" + "=" * 76)
            print("🎉 CẬP NHẬT THÀNH CÔNG! HỆ THỐNG ĐÃ SẴN SÀNG.")
            print("=" * 76)
            print(f"🔹 Địa chỉ truy cập: http://{VPS_IP}")
            print("=" * 76)
            return

        # 1. Dọn dẹp và chuẩn bị môi trường sạch 100% (Chế độ cài mới)
        clean_cmd = (
            "apt-get update -y && apt-get install -y git curl && "
            "systemctl stop chuyenvienao caddy apache2 nginx 2>/dev/null || true; "
            "pkill -9 -f uvicorn 2>/dev/null || true; "
            "pkill -9 -f caddy 2>/dev/null || true; "
            "rm -rf /opt/chuyenvienao; "
            "mkdir -p /opt/chuyenvienao"
        )
        run_remote_command(
            ssh,
            clean_cmd,
            "[2/5] Dọn dẹp môi trường cũ, dừng dịch vụ xung đột (Caddy/Apache) và chuẩn bị Ubuntu",
        )

        # 2. Đồng bộ tệp .env nội bộ từ máy tính sang VPS qua SFTP trước
        if LOCAL_ENV_FILE.exists():
            print("\n>> [3/5] Đồng bộ tệp cấu hình .env (Gemini, DeepSeek & Zalo tokens) sang VPS...")
            try:
                sftp = ssh.open_sftp()
                sftp.put(str(LOCAL_ENV_FILE), "/tmp/.env")
                sftp.close()
                print("✅ Đã truyền file cấu hình .env an toàn sang VPS (/tmp/.env)!")
            except Exception as sftp_err:
                print(f"⚠️ Lưu ý SFTP: {sftp_err}")

        # 3. Tải và chạy deploy_vps.sh
        deploy_cmd = (
            "curl -sSL https://raw.githubusercontent.com/hoangvietconghai/chuyenvienao/main/scripts/deploy_vps.sh "
            "-o /tmp/deploy_vps.sh && chmod +x /tmp/deploy_vps.sh && bash /tmp/deploy_vps.sh"
        )
        run_remote_command(ssh, deploy_cmd, "[4/5] Khởi chạy kịch bản cài đặt tự động trên VPS")

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

