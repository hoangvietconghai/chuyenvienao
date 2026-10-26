# KẾ HOẠCH TRIỂN KHAI SỔ NHIỆM VỤ, SỔ TIÊU CHÍ, BỘ HỆN GIỜ & HỆ THỐNG HYBRID RAG
**Dự án:** Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà  
**Tài liệu kỹ thuật & Checklist thực thi:** Định hướng kiến trúc SQLite hợp nhất, Hybrid RAG 1.000+ văn bản, bộ hẹn giờ tự động và giao diện quản trị CRUD đa nhiệm.

---

## I. MỤC TIÊU VÀ TẦM NHÌN KIẾN TRÚC

Nâng cấp hệ thống từ **"Trợ lý soạn thảo theo yêu cầu"** sang **"Hệ sinh thái Điều phối, Giám sát Tiến độ và Kho Tri thức Hành chính Chủ động"** gói gọn trong 01 tệp cơ sở dữ liệu duy nhất (`data/chuyen_vien_ao.db`):
1. **Sổ Nhiệm vụ Cơ quan (Task Registry):** Tự động bóc tách nhiệm vụ "5 Rõ" từ các Công văn giao việc (`-CV/ĐU`) và Thông báo kết luận (`-TB/ĐU`) giao cho 05 cơ quan chuyên môn và 08 thôn.
2. **Sổ Tiêu chí Nghị quyết & KTXH (KPI & Milestone Registry):** Giám sát thời gian thực 20 chỉ tiêu pháp lệnh Đại hội Đảng bộ xã lần thứ I (nhiệm kỳ 2025 - 2030) và các chỉ tiêu Chuyển đổi số (NQ57).
3. **Kho Tri thức Hybrid RAG (1.000+ Văn bản Đến & Đi):** Kết hợp tìm kiếm siêu dữ liệu (Metadata SQL), từ khóa chính xác (SQLite FTS5 BM25) và ngữ nghĩa (Vector Embedding) để tra cứu, trích dẫn căn cứ pháp lý và tổng hợp số liệu tức thì.
4. **Bộ Hẹn Giờ Tự Động (Proactive Scheduler Engine):** Quét CSDL định kỳ, gom nhóm thông báo (Digest), tự động nhắc bù khi máy tính văn phòng bật muộn (Catch-up Scan) và chống gửi lặp 100% (Idempotency).
5. **Giao diện Quản trị Trực quan (Visual Web CRUD & Dashboard):** Mở rộng giao diện Web hiện tại (`http://localhost:8000`) thành 05 Tab làm việc chuyên nghiệp mà không làm gián đoạn luồng Chatbot.

---

## II. THIẾT KẾ CƠ SỞ DỮ LIỆU HỢP NHẤT (SQLITE WAL + FTS5 + VECTOR)

Sử dụng **SQLite (`data/chuyen_vien_ao.db`)** bật chế độ `PRAGMA journal_mode=WAL;` và `PRAGMA foreign_keys=ON;` để đảm bảo đọc/ghi đồng thời giữa Web Server, Zalo Webhook, Bộ Hẹn giờ và Tiến trình Index văn bản.

### Sơ đồ Kiến trúc Bảng Dữ liệu:

