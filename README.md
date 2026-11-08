# HỆ THỐNG TRỢ LÝ AI THAM MƯU TỔNG HỢP & TỰ ĐỘNG HOÁ CẤP UỶ
## VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI, TỈNH KHÁNH HOÀ
*(Phiên bản 2.2.0 — Chuẩn thể thức Hướng dẫn số 05-HD/VPTW năm 2026 của Văn phòng Trung ương Đảng & Mô hình Chính quyền địa phương 02 cấp)*

---

Hệ thống được phát triển chuyên biệt theo **Mô hình Hạt nhân & Kỹ năng Chuyên sâu Đa tầng (Core & Multi-Tier Advisory Skills)**, kết hợp cùng **Hệ thống Tra cứu Lai Thực chứng (Hybrid RAG: FTS5 BM25 + Vector Embedding)**, **Động cơ Kép Thông minh (Dual-Engine AI: Google Gemini Flash & DeepSeek Cloud)** và **Bộ Lập Lịch Hành Chính Chủ Động (Autonomous Administrative Scheduler)**.

Hệ thống đóng vai trò là **Chuyên viên Ảo Tham mưu Tổng hợp Toàn năng** phục vụ Thường trực Đảng uỷ, Ban Thường vụ Đảng uỷ và Ban Chấp hành Đảng bộ xã Công Hải, tỉnh Khánh Hoà (trực thuộc trực tiếp Tỉnh uỷ Khánh Hoà theo mô hình chính quyền địa phương 02 cấp từ ngày 01/7/2025).

> 🧭 **Dành cho Kỹ sư & Mọi AI Agent:** Tham khảo ngay [CODEBASE_MAP.md](CODEBASE_MAP.md) để xem toàn bộ kiến trúc phân tầng, các sơ đồ luồng thực thi (Mermaid), thiết kế CSDL SQLite WAL và danh mục API Endpoints của hệ thống.

---

## 🏛️ ĐẶC ĐIỂM BỘ MÁY & MÔ HÌNH QUẢN LÝ (TỪ 01/7/2025)

* **Mô hình chính quyền địa phương 02 cấp:** Cấp tỉnh (tỉnh Khánh Hoà) và Cấp xã (xã Công Hải) — **hoàn toàn không còn cấp huyện**. Cấp trên trực tiếp của Đảng uỷ xã là **Tỉnh uỷ Khánh Hoà** và **UBND tỉnh Khánh Hoà**.
* **Đơn vị hành chính:** Toàn xã có diện tích 124,19 km², gồm **08 thôn chính thức**: Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng.
* **Tổ chức Đảng bộ cơ sở:** Gồm **21 chi bộ trực thuộc** (08 chi bộ thôn, 03 chi bộ trường học và các chi bộ cơ quan, lực lượng vũ trang) với **382 đảng viên**.
* **5 Cơ quan chuyên môn phối hợp cấp xã:**
  1. Uỷ ban nhân dân xã Công Hải
  2. Ban Xây dựng Đảng Đảng uỷ xã
  3. Cơ quan Uỷ ban Kiểm tra Đảng uỷ xã
  4. Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã
  5. Văn phòng Đảng uỷ xã (Cơ quan tham mưu tổng hợp hạt nhân)

---

## 🚀 3 KÊNH TƯƠNG TÁC ĐỒNG BỘ CỦA HỆ THỐNG

```text
                  ┌────────────────────────────────────────────────────────┐
                  │          CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ              │
                  │   (Hạt nhân điều phối, Hybrid RAG & HD 05-HD/VPTW)     │
                  └───────────┬────────────────┬────────────────┬──────────┘
                              │                │                │
            ┌─────────────────┴─┐    ┌─────────┴────────┐    ┌──┴───────────────┐
            │ 1. Antigravity IDE │    │ 2. Web Công Hải Số│    │ 3. Zalo Bot Di Động│
            │    (Quản trị mã &  │    │   (ChatCHS - VPS │    │    (Long Polling  │
            │     15 Đảng Skills)│    │    45.119.82.227)│    │     Drive & Nhắc) │
            └───────────────────┘    └──────────────────┘    └──────────────────┘
```

