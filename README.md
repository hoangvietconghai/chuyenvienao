# HỆ THỐNG TRỢ LÝ AI THAM MƯU TỔNG HỢP & TỰ ĐỘNG HOÁ CẤP UỶ
## VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI, TỈNH KHÁNH HOÀ
*(Phiên bản 2.1.0 — Chuẩn thể thức Hướng dẫn số 05-HD/VPTW năm 2026 của Văn phòng Trung ương Đảng & Mô hình Chính quyền địa phương 02 cấp)*

---

Hệ thống được thiết kế theo **Mô hình Hạt nhân & Kỹ năng Chuyên sâu Đa tầng (Core & Multi-Tier Advisory Skills)**, kết hợp cùng **Hệ thống Tìm kiếm Lai Thực thụ (Hybrid RAG: FTS5 BM25 + Vector Embedding)** và **Bộ Hẹn Giờ Tự Động Chủ Động (Autonomous Administrative Scheduler)**. 

Hệ thống đóng vai trò là **Chuyên viên Ảo Tham mưu Tổng hợp Toàn năng** cho Thường trực Đảng uỷ, Ban Thường vụ Đảng uỷ và Ban Chấp hành Đảng bộ xã Công Hải, tỉnh Khánh Hoà (trực thuộc trực tiếp Tỉnh uỷ Khánh Hoà từ ngày 01/7/2025).

---

## 🚀 3 KÊNH TƯƠNG TÁC ĐỒNG BỘ CỦA HỆ THỐNG

```text
                  ┌────────────────────────────────────────────────────────┐
                  │          CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ              │
                  │   (Hạt nhân điều phối, Hybrid RAG & HD 05-HD/VPTW)     │
                  └───────────┬────────────────┬────────────────┬──────────┘
                              │                │                │
            ┌─────────────────┴─┐    ┌─────────┴────────┐    ┌──┴───────────────┐
            │ 1. Antigravity IDE │    │  2. Giao diện Web │    │ 3. Zalo Bot Di Động│
            │    (Cán bộ kỹ thuật│    │   (localhost:8000│    │    (Nhắc việc 24/7│
            │     & Lập trình)   │    │    Văn phòng làm)│    │     & Cloud Drive)│
            └───────────────────┘    └──────────────────┘    └──────────────────┘
```

1. **Google Antigravity IDE (Workspace chuyên sâu):** Dành cho cán bộ quản trị hệ thống, nghiên cứu, kiểm thử và mở rộng kho 15 Skills kỹ năng tham mưu.
2. **Giao diện Web Chuyên nghiệp (`http://localhost:8000`):** Bàn làm việc đồ hoạ cho Văn phòng Đảng uỷ:
   - Tải tệp drag-and-drop, bóc tách "5 Rõ", đối soát sai lệch số liệu tự động.
   - Quy trình nạp RAG có kiểm duyệt **Human-in-the-Loop** (Xem trước trích yếu, số hiệu, chunks $\rightarrow$ duyệt $\rightarrow$ nạp CSDL).
   - Quản trị Sổ Nhiệm vụ, Giám sát Chỉ tiêu Nghị quyết (Đèn giao thông Xanh - Vàng - Đỏ).
3. **Chatbot Zalo Tự Động 24/7 (`scripts/run_zalo_bot.py`):**
   - Tiếp nhận lệnh chỉ đạo và văn bản đính kèm trực tiếp từ điện thoại cán bộ.
   - **Tự động đẩy tệp lên Google Drive đám mây:** Cung cấp liên kết tải trực tiếp tệp Word (.docx) chuẩn thể thức ngay trong tin nhắn Zalo.
   - **Chủ động nhắc việc (Proactive Reminder):** Gửi tin nhắn đôn đốc buổi sáng (07h30), cảnh báo quá hạn buổi chiều (16h30) và nhắc nộp báo cáo tuần sáng thứ Sáu.

---

## 🏛️ 4 TRỤ CỘT NĂNG LỰC TOÀN NĂNG (CORE PILLARS)