```text
┌───────────────────────────┐       ┌───────────────────────────┐
│      danh_ba_can_bo       │       │        so_nhiem_vu        │
├───────────────────────────┤       ├───────────────────────────┤
│ PK can_bo_id (TEXT)       │◄──────┤ PK task_id (TEXT)         │
│    ho_ten (TEXT)          │       │    so_hieu_vb (TEXT)      │
│    chuc_vu (TEXT)         │       │ FK can_bo_id (TEXT)       │
│    co_quan (TEXT)         │       │    co_quan_chu_tri (TEXT) │
│    co_quan_code (TEXT)    │       │    co_quan_phoi_hop (JSON)│
│    co_quan_loai (TEXT)    │       │    noi_dung_nhiem_vu(TEXT)│
│    zalo_chat_id (TEXT)    │       │    ngay_giao (YYYY-MM-DD) │
│    zalo_user_id (TEXT)    │       │    deadline_date (ISO)    │
│    so_dien_thoai (TEXT)   │       │    deadline_time (HH:MM)  │
│    vai_tro (TEXT)         │       │    trang_thai (TEXT)      │
│    is_active (INTEGER)    │       │    muc_do_uu_tien (TEXT)  │
└───────────────────────────┘       │    linh_vuc (TEXT)        │
                                    │    ket_qua_bao_cao (TEXT) │
┌───────────────────────────┐       │    created_from_wf (TEXT) │
│        so_tieu_chi        │       └─────────────┬─────────────┘
├───────────────────────────┤                     │ 1:N
│ PK kpi_id (TEXT)          │       ┌─────────────▼─────────────┐
│    nhom_chi_tieu (TEXT)   │       │     lich_su_nhac_nho      │
│    ten_chi_tieu (TEXT)    │       ├───────────────────────────┤
│    don_vi_tinh (TEXT)     │       │ PK log_id (INTEGER AUTO)  │
│    gia_tri_muc_tieu (REAL)│       │ UK remind_key (TEXT)      │
│    gia_tri_hien_tai (REAL)│       │ FK task_id (TEXT)         │
│    ky_danh_gia (TEXT)     │       │    loai_nhac (TEXT)       │
│    co_quan_phu_trach(TEXT)│       │    thoi_gian_nhac (ISO)   │
└───────────────────────────┘       │    ket_qua (TEXT)         │
                                    └───────────────────────────┘

┌───────────────────────────┐       ┌───────────────────────────┐
│        so_van_ban         │  1:N  │      van_ban_chunks       │
├───────────────────────────┤──────►├───────────────────────────┤
│ PK doc_id (TEXT)          │       │ PK chunk_id (INTEGER AUTO)│
│ UK file_hash (TEXT)       │       │ FK doc_id (TEXT)          │
│    so_hieu_vb (TEXT)      │       │    section_title (TEXT)   │
│    loai_luong (DEN / DI)  │       │    context_header (TEXT)  │
│    the_loai (CV/KH/BC/TB) │       │    chunk_text (TEXT)      │
│    trich_yeu (TEXT)       │       │    embedding (BLOB)       │
│    co_quan_ban_hanh (TEXT)│       └─────────────┬─────────────┘
│    ngay_ban_hanh (ISO)    │                     │ Đồng bộ Trigger
│    linh_vuc (TEXT)        │       ┌─────────────▼─────────────┐
│    file_path (TEXT)       │       │    van_ban_fts (FTS5)     │
│    gdrive_url (TEXT)      │       ├───────────────────────────┤
│    trang_thai_hieu_luc    │       │    so_hieu_vb, trich_yeu, │
└───────────────────────────┘       │    context_header, text   │
                                    └───────────────────────────┘
```

### Quy chuẩn Kỹ thuật Bắt buộc trong Database:
1. **Chuẩn hóa Ngày/Giờ (ISO-8601):** Mọi cột ngày tháng (`ngay_giao`, `deadline_date`, `ngay_ban_hanh`) trong SQLite bắt buộc lưu định dạng `YYYY-MM-DD` để phục vụ toán tử so sánh (`<`, `>`, `BETWEEN`) và sắp xếp. Tầng UI/Zalo sẽ format sang `dd/mm/yyyy` khi hiển thị.
2. **Chống gửi lặp Zalo (Idempotency):** Cột `remind_key` trong `lich_su_nhac_nho` có ràng buộc `UNIQUE` (VD: `MORNING_2026-10-26_CB-UBND-01`). Sử dụng `INSERT OR IGNORE` trước khi gọi Zalo API.
3. **Chunking Hành chính cho RAG:** Mỗi đoạn cắt (`chunk_text`) luôn được ghép sẵn `context_header` theo mẫu: `[Văn bản: {so_hieu_vb} | Ngày: {ngay_ban_hanh} | Trích yếu: {trich_yeu} | Mục: {section_title}]` để AI không bao giờ nhầm lẫn ngữ cảnh giữa các văn bản.

---

## III. CHECKLIST LỘ TRÌNH THỰC THI CHI TIẾT (5 GIAI ĐOẠN)

### GIAI ĐOẠN 1: Xây dựng Nền móng SQLite & Đồng bộ Dữ liệu Gốc (Data Layer)
- [ ] **1.1. Khởi tạo `server/services/db_service.py`:**
  - [ ] Thiết lập kết nối SQLite với `WAL mode`, `foreign_keys=ON`, hỗ trợ context manager an toàn giao dịch (ACID).
  - [ ] Viết hàm `init_db()` tự động tạo 06 bảng cốt lõi: `danh_ba_can_bo`, `so_nhiem_vu`, `lich_su_nhac_nho`, `so_tieu_chi`, `so_van_ban`, `van_ban_chunks` và bảng ảo `van_ban_fts` (FTS5).