1. **Google Antigravity IDE (Workspace Kỹ thuật):** Môi trường phát triển, kiểm thử mã nguồn, đối soát dữ liệu và mở rộng kho 15 kỹ năng tham mưu cấp uỷ chuyên sâu.
2. **Giao diện Web Công Hải Số (ChatCHS — `http://45.119.82.227` hoặc `http://localhost:8000`):**
   * **Nhận diện thương hiệu Đảng bộ:** Tích hợp logo chính thức Công Hải Số, nền chìm hoa văn Trống đồng Đông Sơn tinh tế, tông màu Đỏ Đảng chủ đạo (`#C00000`).
   * **Kiến trúc 1 trang duy nhất (Single-Page View):** Cán bộ thông thường và khách chỉ thấy duy nhất giao diện Chat tinh gọn, sang trọng. Toàn bộ các bảng biểu và phân hệ quản trị được chuyển vào **Bảng Điều Hành Admin** dành riêng cho Quản trị viên (`0327777707`).
   * **Xác thực Cán bộ Hai lớp (Zalo 2FA OTP):** Đăng nhập an toàn bằng số điện thoại trong danh bạ, mã OTP 6 số bảo mật được gửi trực tiếp về Zalo cá nhân của cán bộ (tuyệt đối không hiển thị mã trên trình duyệt để bảo vệ an toàn thông tin nội bộ).
   * **Bảng điều hành Admin 7 phân hệ hoàn chỉnh:** Quản lý danh bạ cán bộ (CRUD), Đổi động cơ AI 1 chạm, Giám sát hội thoại hệ thống, Sổ nhiệm vụ, Kho RAG, Chỉ tiêu KPI và Xem log máy chủ VPS trực tiếp.
3. **Zalo Bot Di Động 24/7 (`scripts/run_zalo_bot.py`):**
   * Hoạt động theo cơ chế **Long Polling (`getUpdates`)**, độc lập hoàn toàn, không phụ thuộc vào proxy hay tên miền ngoài.
   * Tiếp nhận văn bản, xử lý lệnh chỉ đạo từ xa qua điện thoại thông minh của Thường trực Đảng uỷ.
   * Tự động đẩy tệp Word (.docx) chuẩn thể thức lên Google Drive và gửi liên kết tải trực tiếp qua tin nhắn.
   * **Chủ động nhắc việc:** Đôn đốc nhiệm vụ sáng (07h30), cảnh báo quá hạn chiều (16h30) và nhắc nộp báo cáo tuần sáng thứ Sáu.

---

## 🏛️ 4 TRỤ CỘT NĂNG LỰC TOÀN NĂNG (CORE PILLARS)

### 1. Thể thức Văn bản Đảng Chuẩn Tuyệt đối (HD 05-HD/VPTW)
* **Căn lề trang:** Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm (Khổ chuẩn A4).
* **Spacing & Giãn dòng:** Toàn bộ phần thân văn bản canh `Before: 6pt`, `After: 6pt`, `Line spacing: Exactly 18pt`, font Times New Roman cỡ 14.
* **Thụt đầu dòng:** Tất cả các đoạn văn, đề mục lớn (I, II), tiểu mục (1, 2), điểm (a, b), dấu gạch (-) hoặc cộng (+) đều thụt đầu dòng đúng **1cm (10mm)** như nhau.
* **Đường kẻ tiêu ngữ Đảng:** Độ dài đúng **192pt**, độ dày **3/4pt (0.75pt)**, nét liền màu đen.
* **Ô chữ ký chuẩn:**
  * Dòng 1 (Thẩm quyền/Ký thay): `T/M BAN THƯỜNG VỤ`, `T/M ĐẢNG UỶ`, `K/T CHÁNH VĂN PHÒNG`... in hoa, **IN ĐẬM**.
  * Dòng 2 (Chức vụ): `BÍ THƯ`, `PHÓ BÍ THƯ`, `PHÓ CHÁNH VĂN PHÒNG`... viết hoa, **in thường (không đậm)**.
  * Khoảng cách ký tên: Cách đúng **5 dòng 14pt**.
  * Dòng cuối (Họ tên): Chữ in thường, đứng, **IN ĐẬM**.
* **Quy chuẩn khối Kính gửi:** Bảng 1 hàng 2 cột ẩn viền (Cột 1 chữ "*Kính gửi:*" nghiêng canh phải; Cột 2 danh sách cơ quan canh trái). Chỉ áp dụng cho Tờ trình (-TTr) và Công văn (-CV); **tuyệt đối không đưa vào Báo cáo (-BC)**.
* **Chính tả Khối Đảng:** Đặt dấu chuẩn `oà`, `uỷ`, `uý` (Đảng uỷ, Khánh Hoà, Uỷ ban). Ngày tháng trong nội dung dạng `dd/mm/yyyy`.