### 1. Thể thức Văn bản Đảng Chuẩn Tuyệt đối (HD 05-HD/VPTW)
- Căn lề chuẩn: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm (Khổ A4).
- Spacing & Giãn dòng: Before 6pt, After 6pt, Line spacing Exactly 18pt, Font Times New Roman 14.
- Thụt đầu dòng: Mọi đoạn văn, mục lớn, tiểu mục, gạch (-) hoặc cộng (+) đều thụt đúng **1cm (10mm)**.
- Đường kẻ tiêu ngữ: Chiều dài 192pt, độ dày 3/4pt (0.75pt).
- Ô chữ ký chuẩn: Thẩm quyền in hoa đậm (`T/M BAN THƯỜNG VỤ`), chức vụ viết hoa không đậm (`BÍ THƯ`), khoảng cách ký 5 dòng 14pt.
- Bắt buộc chính tả Khối Đảng: `oà`, `uỷ`, `uý` (Đảng uỷ, Khánh Hoà, Ban Thường vụ, Uỷ ban). Ngày tháng dạng `dd/mm/yyyy`.

### 2. Hệ thống Tìm kiếm Lai Thực thụ (Hybrid RAG Engine)
- **Vector Embedding Cục bộ:** Tích hợp mô hình `nomic-embed-text` qua Ollama local API, nén vector float32 thành nhị phân (BLOB) lưu trong SQLite.
- **Tính toán Cosine Similarity trên RAM:** Truy vấn vector cực nhanh trong < 2ms bằng NumPy / Python thuần mà không cần cài đặt Vector DB cồng kềnh.
- **Sliding Window Chunking:** Cắt đoạn 400 từ với **80 từ gối đầu (Overlap)**, chống đứt gãy ngữ cảnh điều khoản pháp lý và bảo toàn tiêu đề bảng biểu (Table Row Contextualization).
- **Thuật toán Dung hợp Điểm RRF (Reciprocal Rank Fusion):**
  $$RRF\_Score = \frac{1}{60 + Rank_{BM25}} + \frac{1}{60 + Rank_{Vector}}$$
- **Chiến lược "Giỏ Ngữ Cảnh 2 - 4 - 2":** Tự động phân bổ tối đa 8 đoạn trích tinh hoa:
  - *Slot 1–2 (Nền tảng):* Nghị quyết Đại hội, Quy chế làm việc.
  - *Slot 3–6 (Chuyên đề):* Báo cáo, Kế hoạch mới nhất.
  - *Slot 7–8 (Đồ thị Căn cứ):* 1-Hop Citation lần theo các văn bản gốc năm trước.

### 3. Bộ Lập Lịch & Nhắc Việc Chủ Động (Autonomous Scheduler)
- **Cơ chế Khởi động bù (`catch_up_missed_jobs`):** Nếu máy tính văn phòng tắt qua đêm và bật lên lúc 08h30 sáng, hệ thống tự động kiểm tra CSDL và gửi bù các thông báo nhắc việc bị bỏ lỡ.
- **Ma trận Lịch hẹn hành chính:**
  - *07h30 Hàng ngày:* Quét nhiệm vụ đến hạn hôm nay & ngày mai $\rightarrow$ gửi tin nhắc đôn đốc (Digest gom nhóm theo cơ quan).
  - *16h30 Hàng ngày:* Quét nhiệm vụ quá hạn $\rightarrow$ gửi báo cáo cảnh báo cho Chánh Văn phòng & Thường trực Đảng uỷ.
  - *08h00 Sáng Thứ Sáu:* Đôn đốc UBND xã và 08 Chi bộ thôn nộp Báo cáo tuần trước 11h00.
  - *08h00 Ngày 23 hàng tháng:* Nhắc Bộ phận CĐS cập nhật số liệu `theodoinq.dcs.vn` và `pakn.nq57.vn` trước hạn ngày 25.
- **Chống spam Zalo:** Khoá `acquire_remind_lock` trong SQLite WAL bảo đảm không bao giờ gửi lặp tin nhắn trong cùng 1 ngày.

### 4. Quản lý Nhiệm vụ & Giám sát Chỉ tiêu (KPI Monitor)
- **Khử trùng lặp Nhiệm vụ (Task Deduplication):** Sử dụng mã băm `task_fingerprint = md5(co_quan + noi_dung)`. Khi công việc trượt tiến độ từ tháng này sang tháng sau (như trong Chương trình 42, 48, 55-CTr/ĐU), hệ thống tự động cập nhật hạn mới và chuyển trạng thái `"Chuyển tiếp tháng sau"`, **không tạo bản ghi trùng lặp**.
- **Đối soát Chỉ tiêu Đại hội (Deterministic Verification):** Kiểm tra chặt chẽ 20 chỉ tiêu Đại hội Đảng bộ xã lần I (`01-NQ/ĐH`) và 19 chỉ tiêu NQ57, cảnh báo ngay khi dự thảo viết sai số liệu (như chỉ tiêu mức độ hài lòng `XH_04` là tăng 5%, không phải đạt 100%).