- [ ] **1.2. Viết các hàm CRUD chuẩn hóa trong `db_service.py`:**
  - [ ] Nhóm hàm Cán bộ: `get_directory()`, `upsert_can_bo()`, `get_can_bo_by_zalo_id()`, `get_can_bo_by_unit()`.
  - [ ] Nhóm hàm Nhiệm vụ: `create_task()`, `update_task()`, `complete_task()`, `delete_task()`, `list_tasks(filters)`, `get_due_and_overdue_tasks()`.
  - [ ] Nhóm hàm Chỉ tiêu: `get_all_kpis()`, `update_kpi_progress()`.
  - [ ] Nhóm hàm Nhắc việc: `acquire_remind_lock(remind_key)`, `update_remind_status()`.
- [ ] **1.3. Viết Script Nạp dữ liệu gốc (`scripts/seed_database.py`):**
  - [ ] Nạp danh bạ 05 cơ quan (UBND xã, Ban Xây dựng Đảng, UBKT, UBMTTQ, Văn phòng Đảng uỷ) và 08 thôn (Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng).
  - [ ] Chuyển đổi dữ liệu từ `references/chi_tieu_nhiem_ky.json` và hệ chỉ tiêu NQ57 vào bảng `so_tieu_chi`.
  - [ ] Chuyển đổi dữ liệu từ `references/so_ke_hoach_chi_dao.json`, `Bang_phan_cong_To_ho_tro_CD_so_Cong_Hai.xlsx` và `Phu_luc_nhiem_vu_CDS_QD11_va_KH04.xlsx` vào bảng `so_nhiem_vu`.
- [ ] **1.4. Kết nối tương thích ngược với `server/plan_registry.py`:**
  - [ ] Chuyển các lệnh đọc/ghi JSON trong `plan_registry.py` sang gọi trực tiếp `db_service.py` để không làm gãy các workflow hiện hữu.

---

### GIAI ĐOẠN 2: Xây dựng Hệ thống Hybrid RAG cho 1.000+ Văn bản Đến & Đi
- [ ] **2.1. Nâng cấp bộ đọc tài liệu (`scripts/doc_reader.py` & `server/services/rag_service.py`):**
  - [ ] Bóc tách Metadata tự động từ tên file và phần đầu văn bản (`.docx`, `.doc`, `.pdf`, `.md`): Số hiệu, Ngày ban hành, Cơ quan ban hành, Trích yếu, Loại luồng (`van_ban_den` / `van_ban_du_thao`).
  - [ ] Kiểm tra trùng lặp bằng mã băm `SHA-256 (file_hash)` — chỉ đánh chỉ mục (index) những văn bản mới hoặc có chỉnh sửa.
- [ ] **2.2. Thuật toán Chia nhỏ theo Cấu trúc Hành chính (Structural Chunking):**
  - [ ] Chia văn bản theo các mốc đề mục lớn (`I.`, `II.`, `III.`, `Điều 1.`, `Điều 2.`, `1.`, `2.`).
  - [ ] Tự động đính kèm `context_header` vào đầu mỗi chunk và lưu vào `van_ban_chunks` + đồng bộ sang bảng tìm kiếm toàn văn `van_ban_fts` (BM25).
  - [ ] Tạo Vector Embedding (sử dụng Gemini Embedding API hoặc local model) lưu dạng nén nhị phân (`BLOB`) để tìm kiếm ngữ nghĩa kết hợp với BM25 (Reciprocal Rank Fusion - RRF).
- [ ] **2.3. Viết công cụ Quét & Đánh chỉ mục Hàng loạt (`scripts/index_all_documents.py`):**
  - [ ] Quét toàn bộ thư mục `van_ban_den/`, `van_ban_du_thao/`, `references/` để nạp hơn 1.000 văn bản vào SQLite.
  - [ ] Tích hợp cơ chế Auto-Index: Tự động nạp vào kho RAG mỗi khi cán bộ tải văn bản mới lên hoặc bấm "Duyệt" văn bản dự thảo.
- [ ] **2.4. Tích hợp RAG vào 4 Workflows và Chế độ Hỏi đáp (`chat_engine.py`):**
  - [ ] Cho phép AI tự động truy xuất văn bản cũ để điền phần *"Căn cứ..."* và đối chiếu số liệu lịch sử khi chạy WF1, WF2, WF3, WF4.

---

### GIAI ĐOẠN 3: Tự động Bóc tách "5 Rõ" & Khép kín Luồng Nghiệp vụ
- [ ] **3.1. Tự động Bóc tách Nhiệm vụ khi Duyệt văn bản (`server/chat_engine.py`):**
  - [ ] Trong hàm `_confirm()`, khi người dùng duyệt Công văn giao việc (WF3) hoặc Thông báo kết luận (WF2), kích hoạt prompt trích xuất cấu trúc JSON theo chuẩn 5 Rõ: *(1. Nội dung việc - 2. Cơ quan chủ trì - 3. Đơn vị phối hợp - 4. Hạn hoàn thành YYYY-MM-DD - 5. Chế độ báo cáo)*.
  - [ ] Tự động đối chiếu với bảng `danh_ba_can_bo` để gán đúng `can_bo_id` phụ trách và lưu vào `so_nhiem_vu`.
