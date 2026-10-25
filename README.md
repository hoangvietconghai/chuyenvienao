# HỆ THỐNG TRỢ LÝ AI THAM MƯU TỔNG HỢP & SOẠN THẢO VĂN BẢN ĐẢNG UỶ XÃ CÔNG HẢI
*(Chuẩn thể thức Hướng dẫn số 05-HD/VPTW năm 2026 của Văn phòng Trung ương Đảng & Quy chế làm việc Đảng bộ xã)*

Hệ thống được thiết kế theo **Mô hình Hạt nhân & Kỹ năng Chuyên sâu Đa tầng (Core & Multi-Tier Advisory Skills)**, đóng vai trò là **Trợ lý Tham mưu Tổng hợp Toàn diện** cho Thường trực Đảng uỷ, Ban Thường vụ Đảng uỷ và Ban Chấp hành Đảng bộ xã Công Hải, tỉnh Khánh Hoà (trực thuộc trực tiếp Tỉnh uỷ Khánh Hoà theo mô hình chính quyền địa phương 02 cấp từ 01/7/2025).

---

## 🚀 3 KÊNH GIAO TIẾP & TƯƠNG TÁC CỦA HỆ THỐNG

Hệ thống hỗ trợ 03 phương án tương tác linh hoạt, đồng bộ:

```
                  ┌──────────────────────────────────────────────┐
                  │    CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ          │
                  │   (Lõi xử lý quy chuẩn Hướng dẫn 05-HD/VPTW)  │
                  └──────┬───────────────┬──────────────┬────────┘
                         │               │              │
       ┌─────────────────┴─┐   ┌─────────┴────────┐   ┌─┴────────────────┐
       │ 1. Antigravity IDE │   │  2. Giao diện Web │   │ 3. Zalo Chatbot  │
       │    (Cán bộ kỹ thuật│   │   (Localhost:8000│   │    (Di động 24/7,│
       │     & Lập trình)   │   │    Văn phòng làm)│   │    đám mây Drive)│
       └───────────────────┘   └──────────────────┘   └──────────────────┘
```

1. **Chat trực tiếp với Google Antigravity:** Dành cho cán bộ quản trị hệ thống, làm việc chuyên sâu trong môi trường phát triển và kiểm thử văn bản.
2. **Giao diện Web Chuyên nghiệp (`http://localhost:8000`):** Giao diện đồ hoạ cho cán bộ Văn phòng Đảng uỷ: tải tệp drag-and-drop, bóc tách 5 Rõ, đối soát số liệu, duyệt dự thảo và xuất Word (.docx).
3. **Chatbot Zalo Di động 24/7 (`scripts/run_zalo_bot.py`):**
   - Tiếp nhận lệnh chỉ đạo và văn bản đính kèm trực tiếp từ điện thoại của cán bộ.
   - Nhận diện ý định và tự động soạn thảo dự thảo chuẩn Hướng dẫn 05-HD/VPTW.
   - **Đẩy tệp trực tiếp lên Google Drive đám mây:** Tự động upload tệp Word qua Google Apps Script Web App và trả liên kết xem/tải trực tiếp về Zalo (không phụ thuộc ổ đĩa ánh xạ cục bộ).
   - **Chủ động nhắc việc & gửi tin nhắn:** Tự động gửi tin nhắn riêng cho từng cán bộ hoặc vào Nhóm Zalo cơ quan khi đến hạn báo cáo, lịch họp hoặc đôn đốc nhiệm vụ.

---

## 📂 SƠ ĐỒ CẤU TRÚC THƯ MỤC HỆ THỐNG