---

## 📂 SƠ ĐỒ CẤU TRÚC HỆ THỐNG MÃ NGUỒN

```text
e:\Viet Design\Chuyên viên ảo\
│
├── 📜 AGENTS.md                             # QUY TẮC VẬN HÀNH MẶC ĐỊNH (auto-load)
├── 📖 README.md                             # TÀI LIỆU TỔNG QUAN HỆ THỐNG (File này)
├── 📖 SETUP.md                              # HƯỚNG DẪN CÀI ĐẶT MÁY CHỦ TỪ ĐẦU
├── 📋 requirements.txt                      # DANH MỤC THƯ VIỆN PYTHON ĐẦY ĐỦ
├── 🔑 .env.example                          # MẪU BIẾN MÔI TRƯỜNG CẤU HÌNH
│
├── 🔌 .agents/skills/                       # HỆ THỐNG 15 SKILLS THAM MƯU CHUYÊN SÂU
│   ├── quy-chuan-nen-tang/SKILL.md          # Thể thức văn bản Đảng & nguyên tắc nền tảng
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
│   ├── app.py                               # Ứng dụng hạt nhân FastAPI (~80 dòng tinh gọn)
│   ├── chat_engine.py                       # Điều phối hội thoại, phiên làm việc (TTL 4h)
│   ├── ai_connector.py                      # Kết nối DeepSeek/Ollama, bộ tự sửa JSON Repair
│   ├── config.py                            # Cấu hình biến môi trường và thư mục
│   ├── logger.py                            # Hệ thống ghi nhật ký xoay vòng UTF-8
│   │
│   ├── routers/                             # CÁC ROUTER CHUYÊN TRÁCH (MODULAR ARCHITECTURE)
│   │   ├── chat.py                          # Endpoint chat, upload file, tải file an toàn
│   │   ├── knowledge.py                     # Quản trị kho RAG, preview, commit, FTS5 search
│   │   ├── admin.py                         # Quản lý AI Model, 4 Workflows, Tasks, KPIs, Danh bạ
│   │   └── zalo_webhook.py                  # Tiếp nhận sự kiện Webhook Zalo
│   │
│   ├── services/                            # CÁC DỊCH VỤ HỆ THỐNG
│   │   ├── db_service.py                    # CSDL SQLite WAL: 7 bảng nghiệp vụ + Indexes
│   │   ├── rag_service.py                   # Lõi Hybrid RAG: Cửa sổ trượt, RRF Fusion, Giỏ 2-4-2
│   │   ├── embedding_service.py             # Sinh Vector nomic-embed-text, Cosine trên RAM
│   │   ├── scheduler_service.py             # Bộ lập lịch hẹn giờ, khởi động bù & Digest reminder
│   │   ├── knowledge_loader.py              # Bộ nạp tri thức chọn lọc 3 lớp (Selective Injection)
│   │   ├── zalo_api.py                      # Wrapper gửi tin Zalo, clean Markdown & split msg
│   │   └── gdrive_service.py                # Upload Google Drive đám mây qua Apps Script
│   │
│   ├── utils/                               # TIỆN ÍCH DÙNG CHUNG (DRY REFACTOR)
│   │   └── text_processing.py               # Chuẩn hoá chính tả Khối Đảng (oà, uỷ, uý), ngày tháng
│   │
│   ├── workflows/                           # 4 QUY TRÌNH THAM MƯU TỰ ĐỘNG
│   │   ├── wf1_synthesizer.py               # WF1: Tổng hợp Báo cáo tuần (-BC/VPĐU)
│   │   ├── wf2_conclusions.py               # WF2: Thông báo Kết luận họp Thường trực (-TB/ĐU)
│   │   ├── wf3_dispatch.py                  # WF3: Công văn Giao việc từ VB Tỉnh (-CV/ĐU)
│   │   └── wf4_appraisal.py                 # WF4: Thẩm định 2 Tầng & Xuất hồ sơ BTV
│   │
│   └── static/                              # Giao diện Web HTML5/CSS3/JS
│
├── ⚙️ scripts/                              # CÔNG CỤ TỰ ĐỘNG HOÁ & RUNNER
│   ├── export_docx.py                       # Engine sinh file Word (.docx) chuẩn HD 05
│   ├── doc_reader.py                        # Trích xuất văn bản (.docx, .doc, .pdf)
│   ├── run_zalo_bot.py                      # Runner Zalo Bot (Long Polling độc lập)
│   └── gdrive_appscript_setup.js            # Mã Google Apps Script triển khai Web App Drive
│
├── 📥 van_ban_den/                          # KHO TIẾP NHẬN TÀI LIỆU ĐẦU VÀO
│   └── 2026/                                # Phân loại theo cơ quan cấp trên & năm
│
├── 📤 van_ban_du_thao/                      # KHO LƯU TRỮ DỰ THẢO ĐẦU RA (.DOCX)
│   └── 2026/                                # Phân mục theo thể loại (Cong_van, Bao_cao...)
│
└── 📚 references/                           # TRI THỨC ĐỊA PHƯƠNG & QUY PHẠM
    ├── tong_quan_xa_cong_hai.md             # Tri thức xã Công Hải, 08 thôn, 21 chi bộ
    ├── chi_tieu_nhiem_ky.json               # 20 chỉ tiêu Đại hội Đảng bộ xã khoá I
    └── Cam_nang_Nghiep_vu_Tham_muu_Cap_uy.md # Thẩm quyền, SLA, chức năng 5 cơ quan
```