- [ ] **3.2. Tự động Tổng hợp Ngược về Báo cáo tuần (`server/workflows/wf1_synthesizer.py`):**
  - [ ] Khi chạy WF1 (Tổng hợp báo cáo tuần/tháng), tự động truy vấn SQLite lấy danh sách nhiệm vụ `Hoàn thành` trong kỳ đưa vào Mục I, và nhiệm vụ `Đang thực hiện` / `Quá hạn` / `Sắp đến hạn` đưa vào Mục II.
- [ ] **3.3. Nâng cấp Kịch bản Tương tác Zalo Thông minh (`server/routers/zalo_webhook.py`):**
  - [ ] **Tra cứu việc cá nhân:** Cán bộ nhắn *"Việc của tôi"* hoặc *"Hôm nay có việc gì?"* $\rightarrow$ Tra `zalo_chat_id` trả về danh sách việc đang làm & sắp đến hạn.
  - [ ] **Kiểm tra tiến độ cho Lãnh đạo:** Nhắn *"Việc quá hạn"* $\rightarrow$ Tổng hợp các đầu việc trễ hạn phân theo từng cơ quan, thôn.
  - [ ] **Báo cáo hoàn thành 1 chạm:** Nhắn *"Xong NV-2026-001 [Ghi chú/File]"* $\rightarrow$ Đổi trạng thái sang `Hoàn thành` và báo tin cho Thường trực/Chánh Văn phòng.
  - [ ] **Giao việc nhanh qua Zalo:** Nhắn *"Giao [Đơn vị] [Nội dung] trước [Ngày]"* $\rightarrow$ Tự động ghi vào `so_nhiem_vu` và nhắn thông báo cho đơn vị nhận việc.
  - [ ] **Tra cứu Kho Văn bản RAG qua Zalo:** Nhắn *"Tìm văn bản [từ khóa / số hiệu]"* $\rightarrow$ Trả lời tóm tắt nội dung kèm link Google Drive.

---

## IV. BỘ HẸN GIỜ TỰ ĐỘNG & CƠ CHẾ BỀN BỈ (`scheduler_service.py`)
- [ ] **4.1. Xây dựng `server/services/scheduler_service.py` với `AsyncIOScheduler`:**
  - [ ] Gắn vào vòng đời `lifespan` của FastAPI (`server/app.py`) với cơ chế khóa tiến trình (tránh nhân bản job khi chạy multi-worker).
- [ ] **4.2. Cơ chế Khởi động bù (`catch_up_missed_jobs()`):**
  - [ ] Ngay khi bật máy tính văn phòng (VD: 08h00 sáng), hệ thống kiểm tra bảng `lich_su_nhac_nho` xem các lịch cố định trong ngày (như lịch 07h30) đã có `remind_key` chưa; nếu chưa thì lập tức chạy bù.
- [ ] **4.3. Cơ chế Gom nhóm Tin nhắn (`Digest / Batching Reminder`):**
  - [ ] Gom toàn bộ các nhiệm vụ đến hạn/quá hạn của cùng 1 cán bộ trong cùng đợt quét thành **01 tin nhắn Zalo tổng hợp duy nhất**, trình bày rõ ràng theo thứ tự ưu tiên (`Khẩn` $\rightarrow$ `Cao` $\rightarrow$ `Bình thường`).
- [ ] **4.4. Cấu hình Ma trận Lịch Hẹn Giờ Định Kỳ:**
  - [ ] **07h30 Hàng ngày:** Quét nhiệm vụ hạn hôm nay & ngày mai $\rightarrow$ Nhắn Zalo 1-1 cho từng cán bộ phụ trách.
  - [ ] **16h30 Hàng ngày:** Quét nhiệm vụ hết hạn trong ngày chưa báo cáo $\rightarrow$ Cảnh báo cán bộ & gửi tổng hợp cho Chánh Văn phòng / Thường trực Đảng uỷ.
  - [ ] **08h00 Thứ Sáu:** Đôn đốc 05 cơ quan và 08 thôn gửi số liệu Báo cáo tuần trước 11h00 vào Nhóm Zalo.
  - [ ] **14h00 Thứ Sáu:** Tự động gom dữ liệu nhiệm vụ trong tuần + văn bản đến/đi $\rightarrow$ Tạo dự thảo Báo cáo tuần gửi Chánh Văn phòng.
  - [ ] **08h00 Ngày mùng 01 hàng tháng:** Nhắc 08 Bí thư Chi bộ thôn chuẩn bị nội dung sinh hoạt chi bộ định kỳ ngày mùng 03.
  - [ ] **08h30 Ngày 25 hàng tháng:** Đôn đốc gửi số liệu Báo cáo tháng.
  - [ ] **Tuần thứ 11 mỗi Quý:** Rà soát bảng `so_tieu_chi`, cảnh báo các chỉ tiêu đạt $< 80\%$ lộ trình quý cho Thường trực Đảng uỷ.

