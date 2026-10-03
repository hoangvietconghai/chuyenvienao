# HƯỚNG DẪN CÀI ĐẶT & TRIỂN KHAI CHUYÊN VIÊN ẢO TRÊN MÁY TÍNH MỚI

## Yêu cầu hệ thống

### Phần mềm bắt buộc
- **Google Antigravity IDE** (hoặc Antigravity 2.0) — Đã cài đặt và kích hoạt
- **Python** >= 3.10 (để chạy scripts xuất file Word .docx)
- **Git** (để clone dự án từ repository)
- **Google Chrome** (để tương tác với Hệ thống Quản lý Văn bản qua Persistent Profile)

### Phần mềm khuyến nghị
- **Microsoft Word** hoặc **LibreOffice Writer** (để mở và kiểm tra file .docx xuất ra)

---

## Bước 1: Clone dự án

```powershell
# Trên PowerShell
git clone <URL_REPOSITORY> "D:\Chuyên viên ảo"
```

Hoặc tải trực tiếp thư mục dự án và giải nén vào ổ D:.

---

## Bước 2: Khởi tạo môi trường tự động (1-Click)

Đồng chí có thể chọn 1 trong 2 cách cực kỳ nhanh chóng:

* **Cách 1 (Khuyến nghị cho Windows):** Click đúp chuột vào tệp `setup.bat` tại thư mục gốc.
* **Cách 2 (Bằng PowerShell):**
  ```powershell
  cd "D:\Chuyên viên ảo"
  .\setup.ps1
  ```

*Tệp cài đặt sẽ tự động: kiểm tra Python, tạo môi trường ảo `.venv`, cài đặt thư viện `python-docx`, tạo sẵn 8 thư mục văn bản đầu ra và chạy thử nghiệm sinh file Word mẫu.*

---

## Bước 3: Mở dự án trong Antigravity IDE

1. Mở **Antigravity IDE**
2. Chọn **Open Folder** → Chọn thư mục `D:\Chuyên viên ảo`
3. Hệ thống tự động nhận:
   - `AGENTS.md` (quy tắc vận hành luôn active)
   - `.agents/skills/` (6 skills nghiệp vụ, load theo yêu cầu)

---

## Bước 4: Đăng nhập Chrome Profile cho Hệ thống QLVB

> **LƯU Ý AN TOÀN:** Chuyên viên ảo **TUYỆT ĐỐI KHÔNG** đụng đến mật khẩu.  
> Cán bộ tự đăng nhập sẵn vào hệ thống QLVB bằng Chrome Profile cá nhân.

1. Mở **Google Chrome**
2. Đăng nhập vào Hệ thống Quản lý Văn bản của Tỉnh uỷ Khánh Hoà
3. Đảm bảo session đăng nhập còn hiệu lực
4. Agent sẽ sử dụng Chrome Profile (`user-data-dir`) đã đăng nhập sẵn

---

## Bước 5: Kiểm tra hoạt động

Thử yêu cầu Agent:

```
Soạn công văn giao UBND xã tham mưu Kế hoạch triển khai thực hiện 
Kế hoạch số 101-KH/TU ngày 15/6/2026 của Ban Thường vụ Tỉnh uỷ 
về hành động 100 ngày giải quyết điểm nghẽn chuyển đổi số.
```

**Kết quả mong đợi:**
- Agent tự đọc skill `quy-chuan-nen-tang` và `cong-van-giao-viec`
- Xuất file .docx đúng thể thức HD 05-HD/VPTW
- File lưu tại `van_ban_du_thao/2026/Cong_van/`

---

## Bước 6: Bổ sung dữ liệu địa phương (QUAN TRỌNG)

Cán bộ Văn phòng Đảng uỷ cần mở file sau và **điền đầy đủ** các mục `...`:

📄 [references/tong_quan_xa_cong_hai.md](./references/tong_quan_xa_cong_hai.md)

Bao gồm:
- Diện tích, dân số, kinh tế, hạ tầng xã Công Hải
- Danh sách chi bộ trực thuộc, số đảng viên
- Nhân sự chủ chốt (đã có Bí thư, Phó Bí thư; cần bổ sung các vị trí còn lại)
- Chỉ tiêu kết nạp đảng viên, kết quả phân loại năm gần nhất
- Thông tin chuyển đổi số

---

## Cấu trúc thư mục hoàn chỉnh sau cài đặt

```text
D:\Chuyên viên ảo\
├── AGENTS.md                              ← Quy tắc mặc định (auto-load)
├── README.md                              ← Tài liệu tổng quan dự án
├── requirements.txt                       ← Python dependencies
├── SETUP.md                               ← File này
│
├── .agents/                               ← Cấu hình Antigravity Skills
│   └── skills/
│       ├── quy-chuan-nen-tang/SKILL.md
│       ├── cong-van-giao-viec/SKILL.md
│       ├── thong-bao-ket-luan/SKILL.md
│       ├── ke-hoach-nghi-quyet/SKILL.md
│       ├── bao-cao-to-trinh/SKILL.md
│       └── tham-dinh-van-ban/SKILL.md
│
├── skills/                                ← Nội dung chi tiết các Skills
│   ├── Skill_Core_The_thuc_Chung.md
│   ├── Skill_Cong_van_Giao_viec.md
│   ├── Skill_Thong_bao_Ket_luan.md
│   ├── Skill_Ke_hoach_Nghi_quyet.md
│   ├── Skill_Bao_cao_To_trinh.md
│   └── Skill_Tham_dinh_Van_ban.md
│
├── references/                            ← Tài liệu tra cứu
│   ├── Cam_nang_Nghiep_vu_Tham_muu_Cap_uy.md
│   ├── tong_quan_xa_cong_hai.md
│   ├── Mẫu văn bản thông dụng/           (18 file mẫu)
│   └── Thông tin thông dụng/
│
├── scripts/                               ← Công cụ tự động hoá
│   ├── export_docx.py
│   └── generate_kh83_documents.py
│
├── van_ban_den/2026/                      ← Kho văn bản đến
└── van_ban_du_thao/2026/                  ← Kho văn bản soạn thảo
    ├── Cong_van/
    ├── Ke_hoach/
    ├── Nghi_quyet/
    ├── Quyet_dinh/
    ├── Ket_luan/
    ├── Thong_bao/
    ├── Bao_cao/
    └── To_trinh/
```

---

## Xử lý sự cố thường gặp

| Sự cố | Giải pháp |
|:---|:---|
| Agent không nhận skills | Kiểm tra thư mục `.agents/` có đúng vị trí gốc dự án không |
| Lỗi `ModuleNotFoundError: python-docx` | Chạy `pip install python-docx>=1.1.0` |
| File .docx bị lỗi font | Cài font **Times New Roman** trên máy |
| Agent nhắc đến cấp huyện | Báo lỗi để bổ sung Anti-Hallucination Guardrail |
| Chrome session hết hạn | Cán bộ tự đăng nhập lại Chrome (Agent KHÔNG đụng mật khẩu) |