```text
e:\Viet Design\Chuyên viên ảo\
│
├── 📜 AGENTS.md                             # QUY TẮC VẬN HÀNH MẶC ĐỊNH (auto-load khi mở workspace)
├── 📖 SETUP.md                              # HƯỚNG DẪN CÀI ĐẶT & TRIỂN KHAI TRÊN MÁY TÍNH MỚI
├── 📋 CHECKLIST_TIEN_DO.md                  # BẢNG TIẾN ĐỘ THỰC HIỆN TOÀN HỆ THỐNG
├── 📌 KE_HOACH_SO_NHIEM_VU_VA_HEN_GIO.md    # KẾ HOẠCH SỔ NHIỆM VỤ, TIÊU CHÍ & BỘ HẸN GIỜ TỰ ĐỘNG
│
├── 🔌 .agents/                              # HỆ THỐNG SKILLS ANTIGRAVITY (auto-discovery)
│   └── skills/
│       ├── quy-chuan-nen-tang/SKILL.md      # Quy chuẩn nền tảng thể thức văn bản Đảng toàn diện
│       ├── bao-cao/SKILL.md                 # Kỹ năng soạn Báo cáo của cấp uỷ (-BC/ĐU)
│       ├── to-trinh/SKILL.md                # Kỹ năng soạn Tờ trình xin chủ trương & trình duyệt (-TTr)
│       ├── ke-hoach/SKILL.md                # Kỹ năng soạn Kế hoạch cấp uỷ (-KH/ĐU) theo nguyên tắc "5 Rõ"
│       ├── nghi-quyet/SKILL.md              # Kỹ năng soạn Nghị quyết (-NQ/ĐU) (tuyệt đối không chia Điều)
│       ├── quyet-dinh/SKILL.md              # Kỹ năng soạn Quyết định (-QĐ/ĐU) (bắt buộc chia Điều)
│       ├── chi-thi/SKILL.md                 # Kỹ năng soạn Chỉ thị (-CT/ĐU) & Chương trình hành động (-CTr)
│       ├── thong-bao/SKILL.md               # Kỹ năng soạn Thông báo Kết luận họp BTV & Thường trực (-TB/ĐU)
│       ├── ket-luan/SKILL.md                # Kỹ năng soạn Kết luận Hội nghị Ban Chấp hành (-KL/ĐU)
│       ├── cong-van/SKILL.md                # Kỹ năng soạn Công văn giao việc/chỉ đạo & Lấy ý kiến BTV (-CV/ĐU)
│       ├── tham-muu-chuyen-doi-so/SKILL.md  # Kỹ năng Tham mưu Chuyển đổi số, Đề án 06, Ban Chỉ đạo 57
│       └── tham-dinh-van-ban/SKILL.md       # Kỹ năng Thẩm định văn bản & Đối soát tiếp thu
│
├── ⚙️ server/                                # MÁY CHỦ BACKEND & BỘ ĐIỀU PHỐI THÔNG MINH
│   ├── app.py                               # FastAPI application & Web server
│   ├── chat_engine.py                       # Bộ điều phối hội thoại & xử lý nghiệp vụ trung tâm
│   ├── ai_connector.py                      # Kết nối DeepSeek API chuyên sâu, tự động sửa JSON
│   ├── config.py                            # Quản lý biến môi trường (.env)
│   ├── prompts/
│   │   ├── chat_mode.py                     # Prompt chế độ trò chuyện & dữ liệu thường trực
│   │   └── intent_router.py                 # Bộ phân loại câu lệnh & phân luồng nghiệp vụ
│   ├── services/
│   │   ├── knowledge_loader.py              # BỘ NẠP TRI THỨC & KỸ NĂNG CHỌN LỌC (Selective Context Injection)
│   │   ├── gdrive_service.py                # Dịch vụ upload Google Drive đám mây (Cloud Network Upload)
│   │   └── zalo_api.py                      # Zalo Bot API wrapper (gửi tin, làm sạch URL, tải tệp)
│   ├── routers/
│   │   └── zalo_webhook.py                  # Endpoint tiếp nhận sự kiện Zalo Webhook / Background Tasks
│   ├── workflows/                           # 4 Luồng tham mưu cốt lõi (WF1, WF2, WF3, WF4)
│   └── static/                              # Giao diện Web (HTML5, CSS3, JS giao diện Đảng)
│
├── ⚙️ scripts/                              # BỘ CÔNG CỤ TỰ ĐỘNG HÓA VĂN THƯ & RUNNER
│   ├── run_zalo_bot.py                      # Runner Zalo Bot cơ chế Long Polling (chạy độc lập localhost)
│   ├── gdrive_appscript_setup.js            # Mã Google Apps Script Web App triển khai tải tệp lên Drive
│   ├── export_docx.py                       # Engine sinh tệp Word (.docx) chuẩn hóa tự động HD 05
│   └── doc_reader.py                        # Trích xuất và đọc văn bản Office (.docx, .doc, .pdf)
│
├── 📥 van_ban_den/                          # KHO TIẾP NHẬN TÀI LIỆU ĐẦU VÀO
│   └── 2026/                                # Văn bản chỉ đạo cấp trên (Tỉnh uỷ, Trung ương) theo năm
│
├── 📤 van_ban_du_thao/                      # KHO LƯU TRỮ VĂN BẢN SOẠN THẢO ĐẦU RA
│   └── 2026/                                # Quản lý theo năm công tác và theo từng thể loại
│
└── 📚 references/                           # TÀI LIỆU TRA CỨU & QUY PHẠM ĐỊA PHƯƠNG
    ├── tong_quan_xa_cong_hai.md             # Tri thức, mục tiêu Đại hội Đảng bộ xã lần I, 08 thôn
    └── Cam_nang_Nghiep_vu_Tham_muu_Cap_uy.md # Cẩm nang tra cứu thẩm quyền, SLA, phân vai 5 cơ quan
```

---

## 🧠 BỘ NẠP TRI THỨC CHỌN LỌC (SELECTIVE KNOWLEDGE INJECTION)

