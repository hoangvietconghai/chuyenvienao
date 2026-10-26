# KẾ HOẠCH TRIỂN KHAI SỔ NHIỆM VỤ, SỔ TIÊU CHÍ VÀ BỘ HẸN GIỜ TỰ ĐỘNG
**Dự án:** Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà  
**Tài liệu kỹ thuật:** Định hướng kiến trúc, cơ sở dữ liệu SQL, giao diện quản trị CRUD và lộ trình thực thi (Dành cho giai đoạn triển khai tiếp theo)

---

## I. MỤC TIÊU VÀ TẦM NHÌN

Hiện tại, hệ thống đã hoàn thiện xuất sắc năng lực **Soạn thảo văn bản chuẩn Hướng dẫn 05-HD/VPTW**, **Bóc tách 5 Rõ**, **Tải tệp lên Google Drive đám mây** và **Tương tác qua Zalo Bot 24/7**.

Bước phát triển đột phá tiếp theo là chuyển đổi từ **"Trợ lý soạn thảo theo yêu cầu"** sang **"Hệ sinh thái Điều phối, Giám sát Tiến độ và Quản trị Công việc Chủ động"**:
1. **Sổ Nhiệm vụ Cơ quan (Task Registry):** Tự động bóc tách và lưu trữ các nhiệm vụ giao cho 5 cơ quan chuyên môn và 08 thôn từ các Công văn giao việc (-CV/ĐU) và Thông báo kết luận (-TB/ĐU).
2. **Sổ Tiêu chí Nghị quyết & KTXH (KPI & Milestone Registry):** Theo dõi tiến độ các chỉ tiêu Đại hội Đảng bộ xã lần thứ I (hàng năm, hàng quý, hàng tháng) để kịp thời cảnh báo khi có nguy cơ trễ hạn.
3. **Bộ Hẹn Giờ TỰ Động (Scheduler & Proactive Reminder Engine):** Định kỳ quét cơ sở dữ liệu, tự động gửi tin nhắn Zalo đôn đốc từng cán bộ phụ trách hoặc gửi thông báo vào Nhóm Zalo cơ quan hoàn toàn tự động.
4. **Giao diện Quản trị Trực quan (Visual Web CRUD & Dashboard):** Cung cấp các trang quản lý chuyên nghiệp dạng Tab (Kanban, Bảng dữ liệu, Tiến độ chỉ tiêu, Danh bạ cán bộ) giúp Thường trực Đảng uỷ và Chánh Văn phòng nắm trọn bức tranh toàn cảnh chỉ sau vài giây.

---

## II. THIẾT KẾ CƠ SỞ DỮ LIỆU QUAN HỆ (SQLITE ENGINE)

Thay vì lưu trữ bằng các tệp JSON thuần túy (dễ bị xung đột ghi đồng thời giữa Scheduler và Zalo Webhook, nguy cơ hỏng tệp khi mất điện đột ngột), hệ thống nâng cấp sử dụng **Cơ sở dữ liệu SQLite (`data/chuyen_vien_ao.db`)**:
* **Không cần cài đặt máy chủ:** Tích hợp sẵn 100% trong Python chuẩn (`sqlite3` / `aiosqlite`).
* **Đóng gói trong 01 file duy nhất:** Dễ dàng sao lưu, di chuyển máy trạm hoặc đưa lên Google Drive.
* **Đảm bảo giao dịch ACID & WAL Mode:** An toàn tuyệt đối, chống mất dữ liệu khi mất điện đột ngột, hỗ trợ đa luồng đọc/ghi đồng thời cực nhanh (< 1ms).