---

## V. PHÁT TRIỂN RESTFUL API & GIAO DIỆN QUẢN TRỊ ĐA TAB (WEB UI)
- [ ] **5.1. Mở rộng RESTful API trong `server/app.py`:**
  - [ ] `GET / POST / PUT / DELETE /api/tasks`: Quản lý Sổ Nhiệm vụ & xuất file Excel báo cáo giao ban (`/api/tasks/export-excel`).
  - [ ] `GET / PUT /api/kpis`: Truy vấn và cập nhật tiến độ 20 chỉ tiêu Nghị quyết.
  - [ ] `GET / POST / PUT / DELETE /api/directory`: Quản lý Danh bạ cán bộ & cấu hình Zalo ID.
  - [ ] `GET / POST /api/documents`: Tìm kiếm Hybrid RAG trên giao diện Web và tải lên văn bản mới.
  - [ ] `POST /api/scheduler/trigger`: Nút bấm cho phép Chánh Văn phòng kích hoạt quét nhắc việc thủ công bất cứ lúc nào.
- [ ] **5.2. Nâng cấp Giao diện `index.html`, `style.css`, `app.js` với 05 Tab Điều hướng:**
  - [ ] **Tab 1 `[💬 Trợ lý Soạn thảo]`:** Giữ nguyên không gian Chatbot & 4 Workflows hiện tại.
  - [ ] **Tab 2 `[📋 Sổ Nhiệm Vụ]`:** Bộ lọc đa chiều (Cơ quan, Trạng thái, Độ ưu tiên, Từ khóa); chuyển đổi linh hoạt giữa **Bảng Kanban 3 cột** (hỗ trợ chuyển trạng thái nhanh, viền đỏ cho việc quá hạn) và **Bảng dữ liệu chi tiết**; Modal Thêm/Sửa/Hoàn thành nhiệm vụ; nút Xuất Excel Giao ban.
  - [ ] **Tab 3 `[📚 Kho Văn Bản RAG]`:** Thanh tìm kiếm thông minh (lọc theo Số hiệu, Ngày ban hành, Loại văn bản, Tìm kiếm ngữ nghĩa); xem nhanh nội dung trích xuất và mở link Google Drive.
  - [ ] **Tab 4 `[🎯 Giám sát Chỉ tiêu]`:** Dashboard trực quan hóa 20 chỉ tiêu Đại hội bằng Thanh tiến độ (Progress Bars) đổi màu tự động (Xanh $\ge 90\%$, Vàng $70-89\%$, Đỏ $< 70\%$) kèm nút cập nhật số liệu nhanh.
  - [ ] **Tab 5 `[👥 Danh Bạ Cán Bộ]`:** Giao diện CRUD quản lý nhân sự 05 cơ quan và 08 thôn, cập nhật nhanh `zalo_chat_id` khi có điều động, phân công mới.

---

## VI. KIỂM THỬ & NGHIỆM THU HỆ THỐNG (QUALITY ASSURANCE)

- [ ] **Kiểm thử chịu tải & đồng thời:** Chạy `scripts/test_system_integration.py` xác nhận SQLite WAL không bị lỗi `database is locked` khi vừa ghi nhiệm vụ từ Zalo vừa quét Scheduler.
- [ ] **Kiểm thử độ chính xác RAG:** Truy vấn thử nghiệm 20 câu hỏi hóc búa (hỏi theo số hiệu văn bản cụ thể, hỏi tổng hợp theo thôn, hỏi đối chiếu chỉ tiêu NQ57) đảm bảo tốc độ phản hồi $< 1.5\text{ giây}$ và trích dẫn đúng số hiệu văn bản gốc.
- [ ] **Kiểm thử Chống Spam Zalo:** Khởi động lại server 03 lần liên tiếp trong cùng một buổi sáng để xác nhận `catch_up_missed_jobs()` chỉ gửi tin nhắn nhắc việc đúng 01 lần duy nhất.