### 2. Động cơ Kép Thông minh (Dual-Engine AI Failover)
* **Động cơ chính (Google Gemini 3.5 Flash Lite):** Cửa sổ ngữ cảnh 1 triệu tokens, tốc độ siêu tốc, miễn phí quota hàng ngày, phân tích sâu và soạn thảo văn bản Đảng cực nhanh.
* **Động cơ dự phòng (DeepSeek Cloud 671B):** Mô hình suy luận lớn 671 tỷ tham số. Hệ thống tự động chuyển hướng sang DeepSeek khi Gemini đạt giới hạn hoặc mất kết nối.
* **Mô hình Offline nội bộ (Ollama Local):** Hỗ trợ `Qwen 2.5` và `DeepSeek-R1` chạy trực tiếp trên GPU/CPU máy chủ khi mất Internet, đảm bảo 100% tính bảo mật cho tài liệu nội bộ.
* **Cơ chế Tự chuyển hướng Thông minh:** Nếu người dùng chọn DeepSeek nhưng chưa cấu hình khoá trong `.env`, hệ thống tự động hoán đổi sang Gemini Flash để duy trì hội thoại thông suốt, không báo lỗi gián đoạn.

### 3. Hệ thống Tra cứu Lai Thực chứng (Hybrid RAG Engine)
* **Sliding Window Chunking:** Cắt đoạn 400 từ với **80 từ gối đầu (Overlap)**, chống đứt gãy ngữ cảnh điều khoản và bảo toàn cấu trúc bảng biểu.
* **Vector Embedding & FTS5 BM25:** Tích hợp mô hình vector `nomic-embed-text` lưu dưới dạng BLOB trong SQLite kết hợp chỉ mục văn bản toàn văn SQLite FTS5.
* **Thuật toán Dung hợp Điểm RRF (Reciprocal Rank Fusion):**
  $$RRF\_Score = \frac{1}{60 + Rank_{BM25}} + \frac{1}{60 + Rank_{Vector}}$$
* **Chiến lược "Giỏ Ngữ Cảnh 2 - 4 - 2":** Tự động phân bổ tối đa 8 đoạn trích tinh hoa:
  * *Slot 1–2 (Nền tảng):* Nghị quyết Đại hội Đảng bộ xã lần I, Quy chế làm việc.
  * *Slot 3–6 (Chuyên đề):* Báo cáo, Kế hoạch mới nhất của Tỉnh uỷ và Đảng uỷ xã.
  * *Slot 7–8 (Đồ thị Căn cứ):* 1-Hop Citation lần theo các văn bản gốc năm trước.

### 4. Quản trị Sổ Nhiệm Vụ & Giám Sát Chỉ Tiêu (KPI Monitor)
* **Khử trùng lặp Nhiệm vụ (Task Deduplication):** Sử dụng mã băm `task_fingerprint = md5(co_quan + noi_dung)`. Khi công việc chuyển tiếp từ tháng này sang tháng sau (như trong Chương trình 42, 48, 55-CTr/ĐU), hệ thống tự động cập nhật hạn mới và chuyển trạng thái `"Chuyển tiếp tháng sau"`.
* **Giám sát 20 Chỉ tiêu Đại hội Đảng bộ xã khoá I & 19 Chỉ tiêu NQ57 CĐS:** Theo dõi theo cơ chế đèn giao thông (Xanh - Vàng - Đỏ), đối soát số liệu thực tế với mục tiêu 2026 và 2030.

---

## 📂 SƠ ĐỒ CẤU TRÚC HỆ THỐNG MÃ NGUỒN