---

## 🔒 NGUYÊN TẮC AN TOÀN & BẢO MẬT (SECURITY FIRST)

1. **Chống Path Traversal tại `/api/download`:** 
   - Tuyệt đối cấm tải các tệp ngoài thư mục `van_ban_du_thao/`.
   - Bắt buộc kiểm tra phần mở rộng tệp: Chỉ cho phép tải `.docx` và `.pdf`. Ngăn chặn hoàn toàn nguy cơ lộ file `.env` hoặc CSDL SQLite.
2. **Chốt chặn Độ mật (Secret Document Gatekeeper):**
   - Quét từ khóa đóng dấu độ mật (`MẬT`, `TỐI MẬT`, `TUYỆT MẬT`). Nếu phát hiện, hệ thống **lập tức từ chối xử lý và không gửi lên AI**, tuân thủ nghiêm ngặt Quyết định 37-QĐ/ĐU và Nghị định 63/2026/NĐ-CP.
3. **Cơ chế An toàn Human-in-the-Loop:**
   - Tuyệt đối không tự ý ký số, ban hành hay gửi văn bản. Mọi văn bản AI tạo ra là **bản dự thảo tham mưu**. Cán bộ có toàn quyền xem trước, chỉnh sửa và bấm duyệt.
4. **Không hỏi, không lưu trữ mật khẩu** của cán bộ dưới bất kỳ hình thức nào.

---

## 🛠️ HƯỚNG DẪN KHỞI ĐỘNG VÀ VẬN HÀNH

### 1. Cài đặt môi trường (Lần đầu tiên):
```powershell
# 1. Cài đặt thư viện Python
pip install -r requirements.txt

# 2. Tải mô hình Vector Embedding cục bộ qua Ollama (miễn phí, nhanh):
ollama pull nomic-embed-text

# 3. Tạo file cấu hình môi trường .env (từ mẫu .env.example)
copy .env.example .env
# Điền DEEPSEEK_API_KEY hoặc bật chế độ OLLAMA_LOCAL
```

### 2. Khởi động Máy chủ Web Backend (Văn phòng làm việc):
```powershell
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload
```
- Mở trình duyệt truy cập: `http://localhost:8000`
- Giao diện cung cấp đầy đủ: Khung chat AI, Đính kèm tài liệu, Xem trước đối soát RAG, Quản lý Sổ Nhiệm vụ và Chỉ tiêu KPI.

### 3. Khởi động Zalo Bot (Di động 24/7):
```powershell
python scripts/run_zalo_bot.py
```
- Cán bộ gửi lệnh hoặc file Word/PDF trực tiếp từ điện thoại.
- Bot tự động phản hồi dự thảo tham mưu và trả link Google Drive để tải văn bản ngay lập tức.

---
*Hệ thống được phát triển chuyên biệt phục vụ công tác tham mưu cấp uỷ tại Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà.*
