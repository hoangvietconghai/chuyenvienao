#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/migrate_ollama_to_d.py
==============================
Chuyển đổi lưu trữ mô hình Ollama từ ổ C (C:\\Users\\Viet_Long\\.ollama\\models)
sang ổ D (D:\\ollama_models) để giải phóng ngay ~11.3 GB cho ổ C.
"""

import os
import sys
import shutil
import subprocess
import time
import urllib.request
import json

sys.stdout.reconfigure(encoding="utf-8")

SOURCE_DIR = r"C:\Users\Viet_Long\.ollama\models"
TARGET_DIR = r"D:\ollama_models"
OLLAMA_APP_EXE = r"C:\Users\Viet_Long\AppData\Local\Programs\Ollama\ollama app.exe"
OLLAMA_CLI_EXE = r"C:\Users\Viet_Long\AppData\Local\Programs\Ollama\ollama.exe"

def get_dir_size(path):
    total = 0
    if not os.path.exists(path):
        return 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except Exception:
                pass
    return total

def print_disk_usage():
    c_usage = shutil.disk_usage("C:\\")
    d_usage = shutil.disk_usage("D:\\")
    print(f"[*] Ổ C hiện tại: Trống {c_usage.free / 1e9:.2f} GB / Tổng {c_usage.total / 1e9:.2f} GB")
    print(f"[*] Ổ D hiện tại: Trống {d_usage.free / 1e9:.2f} GB / Tổng {d_usage.total / 1e9:.2f} GB")

def stop_ollama():
    print("[1/6] Đang dừng tiến trình Ollama để tránh xung đột file...")
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe"], capture_output=True)
    time.sleep(2)
    print("      -> Đã dừng các tiến trình Ollama thành công.")

def copy_models():
    source_size = get_dir_size(SOURCE_DIR)
    print(f"[2/6] Dung lượng mô hình cần chuyển: {source_size / 1e9:.2f} GB")
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    print(f"      Đang sao chép từ {SOURCE_DIR} sang {TARGET_DIR}...")
    # Dùng robocopy cho tốc độ cao và an toàn nhất trên Windows
    cmd = [
        "robocopy",
        SOURCE_DIR,
        TARGET_DIR,
        "/E",
        "/R:2",
        "/W:2",
        "/NFL",
        "/NDL",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    # Robocopy trả mã < 8 là thành công
    if res.returncode >= 8:
        raise RuntimeError(f"Lỗi khi sao chép thư mục: {res.stderr or res.stdout}")
    
    target_size = get_dir_size(TARGET_DIR)
    print(f"      -> Sao chép hoàn tất! Dung lượng đích: {target_size / 1e9:.2f} GB")
    if abs(source_size - target_size) > 50 * 1024 * 1024: # chênh lệch > 50MB
        raise RuntimeError("Cảnh báo: Dung lượng đích không khớp với nguồn!")

def setup_environment_and_junction():
    print("[3/6] Cấu hình biến môi trường OLLAMA_MODELS = D:\\ollama_models...")
    # 1. Đặt biến môi trường User vĩnh viễn trong Windows Registry
    ps_cmd = "[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'D:\\ollama_models', 'User')"
    subprocess.run(["powershell", "-Command", ps_cmd], check=True)
    os.environ["OLLAMA_MODELS"] = TARGET_DIR
    print("      -> Đã lưu biến môi trường OLLAMA_MODELS vào Windows User Environment.")

    print("[4/6] Xoá dữ liệu cũ trên ổ C và tạo liên kết Junction...")
    # Xoá SOURCE_DIR cũ
    shutil.rmtree(SOURCE_DIR, ignore_errors=True)
    
    # Tạo Junction link: C:\Users\Viet_Long\.ollama\models -> D:\ollama_models
    mklink_cmd = f'cmd /c mklink /J "{SOURCE_DIR}" "{TARGET_DIR}"'
    res = subprocess.run(mklink_cmd, shell=True, capture_output=True, text=True)
    print(f"      -> Kết quả tạo Junction: {res.stdout.strip()}")

def restart_ollama():
    print("[5/6] Đang khởi động lại Ollama với cấu hình mới...")
    # Chạy ollama app.exe
    env = os.environ.copy()
    env["OLLAMA_MODELS"] = TARGET_DIR
    if os.path.exists(OLLAMA_APP_EXE):
        subprocess.Popen([OLLAMA_APP_EXE], env=env)
    else:
        subprocess.Popen([OLLAMA_CLI_EXE, "serve"], env=env)
    
    print("      Đang đợi Ollama khởi động...")
    ready = False
    for i in range(15):
        time.sleep(2)
        try:
            req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
            if req.status == 200:
                data = json.loads(req.read().decode())
                models = [m.get("name") for m in data.get("models", [])]
                print(f"      -> Ollama đã hoạt động trở lại! Danh sách mô hình tìm thấy: {models}")
                ready = True
                break
        except Exception:
            pass

    if not ready:
        print("      (!) Chưa nhận được phản hồi từ Ollama qua API, vui lòng kiểm tra sau.")

def main():
    print("=== BẮT ĐẦU CHUYỂN DỮ LIỆU OLLAMA SANG Ổ D ===")
    print_disk_usage()
    
    stop_ollama()
    copy_models()
    setup_environment_and_junction()
    restart_ollama()
    
    print("\n[6/6] KẾT QUẢ SAU KHI GIẢI PHÓNG Ổ C:")
    print_disk_usage()
    print("=== HOÀN TẤT THÀNH CÔNG ===")

if __name__ == "__main__":
    main()