```text
e:\Viet Design\Chuyên viên ảo\
│
├── 📜 AGENTS.md                             # QUY TẮC VẬN HÀNH MẶC ĐỊNH (auto-load)
├── 🗺️ CODEBASE_MAP.md                       # BẢN ĐỒ KIẾN TRÚC MÃ NGUỒN & AI ONBOARDING
├── 📖 README.md                             # TÀI LIỆU TỔNG QUAN DỰ ÁN (File này)
├── 📖 SETUP.md                              # HƯỚNG DẪN CÀI ĐẶT MÁY CHỦ TỪ ĐẦU
├── 📋 requirements.txt                      # DANH MỤC THƯ VIỆN PYTHON ĐẦY ĐỦ
├── 🔑 .env.example                          # MẪU BIẾN MÔI TRƯỜNG CẤU HÌNH
├── 🚀 run.py                                # Script khởi động nhanh toàn hệ thống
│
├── 🔌 .agents/skills/                       # HỆ THỐNG 15 SKILLS THAM MƯU CẤP UỶ
│   ├── quy-chuan-nen-tang/SKILL.md          # Thể thức văn bản Đảng & quy chuẩn chung
│   ├── bao-cao/SKILL.md                     # Báo cáo công tác định kỳ & chuyên đề (-BC/ĐU)
│   ├── bao-cao-thang/SKILL.md               # Báo cáo tháng chuyên sâu gửi Tỉnh uỷ
│   ├── ke-hoach/SKILL.md                    # Kế hoạch công tác theo nguyên tắc "5 Rõ" (-KH/ĐU)
│   ├── cong-van/SKILL.md                    # Công văn chỉ đạo & lấy ý kiến BTV (-CV/ĐU)
│   ├── thong-bao/SKILL.md                   # Thông báo Kết luận họp Thường trực/BTV (-TB/ĐU)
│   ├── ket-luan/SKILL.md                    # Kết luận Hội nghị Ban Chấp hành (-KL/ĐU)
│   ├── nghi-quyet/SKILL.md                  # Nghị quyết chuyên đề & nhiệm vụ năm (-NQ/ĐU)
│   ├── quyet-dinh/SKILL.md                  # Quyết định cấp uỷ chia Điều (-QĐ/ĐU)
│   ├── to-trinh/SKILL.md                    # Tờ trình xin chủ trương & trình duyệt (-TTr/ĐU)
│   ├── chi-thi/SKILL.md                     # Chỉ thị & Chương trình hành động (-CT/ĐU, -CTr)
│   ├── tham-dinh-van-ban/SKILL.md           # Thẩm định dự thảo 2 tầng & đối soát tiếp thu
│   └── tham-muu-chuyen-doi-so/SKILL.md      # Tham mưu CĐS, Đề án 06 và Ban Chỉ đạo 57
│
├── ⚙️ server/                                # MÁY CHỦ BACKEND FASTAPI MODULAR
│   ├── app.py                               # Ứng dụng hạt nhân FastAPI tích hợp Zalo Polling
│   ├── chat_engine.py                       # Điều phối hội thoại, phân luồng nghiệp vụ & lưu log
│   ├── ai_connector.py                      # Động cơ kép Failover (Gemini, DeepSeek, Ollama)
│   ├── config.py                            # Quản lý cấu hình biến môi trường
│   ├── logger.py                            # Hệ thống ghi nhật ký xoay vòng UTF-8
│   ├── plan_registry.py                     # Sổ kế hoạch và định danh pháp quy cấp uỷ
│   │
│   ├── routers/                             # CÁC ROUTER CHUYÊN TRÁCH
│   │   ├── auth.py                          # Xác thực cán bộ, Zalo OTP bảo mật 2FA, phiên làm việc
│   │   ├── chat.py                          # Endpoint chat, tải file đính kèm, xuất Word
│   │   ├── knowledge.py                     # Quản trị kho tri thức RAG, preview, commit
│   │   ├── admin.py                         # Quản lý AI Model, CRUD cán bộ, Tasks, KPIs, Logs, Webhook
│   │   └── zalo_webhook.py                  # Tiếp nhận sự kiện Webhook Zalo
│   │
│   ├── services/                            # CÁC DỊCH VỤ HỆ THỐNG
│   │   ├── db_service.py                    # CSDL SQLite WAL: Cán bộ, Nhiệm vụ, KPIs, Chat Logs
│   │   ├── rag_service.py                   # Lõi Hybrid RAG: Cửa sổ trượt, RRF, Giỏ 2-4-2
│   │   ├── embedding_service.py             # Sinh Vector nomic-embed-text, Cosine trên RAM
│   │   ├── scheduler_service.py             # Bộ lập lịch hẹn giờ, khởi động bù & Digest reminder
│   │   ├── knowledge_loader.py              # Bộ nạp tri thức chọn lọc 3 lớp (Selective Injection)
│   │   ├── zalo_bot_service.py              # Động cơ Zalo Bot Long Polling độc lập
│   │   ├── zalo_api.py                      # Wrapper gửi tin Zalo, clean Markdown & split msg
│   │   └── gdrive_service.py                # Upload Google Drive đám mây qua Apps Script
│   │
│   ├── utils/                               # TIỆN ÍCH DÙNG CHUNG
│   │   └── text_processing.py               # Chuẩn hoá chính tả Khối Đảng (oà, uỷ, uý), ngày tháng
│   │
│   ├── workflows/                           # 4 QUY TRÌNH THAM MƯU TỰ ĐỘNG
│   │   ├── wf1_synthesizer.py               # WF1: Tổng hợp Báo cáo tuần (-BC/VPĐU)
│   │   ├── wf2_conclusions.py               # WF2: Thông báo Kết luận họp Thường trực (-TB/ĐU)
│   │   ├── wf3_dispatch.py                  # WF3: Công văn Giao việc từ VB Tỉnh (-CV/ĐU)
│   │   └── wf4_appraisal.py                 # WF4: Thẩm định 2 Tầng & Xuất hồ sơ BTV
│   │
│   └── static/                              # GIAO DIỆN WEB CÔNG HẢI SỐ (ChatCHS)
│       ├── index.html                       # Giao diện đơn trang + Modal Quản trị Admin
│       ├── style.css                        # CSS Thương hiệu Đỏ Đảng (#C00000) & Trống đồng
│       ├── app.js                           # JavaScript tương tác, OTP, Chat, Admin Subtabs
│       └── assets/                          # Logo Công Hải Số, Icon, Trống đồng Đông Sơn
│
├── ⚙️ scripts/                              # CÔNG CỤ TỰ ĐỘNG HOÁ & RUNNER
│   ├── generate_code_map.py                 # Bộ phân tích AST & tự động đồng bộ CODEBASE_MAP
│   ├── pull_db_from_vps.py                  # Đồng bộ an toàn CSDL thực tế từ VPS về máy cục bộ
│   ├── export_docx.py                       # Engine cốt lõi sinh file Word (.docx) chuẩn HD 05
│   ├── doc_reader.py                        # Trích xuất văn bản (.docx, .doc, .pdf)
│   ├── deploy_remote.py                     # Tool điều phối triển khai và cập nhật VPS từ xa
│   ├── deploy_vps.sh                        # Kịch bản cài đặt sạch toàn diện máy chủ VPS
│   ├── update_vps.sh                        # Kịch bản cập nhật siêu tốc CI/CD (3 - 5 giây)
│   ├── run_zalo_bot.py                      # Runner chạy Zalo Bot độc lập
│   ├── seed_database.py                     # Khởi tạo CSDL SQLite WAL ban đầu
│   ├── build_plan_registry.py               # Biên soạn Sổ Kế hoạch nghiệp vụ
│   ├── build_indicator_registry.py          # Biên soạn Sổ Chỉ tiêu Đại hội
│   └── gdrive_appscript_setup.js            # Mã Google Apps Script triển khai Web App Drive
│
├── 📥 van_ban_den/                          # KHO TIẾP NHẬN TÀI LIỆU ĐẦU VÀO
│   └── 2026/                                # Phân mục theo năm tiếp nhận
│
├── 📤 van_ban_du_thao/                      # KHO LƯU TRỮ DỰ THẢO ĐẦU RA (.DOCX)
│   └── 2026/                                # Phân mục theo thể loại (Cong_van, Bao_cao...)
│
└── 📚 references/                           # TRI THỨC ĐỊA PHƯƠNG & QUY PHẠM
    ├── tong_quan_xa_cong_hai.md             # Tri thức xã Công Hải, 08 thôn, 21 chi bộ
    ├── chi_tieu_nhiem_ky.json               # 20 chỉ tiêu Đại hội Đảng bộ xã khoá I
    ├── so_ke_hoach_chi_dao.json             # Sổ Kế hoạch và chỉ đạo cấp Tỉnh - Xã
    ├── kien_truc_rag_lai.md                 # Đặc tả kiến trúc Hybrid RAG hành chính Đảng
    └── Cam_nang_Nghiep_vu_Tham_muu_Cap_uy.md # Thẩm quyền, SLA, chức năng 5 cơ quan
```

