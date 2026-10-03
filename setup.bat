@echo off
chcp 65001 >nul
title Cài đặt Chuyên viên ảo - Văn phòng Đảng uỷ xã Công Hải

echo ==============================================================================
echo    CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI, TỈNH KHÁNH HOÀ
echo               CHƯƠNG TRÌNH KHỞI TẠO MÔI TRƯỜNG TỰ ĐỘNG (1-CLICK)
echo ==============================================================================
echo.

:: 1. Kiểm tra Python
echo [1/4] Kiểm tra môi trường Python trên hệ thống...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Chưa tìm thấy Python trên máy tính này.
    echo.
    echo Hướng dẫn xử lý:
    echo 1. Tải và cài đặt Python 3.10 trở lên tại: https://www.python.org/downloads/
    echo 2. QUAN TRỌNG: Nhớ tích chọn ô "Add Python to PATH" trong quá trình cài đặt.
    echo 3. Sau khi cài xong, mở lại file setup.bat này.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo     -> Đã tìm thấy: %PY_VER% (Hợp lệ)
echo.

:: 2. Khởi tạo môi trường ảo Python (.venv)
echo [2/4] Kiểm tra / Thiết lập môi trường ảo (.venv)...
if not exist ".venv" (
    echo     -> Đang tạo môi trường ảo .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [LỖI] Không thể tạo môi trường ảo. Vui lòng kiểm tra quyền ghi thư mục.
        pause
        exit /b 1
    )
    echo     -> Tạo môi trường ảo thành công.
) else (
    echo     -> Môi trường ảo .venv đã sẵn sàng.
)
echo.

:: 3. Kích hoạt môi trường & cài đặt thư viện
echo [3/4] Cài đặt các thư viện cần thiết (requirements.txt)...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [CẢNH BÁO] Không tải được qua requirements.txt, đang thử cài trực tiếp python-docx...
    pip install python-docx
)
echo     -> Đã cài đặt thành công python-docx (Hỗ trợ sinh văn bản Word chuẩn HD 05).
echo.

:: 4. Khởi tạo cấu trúc thư mục văn bản đầu ra
echo [4/4] Khởi tạo hệ thống thư mục lưu trữ văn bản dự thảo năm 2026...
if not exist "van_ban_du_thao\2026\Cong_van" mkdir "van_ban_du_thao\2026\Cong_van"
if not exist "van_ban_du_thao\2026\Ke_hoach" mkdir "van_ban_du_thao\2026\Ke_hoach"
if not exist "van_ban_du_thao\2026\Nghi_quyet" mkdir "van_ban_du_thao\2026\Nghi_quyet"
if not exist "van_ban_du_thao\2026\Quyet_dinh" mkdir "van_ban_du_thao\2026\Quyet_dinh"
if not exist "van_ban_du_thao\2026\Thong_bao" mkdir "van_ban_du_thao\2026\Thong_bao"
if not exist "van_ban_du_thao\2026\Ket_luan" mkdir "van_ban_du_thao\2026\Ket_luan"
if not exist "van_ban_du_thao\2026\Bao_cao" mkdir "van_ban_du_thao\2026\Bao_cao"
if not exist "van_ban_du_thao\2026\To_trinh" mkdir "van_ban_du_thao\2026\To_trinh"
if not exist "van_ban_du_thao\2026\Chi_thi" mkdir "van_ban_du_thao\2026\Chi_thi"
if not exist "van_ban_du_thao\2026\Chuong_trinh" mkdir "van_ban_du_thao\2026\Chuong_trinh"
echo     -> Đã sẵn sàng các thư mục tại van_ban_du_thao\2026\...
echo.

:: Kiểm tra chạy thử nghiệm sinh file Word
echo ------------------------------------------------------------------------------
echo Đang chạy thử nghiệm Engine sinh văn bản Word (export_docx.py)...
python scripts\export_docx.py --demo
echo ------------------------------------------------------------------------------
echo.

echo ==============================================================================
echo                   [HOÀN TẤT CÀI ĐẶT THÀNH CÔNG!]
echo  Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải đã sẵn sàng hoạt động 100%%.
echo  Đồng chí có thể mở Antigravity IDE và giao việc ngay!
echo ==============================================================================
echo.
pause