Để AI nắm bắt sâu sắc tình hình xã Công Hải mà không làm phình to chi phí token:
- **Cơ chế 3 lớp (3 Decision Layers):**
  1. *Lớp Phân loại Ý định (Intent Router):* Phân tích câu lệnh của cán bộ để xác định đúng thể loại văn bản cần xử lý (`CV`, `KH`, `BC`, `TB`, `KL`, `QD`, `NQ`, `TTr`, `CT`).
  2. *Lớp Quy chuẩn Nền tảng Bắt buộc (Core Rules):* Tự động nạp: mô hình 02 cấp (không còn cấp huyện), 08 thôn, lãnh đạo thường trực, thể thức HD 05, chính tả khối Đảng (`oà`, `uỷ`, `uý`, ngày `dd/mm/yyyy`).
  3. *Lớp Kỹ năng Chuyên sâu:* Chỉ nạp đúng nội dung tệp `SKILL.md` của thể loại đó (chỉ tiêu tăng trưởng 11-12%, ngân sách 12%, không còn hộ nghèo đến 2030, NTM nâng cao, hồ Sông Trâu 800ha...).
- **Hiệu quả:** Mỗi yêu cầu chỉ tiêu thụ **3.600 – 3.900 tokens** (tiết kiệm 93% chi phí so với nạp toàn bộ 55.000 tokens), phản hồi trong 3 – 5 giây.

---

## ☁️ CƠ CHẾ GOOGLE DRIVE ĐÁM MÂY (CLOUD UPLOAD)

Hệ thống tải tệp trực tuyến qua Internet, **hoàn toàn không dùng ổ đĩa ánh xạ cục bộ (`G:\`)**:
1. **Google Apps Script Web App:** Sử dụng mã [scripts/gdrive_appscript_setup.js](file:///e:/Viet%20Design/Chuy%C3%AAn%20vi%C3%AAn%20%E1%BA%A3o/scripts/gdrive_appscript_setup.js) triển khai trên tài khoản của Cán bộ (chỉ cấp quyền 1 lần duy nhất).
2. **Quyền riêng tư & Tiện ích:** Các cán bộ khác trong cơ quan chỉ cần nhận link tải qua Zalo là xem và tải được văn bản ngay lập tức, không cần cấp quyền thêm.
3. **Chống lỗi định dạng link:** Tự động mã hoá ký tự gạch dưới (`%5F`) trong liên kết Google Drive để tránh bị bộ đọc Markdown của Zalo biến thành chữ in nghiêng gây lỗi 404.

---

## 🎯 CÁC NGUYÊN TẮC NGHIỆP VỤ BẮT BUỘC TUÂN THỦ

1. **Mô hình Chính quyền 2 cấp địa phương (Tỉnh $\Rightarrow$ Xã):**
   * Vận hành từ ngày **01/7/2025**, hoàn toàn không còn cấp huyện.
   * Cấp trên trực tiếp của xã là **Tỉnh uỷ Khánh Hoà** và **UBND tỉnh Khánh Hoà**.
   * Khi phát hiện còn sót cấp huyện trong dự thảo, chỉ ghi ngắn gọn: *"không còn cấp huyện nữa"*.
2. **Quy chuẩn Thể thức Hướng dẫn số 05-HD/VPTW:**
   * Căn lề: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm (Khổ A4).
   * Spacing & Giãn dòng: Before 6pt, After 6pt, Line spacing cố định Exactly 18pt, Font Times New Roman 14.
   * Thụt đầu dòng: Mọi đoạn văn, mục lớn, tiểu mục, gạch đầu dòng (-) hoặc cộng (+) đều thụt đúng 1cm (10mm).
   * Đường kẻ dưới tiêu ngữ ĐCSVN: Dài 192pt, độ dày 3/4pt (0.75pt).
   * Ô chữ ký: Dòng 1 thẩm quyền in hoa đậm (`T/M BAN THƯỜNG VỤ`); Dòng 2 chức vụ in hoa đứng thường (`BÍ THƯ`, `PHÓ BÍ THƯ`); Tên người ký cách chức danh 5 dòng 14pt, in thường đậm.
3. **Cơ chế An toàn Human-in-the-Loop:**
   * Tuyệt đối không lưu, không hỏi mật khẩu.
   * Mọi văn bản AI tạo ra là **Dự thảo Tham mưu**. Thao tác ký số, ban hành do Cán bộ tự tay thực hiện.
4. **Quy tắc Tiết kiệm Token:**
   * Tuyệt đối không in lại toàn văn văn bản vào chat khi đã xuất tệp Word (.docx). Chỉ tóm tắt Bảng phân công/đối soát, Lưu ý nghiệp vụ và Link tải tệp.

---

## 🛠️ HƯỚNG DẪN VẬN HÀNH NHANH

### 1. Khởi động Web Server (Giao diện cán bộ):
```powershell
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload
```
Truy cập: `http://localhost:8000`

### 2. Khởi động Bot Zalo (Long Polling di động):
```powershell
python scripts/run_zalo_bot.py
```
Cán bộ mở Zalo, nhắn lệnh chỉ đạo hoặc gửi tệp đính kèm để Bot xử lý và trả về link Google Drive ngay lập tức.