---

## 🔒 NGUYÊN TẮC AN TOÀN & BẢO MẬT (SECURITY FIRST)

1. **Tuyệt đối KHÔNG đụng đến Mật khẩu:** Không yêu cầu, không đọc, không lưu, không tiết lộ mật khẩu dưới bất kỳ hình thức nào.
2. **Tuyệt đối KHÔNG tự ý Ban hành, Gửi đi, Ký số:** Mọi quyết định phát hành văn bản phải do cán bộ tự tay bấm nút (Human-in-the-Loop). Văn bản do AI tạo ra chỉ là bản dự thảo tham mưu.
3. **Chốt chặn Độ mật (Secret Document Gatekeeper):** Quét từ khóa đóng dấu độ mật (`MẬT`, `TỐI MẬT`, `TUYỆT MẬT`). Nếu phát hiện, hệ thống **từ chối xử lý và không đẩy lên AI**, tuân thủ nghiêm ngặt Quyết định 37-QĐ/ĐU và Nghị định 63/2026/NĐ-CP.
4. **Chống Path Traversal tại `/api/download`:** Chỉ cho phép tải file an toàn từ thư mục được phân quyền, ngăn chặn triệt để nguy cơ lộ file cấu hình `.env` hoặc CSDL SQLite.

---

## 🛠️ HƯỚNG DẪN VẬN HÀNH & TRIỂN KHAI