### Sơ đồ Quan hệ Dữ liệu (Entity Relationship):

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│        danh_ba_can_bo           │       │           so_nhiem_vu           │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ PK can_bo_id (VARCHAR)          │◄──────┤ PK task_id (VARCHAR)            │
│    ho_ten (VARCHAR)             │       │    so_hieu_vb (VARCHAR)         │
│    chuc_vu (VARCHAR)            │       │    FK can_bo_id (VARCHAR)       │
│    co_quan (VARCHAR)            │       │    co_quan_chu_tri (VARCHAR)    │
│    co_quan_loai (co_quan/thon)  │       │    co_quan_phoi_hop (TEXT/JSON) │
│    zalo_chat_id (VARCHAR)       │       │    noi_dung_nhiem_vu (TEXT)     │
│    zalo_user_id (VARCHAR)       │       │    ngay_giao (DATE)             │
│    so_dien_thoai (VARCHAR)      │       │    deadline (DATE)              │
│    vai_tro (lanh_dao/chuyen_vien│       │    che_do_bao_cao (TEXT)        │
└─────────────────────────────────┘       │    trang_thai (TEXT)            │
                                          │    muc_do_uu_tien (TEXT)        │
                                          │    linh_vuc (TEXT)              │
                                          │    ket_qua_bao_cao (TEXT)       │
                                          └────────────────┬────────────────┘
                                                           │ 1
                                                           │ n
                                          ┌────────────────▼────────────────┐
                                          │        lich_su_nhac_nho         │
                                          ├─────────────────────────────────┤
                                          │ PK log_id (INTEGER AUTO)        │
                                          │ FK task_id (VARCHAR)            │
                                          │    thoi_gian_nhac (DATETIME)    │
                                          │    hinh_thuc (zalo_1_1 / group) │
                                          │    noi_dung_nhac (TEXT)         │
                                          │    ket_qua (success / failed)   │
                                          └─────────────────────────────────┘
```

---

### Chi tiết các Bảng Dữ liệu Chuẩn hoá:

#### 1. Bảng Danh bạ Cán bộ (`danh_ba_can_bo`)
Quản lý cán bộ thuộc 5 cơ quan chuyên môn cấp xã (UBND, Ban Xây dựng Đảng, UBKT, UBMTTQ, Văn phòng Đảng uỷ) và 08 thôn (Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng):
* `can_bo_id` (PK): Mã định danh (ví dụ: `CB-UBND-01`, `CB-THON-03`).
* `ho_ten`: Họ và tên cán bộ (ví dụ: "Nguyễn Văn A").
* `chuc_vu`: Chức vụ hành chính hoặc chức vụ Đảng (ví dụ: "Phó Chủ tịch UBND xã", "Bí thư Chi bộ thôn Bình Tiên").
* `co_quan`: Đơn vị trực thuộc.
* `zalo_chat_id`: Định danh cuộc trò chuyện Zalo với Bot để gửi tin đôn đốc 1-1.
* `vai_tro`: Phân quyền truy cập (`lanh_dao_thuong_truc`, `lanh_dao_co_quan`, `chuyen_vien`, `bi_thu_thon`).

#### 2. Bảng Sổ Nhiệm vụ (`so_nhiem_vu`)
Lưu trữ toàn bộ các nhiệm vụ phát sinh từ văn bản hoặc giao trực tiếp:
* `task_id` (PK): Mã nhiệm vụ (ví dụ: `NV-2026-001`).
* `so_hieu_vb`: Số hiệu văn bản nguồn (ví dụ: `42-TB/ĐU`, `817-CV/ĐU`).
* `can_bo_id` (FK): Khóa ngoại liên kết tới cán bộ chịu trách nhiệm chính.
* `co_quan_chu_tri`: Tên cơ quan chủ trì (ví dụ: "Uỷ ban nhân dân xã").
* `co_quan_phoi_hop`: Mảng JSON các đơn vị phối hợp.
* `noi_dung_nhiem_vu`: Nội dung công việc cụ thể theo nguyên tắc 5 Rõ.
* `ngay_giao`: Ngày giao việc (`dd/mm/yyyy`).
* `deadline`: Hạn chót hoàn thành (`dd/mm/yyyy`).
* `che_do_bao_cao`: Yêu cầu báo cáo (trước mấy giờ, gửi cho ai).
* `trang_thai`: Trạng thái thực hiện (`Chưa thực hiện`, `Đang thực hiện`, `Hoàn thành`, `Quá hạn`).
* `muc_do_uu_tien`: `Bình thường`, `Cao`, `Khẩn`.
* `linh_vuc`: `Xây dựng Đảng`, `Kinh tế - Xã hội`, `Chuyển đổi số & Đề án 06`, `Quốc phòng - An ninh`.
* `ket_qua_bao_cao`: Tóm tắt kết quả khi hoàn thành hoặc link tệp báo cáo đính kèm.

#### 3. Bảng Lịch sử Nhắc việc (`lich_su_nhac_nho`)
Lưu lại vết đôn đốc của Bot để theo dõi tiến độ và ngăn ngừa gửi tin nhắn trùng lặp.

#### 4. Bảng Sổ Tiêu chí & Tiến độ (`so_tieu_chi` & `tien_do_tieu_chi`)
* Đối soát trực tiếp với 20 chỉ tiêu pháp lệnh của Đại hội Đảng bộ xã lần thứ I nhiệm kỳ 2025 - 2030 (trong `references/chi_tieu_nhiem_ky.json`).
* Theo dõi tiến độ động theo 3 tầng thời gian: Hàng năm (tăng trưởng 11-12%, ngân sách +12%, NTM nâng cao, xoá nghèo 2030), Hàng quý (thu thuế quý, giải ngân đầu tư công, hạ tầng Hồ Sông Trâu) và Hàng tháng (sinh hoạt chi bộ ngày 03, dịch vụ công trực tuyến $\ge 85\%$).

---

## III. THIẾT KẾ GIAO DIỆN QUẢN TRỊ TRỰC QUAN (WEB CRUD & DASHBOARD)

Hệ thống bổ sung **Thanh điều hướng Tab (Tab Navigation)** ngay trên thanh Topbar của giao diện Web hiện tại (`http://localhost:8000`), không làm gián đoạn khung chat hiện tại mà mở rộng không gian làm việc đa nhiệm:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ★ Chuyên viên ảo — Đảng uỷ xã Công Hải    [💬 Trợ lý Soạn thảo] [📋 Sổ Nhiệm Vụ] [🎯 Chỉ Tiêu] [👥 Danh Bạ] │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Tab `[📋 Sổ Nhiệm Vụ]` (Giao diện Quản trị CRUD Nhiệm vụ)
Cung cấp khả năng kiểm soát toàn diện vòng đời công việc của toàn xã:
* **Bộ lọc thông minh (Filters):**
  * Lọc theo Cơ quan: Tất cả, UBND xã, Ban Xây dựng Đảng, UBKT, MTTQ, 08 thôn.
  * Lọc theo Trạng thái: Tất cả, Đang thực hiện, Quá hạn, Đến hạn hôm nay, Đã hoàn thành.
  * Lọc theo Độ ưu tiên: Khẩn, Cao, Bình thường.
  * Ô tìm kiếm từ khoá theo nội dung nhiệm vụ hoặc cán bộ phụ trách.
* **2 Chế độ hiển thị linh hoạt:**
  * **Chế độ Kanban (Kanban Board):** 3 cột thẻ trực quan (*Chưa thực hiện $\rightarrow$ Đang thực hiện $\rightarrow$ Hoàn thành*). Cán bộ có thể kéo thả hoặc click chuyển trạng thái tức thì. Các nhiệm vụ quá hạn sẽ tự động đổi viền đỏ cảnh báo.
  * **Chế độ Bảng Dữ liệu (Data Table):** Hiển thị danh sách chi tiết có phân trang, hỗ trợ nút **"Xuất Excel Báo cáo Giao ban"** để phục vụ các cuộc họp Thường trực Đảng uỷ.
* **Hành động CRUD đầy đủ:**
  * **➕ Thêm nhiệm vụ (Create):** Modal nhập việc mới phát sinh đột xuất hoặc lãnh đạo giao miệng (chọn cơ quan, người làm, hạn chót, nội dung).
  * **✏️ Chỉnh sửa (Update):** Gia hạn tiến độ (Deadline), đổi cán bộ phụ trách, cập nhật ghi chú tiến độ.
  * **✅ Đánh dấu hoàn thành (Quick Complete):** Chuyển trạng thái sang "Hoàn thành" chỉ bằng 1 cú nhấp chuột, kèm ô nhập tóm tắt kết quả.
  * **🗑️ Xoá nhiệm vụ (Delete):** Cho phép Chánh Văn phòng xoá các đầu việc trùng lặp hoặc đã bị huỷ bỏ.

### 2. Tab `[🎯 Giám sát Chỉ tiêu]` (KPIs Dashboard)
* Trực quan hoá 20 chỉ tiêu Đại hội Đảng bộ xã lần thứ I thành các **Thanh tiến độ phần trăm (Progress Bars)** và biểu đồ đo lường:
  * Tốc độ tăng trưởng sản xuất: Đạt $11.5\% / 12\%$ (Xanh lá).
  * Thu ngân sách nhà nước: Đạt $85\%$ kế hoạch năm (Vàng - Cần đôn đốc quý 4).
  * Xây dựng Nông thôn mới nâng cao: Đạt $16 / 19$ tiêu chí.
  * Dịch vụ công trực tuyến toàn trình (Đề án 06): $88\% / 85\%$ (Đạt).
  * Tỷ lệ sinh hoạt chi bộ ngày 03 hàng tháng: $100\% (8/8\text{ thôn})$.
* Cho phép cán bộ phụ trách cập nhật số liệu định kỳ hàng tháng/quý.

### 3. Tab `[👥 Danh bạ Cán bộ]` (Directory CRUD)
* Quản lý thông tin cán bộ phụ trách của 5 cơ quan và 8 Bí thư Chi bộ thôn.
* Hỗ trợ thêm mới, chỉnh sửa thông tin nhân sự khi có điều động, luân chuyển công tác, bảo đảm bot luôn gửi tin nhắn nhắc việc đúng người, đúng việc.

---

## IV. BỘ HẸN GIỜ TỰ ĐỘNG VÀ CÁC GIẢI PHÁP BỀN BỈ (SCHEDULER ENGINE)

### 1. Kiến trúc kỹ thuật:
* **Module:** `server/services/scheduler_service.py` sử dụng `AsyncIOScheduler`.
* **Cơ chế Khởi động bù (Catch-up Scan on Startup):** Khắc phục nhược điểm máy tính văn phòng tắt ban đêm/cuối tuần. Khi cán bộ bật máy tính lúc 08h00 sáng, hệ thống lập tức quét các lịch của khung giờ 07h30 chưa kịp gửi để nhắc bù ngay, đảm bảo không bỏ sót việc.
* **Cơ chế Gom nhóm Thông báo (Digest / Batching Reminder):** Nếu một cán bộ có 3 nhiệm vụ cùng đến hạn trong ngày, Bot tự động gộp thành 01 tin nhắn tổng hợp duy nhất, tránh tình trạng spam gây quá tải thông báo.

### 2. Ma trận Lịch hẹn giờ định kỳ:

| Tần suất | Thời gian | Tác vụ thực hiện | Đối tượng nhận |
| :--- | :---: | :--- | :--- |
| **Hàng ngày** | **07h30 sáng** | Quét các nhiệm vụ có hạn hôm nay & ngày mai $\rightarrow$ Gom nhóm nhắc việc | Gửi tin nhắn riêng (1-1) cho từng cán bộ phụ trách |
| **Hàng ngày** | **16h30 chiều** | Quét các nhiệm vụ hết hạn trong ngày chưa báo cáo hoàn thành | Cảnh báo cán bộ phụ trách & báo Thường trực Đảng uỷ |
| **Thứ Sáu** | **08h00 sáng** | Đôn đốc 5 cơ quan và 8 thôn gửi Báo cáo tuần trước 11h00 | Gửi tin nhắn vào Nhóm Zalo cơ quan |
| **Thứ Sáu** | **14h00 chiều** | Tự động tổng hợp dữ liệu báo cáo tuần thành bản dự thảo sơ bộ | Báo tin cho Chánh Văn phòng Đảng uỷ |
| **Ngày mùng 1** | **08h00 sáng** | Nhắc các Chi uỷ thôn chuẩn bị sinh hoạt chi bộ ngày mùng 3 | Gửi tin nhắn cho 08 Bí thư Chi bộ thôn |
| **Ngày 25** | **08h30 sáng** | Đôn đốc gửi số liệu Báo cáo tháng của Đảng uỷ xã | Nhắn vào Nhóm chuyên môn |
| **Cuối quý** | **Tuần 11** | Rà soát chỉ tiêu quý $\rightarrow$ Cảnh báo các chỉ tiêu $< 80\%$ | Báo cáo Thường trực Đảng uỷ xã |

---

## V. KỊCH BẢN TƯƠNG TÁC THÔNG MINH TRÊN ZALO

1. **Cán bộ hỏi việc của mình:**
   * Cán bộ nhắn: *"Hôm nay tôi có nhiệm vụ gì cần làm?"*
   * Bot nhận diện `chat_id` $\rightarrow$ Tra cứu CSDL SQLite $\rightarrow$ Trả lời nhanh trong 1 giây.
2. **Lãnh đạo kiểm tra tiến độ chung:**
   * Thường trực nhắn: *"Hiện tại có những việc nào bị chậm tiến độ?"*
   * Bot truy vấn các bản ghi `Quá hạn` $\rightarrow$ Trả về bảng tổng hợp phân loại theo UBND xã, Ban Xây dựng Đảng, các thôn.
3. **Báo cáo hoàn thành một chạm (Interactive Status Update):**
   * Cán bộ chỉ cần phản hồi vào tin nhắn nhắc việc: *"Đã xong NV-2026-001"* kèm file báo cáo.
   * Bot tự động đổi trạng thái sang `Hoàn thành`, lưu link tài liệu và thông báo cho Thường trực Đảng uỷ.
4. **Giao việc nhanh bằng tin nhắn:**
   * Lãnh đạo nhắn: *"Giao UBND xã kiểm tra việc nạo vét mương thôn Ma Trai xong trước 30/10"*.
   * Bot tạo bản ghi trong SQLite, dự thảo công văn giao việc và gửi tin báo cho cán bộ phụ trách UBND xã.

---

## VI. LỘ TRÌNH THỰC THI 4 BƯỚC (DÀNH CHO LẦN THỰC HIỆN SAU)

Khi Cán bộ muốn triển khai, chỉ cần yêu cầu AI: **"Bắt đầu thực hiện Kế hoạch tại file KE_HOACH_SO_NHIEM_VU_VA_HEN_GIO.md"**, quy trình sẽ lần lượt gồm 4 bước:

* **Bước 1 (Xây dựng CSDL SQLite & Data Service):**
  * Tạo tệp CSDL `data/chuyen_vien_ao.db` và khởi tạo các bảng: `danh_ba_can_bo`, `so_nhiem_vu`, `lich_su_nhac_nho`, `so_tieu_chi`.
  * Viết module `server/services/db_service.py` với các hàm CRUD an toàn (Async SQLite / Transactions).
  * Nạp dữ liệu ban đầu (Seed data) cho 5 cơ quan, 08 thôn và 20 chỉ tiêu Đại hội Đảng bộ xã.
* **Bước 2 (Tích hợp Tự động Bóc tách từ Văn bản):**
  * Cập nhật hàm `_confirm()` trong `server/chat_engine.py`: Khi Cán bộ bấm "Duyệt" Công văn giao việc hoặc Thông báo kết luận cuộc họp $\rightarrow$ Tự động bóc tách các nhiệm vụ "5 Rõ" và lưu thẳng vào bảng `so_nhiem_vu` trong SQLite.
* **Bước 3 (Xây dựng Bộ Hẹn Giờ Scheduler & Zalo Batching):**
  * Xây dựng `server/services/scheduler_service.py` tích hợp `zalo_api.py`.
  * Thiết lập cơ chế bù lịch khi khởi động (`catch_up_missed_jobs`) và cơ chế gom nhóm thông báo nhắc việc.
* **Bước 4 (Phát triển Giao diện Quản trị CRUD & Dashboard):**
  * Nâng cấp `server/static/index.html`, `app.js`, `style.css` với hệ thống Tab Navigation:
    * Tab 1: Trợ lý Soạn thảo (Chatbot hiện tại).
    * Tab 2: Sổ Nhiệm Vụ (CRUD Kanban & Data Table).
    * Tab 3: Giám sát Chỉ tiêu (KPIs Dashboard thanh tiến độ).
    * Tab 4: Danh bạ Cán bộ (Quản trị nhân sự & Zalo Chat ID).
  * Cung cấp các API RESTful trong `server/app.py` phục vụ các thao tác CRUD trên giao diện web.

---
*Kế hoạch kỹ thuật này đã được chuẩn hoá toàn diện và sẵn sàng kích hoạt bất cứ lúc nào theo chỉ đạo của cán bộ.*