### 1. Khởi chạy Cục bộ (Local Development)
```powershell
# 1. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 2. Khởi tạo cơ sở dữ liệu SQLite ban đầu
python scripts/seed_database.py

# 3. Khởi động hệ thống
python run.py
```
* Mở trình duyệt: `http://localhost:8000`

### 2. Triển khai & Cập nhật Máy chủ VPS Ubuntu (45.119.82.227)

#### ⚡ Cập nhật siêu tốc mã nguồn (CI/CD Webhook — Khuyên dùng):
Mỗi khi đồng chí thực hiện lệnh đẩy mã nguồn lên GitHub:
```powershell
git push origin main
```
Sau đó kích hoạt kịch bản CI/CD trên VPS bằng một lệnh gọi Webhook:
```powershell
curl.exe -X POST http://45.119.82.227/api/admin/system/deploy-webhook
```
* **Thời gian hoàn tất:** Chỉ từ **3 đến 5 giây**.
* **Đảm bảo an toàn:** Không cần nhập mật khẩu SSH, không ghi đè tệp cấu hình `.env`, bảo toàn nguyên vẹn 100% CSDL SQLite WAL (danh bạ, sổ nhiệm vụ, nhật ký chat).

#### 🛡️ Cơ chế Bảo vệ CSDL Sản xuất (Production Database Shield):
* **Máy chủ VPS là nguồn dữ liệu duy nhất (Single Source of Truth):** Toàn bộ tệp CSDL SQLite `chuyen_vien_ao.db` trên VPS được bảo vệ độc lập, không bị theo dõi bởi Git (đã loại trừ trong `.gitignore`). Khi đồng chí đẩy code từ máy tính cá nhân lên GitHub, dữ liệu trên VPS **tuyệt đối không bao giờ bị ghi đè hoặc reset**.
* **Tự động sao lưu dự phòng khi cập nhật:** Mỗi lần chạy lệnh cập nhật, script `update_vps.sh` sẽ tự động tạo bản sao lưu tại `/opt/chuyenvienao/backups/chuyen_vien_ao_[timestamp].db` trước khi áp dụng code mới (lưu trữ tối đa 15 bản sao lưu gần nhất).
* **Đồng bộ CSDL thực tế từ VPS về máy tính cá nhân:** Khi đồng chí cần lấy dữ liệu thực tế mới nhất từ VPS về máy tính cá nhân để xem xét hoặc sao lưu:
```powershell
python scripts/pull_db_from_vps.py
```

#### 🛠️ Triển khai mới toàn diện (Reset / Cài đặt sạch môi trường VPS):
Dùng khi máy chủ VPS mới tinh hoặc cần cài đặt lại từ đầu:
```powershell
python scripts/deploy_remote.py
```
* Tự động cấu hình môi trường Python `.venv`, cài đặt Nginx Reverse Proxy (cổng 80) và thiết lập dịch vụ chạy nền Systemd `chuyenvienao.service` tự khởi động cùng máy chủ.

---

*Hệ thống được thiết kế và vận hành chuyên biệt phục vụ công tác tham mưu cấp uỷ tại Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà.*
