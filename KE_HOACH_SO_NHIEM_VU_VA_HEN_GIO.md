# KẾ HOẠCH TRIỂN KHAI SỔ NHIỆM VỤ, SỔ TIÊU CHÍ VÀ BỘ HẸN GIỜ TỰ ĐỘNG
**Dự án:** Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà  
**Tài liệu kỹ thuật:** Định hướng kiến trúc và lộ trình thực thi (Dành cho giai đoạn triển khai tiếp theo)

---

## I. MỤC TIÊU VÀ TẦM NHÌN

Hiện tại, hệ thống đã hoàn thiện xuất sắc năng lực **Soạn thảo văn bản chuẩn Hướng dẫn 05-HD/VPTW**, **Bóc tách 5 Rõ**, **Tải tệp lên Google Drive đám mây** và **Tương tác qua Zalo Bot 24/7**.

Bước phát triển đột phá tiếp theo là chuyển đổi từ **"Trợ lý soạn thảo theo yêu cầu"** sang **"Hệ thống Điều phối & Giám sát Tiến độ Chủ động"**:
1. **Sổ Nhiệm vụ Cơ quan (Task Registry):** Tự động bóc tách và lưu trữ các nhiệm vụ giao cho 5 cơ quan chuyên môn và 08 thôn từ các Công văn giao việc (-CV/ĐU) và Thông báo kết luận (-TB/ĐU).
2. **Sổ Tiêu chí Nghị quyết & KTXH (KPI & Milestone Registry):** Theo dõi tiến độ các chỉ tiêu Đại hội Đảng bộ xã lần thứ I (hàng năm, hàng quý, hàng tháng) để kịp thời cảnh báo khi có nguy cơ trễ hạn.
3. **Bộ Hẹn Giờ Tự Động (Scheduler & Proactive Reminder Engine):** Định kỳ quét cơ sở dữ liệu, tự động gửi tin nhắn Zalo đôn đốc từng cán bộ phụ trách hoặc gửi thông báo vào Nhóm Zalo cơ quan hoàn toàn tự động.

---

## II. THIẾT KẾ KIẾN TRÚC DỮ LIỆU

### 1. Sổ Nhiệm vụ Cơ quan (`data/so_nhiem_vu.json`)

Mỗi khi hệ thống xuất một Công văn giao việc (WF3) hoặc Thông báo kết luận (WF2), các nhiệm vụ "5 Rõ" được lưu vào Sổ nhiệm vụ theo cấu trúc chuẩn:

```json
[
  {
    "task_id": "NV-2026-001",
    "nguon_goc": {
      "loai_van_ban": "TB",
      "so_hieu": "Số 42-TB/ĐU",
      "ngay_ban_hanh": "20/10/2026",
      "trich_yeu": "Kết luận cuộc họp Thường trực Đảng uỷ tuần 42"
    },
    "co_quan_chu_tri": "Uỷ ban nhân dân xã",
    "co_quan_phoi_hop": ["Ban Xây dựng Đảng", "Cơ quan UBMTTQVN xã"],
    "can_bo_phu_trach": "Đồng chí Nguyễn Văn A",
    "zalo_chat_id": "b0ce7fa772e49bbac2f5",
    "noi_dung_nhiem_vu": "Hoàn thành rà soát hồ sơ đền bù giải phóng mặt bằng dự án đường ven biển qua thôn Bình Tiên",
    "ngay_giao": "20/10/2026",
    "deadline": "28/10/2026",
    "che_do_bao_cao": "Báo cáo Thường trực Đảng uỷ trước 16h00 ngày 28/10",
    "trang_thai": "Đang thực hiện", // Các trạng thái: "Chưa thực hiện", "Đang thực hiện", "Hoàn thành", "Quá hạn"
    "muc_do_uu_tien": "Cao", // "Bình thường", "Cao", "Khẩn"
    "lich_su_nhac_nho": [
      {
        "thoi_gian": "25/10/2026 07:30:00",
        "hinh_thuc": "zalo_1_1",
        "ket_qua": "success"
      }
    ]
  }
]
```

---

### 2. Sổ Tiêu chí & Chỉ tiêu Đa tầng (`data/so_tieu_chi.json`)

Tổ chức theo 3 tầng thời gian bám sát Nghị quyết Đại hội Đảng bộ xã lần thứ I:

```
                          SỔ TIÊU CHÍ ĐẢNG BỘ XÃ
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
   1. HÀNG NĂM                2. HÀNG QUÝ                3. HÀNG THÁNG
- Tăng trưởng (11-12%)      - Thu ngân sách quý        - Dịch vụ công trực tuyến
- Thu ngân sách (+12%)      - Sinh hoạt chi bộ thôn    - Tỷ lệ xử lý đúng hạn
- Chuẩn NTM nâng cao        - Tiến độ vốn đầu tư công  - Sinh hoạt chi bộ (ngày 03)
- Xoá nghèo (2030)          - Hạ tầng Hồ Sông Trâu     - Chuẩn hoá dữ liệu ĐV
- Kết nạp Đảng viên         - Giám sát chuyên đề UBKT  - Thu thuế tháng
```

**Cấu trúc dữ liệu mẫu:**
```json
{
  "tieu_chi_nam": [
    {
      "ma_tc": "TC-NAM-01",
      "ten_tieu_chi": "Tốc độ tăng trưởng giá trị sản xuất",
      "chi_tieu_giao": "11 - 12%",
      "thuc_hien_hien_tai": "11.5%",
      "don_vi_phu_trach": "Uỷ ban nhân dân xã",
      "danh_gia": "Đạt tiến độ"
    },
    {
      "ma_tc": "TC-NAM-02",
      "ten_tieu_chi": "Thu ngân sách nhà nước trên địa bàn",
      "chi_tieu_giao": "Tăng 12% so với năm trước",
      "thuc_hien_hien_tai": "85% kế hoạch năm",
      "don_vi_phu_trach": "Uỷ ban nhân dân xã",
      "danh_gia": "Cần đôn đốc quý 4"
    },
    {
      "ma_tc": "TC-NAM-03",
      "ten_tieu_chi": "Xây dựng Nông thôn mới",
      "chi_tieu_giao": "Đạt chuẩn Xã Nông thôn mới nâng cao",
      "thuc_hien_hien_tai": "16/19 tiêu chí",
      "don_vi_phu_trach": "BCĐ Xây dựng NTM xã",
      "danh_gia": "Tập trung tiêu chí môi trường và thu nhập"
    }
  ],
  "tieu_chi_quy": [
    {
      "ma_tc": "TC-Q4-01",
      "ky": "Quý 4/2026",
      "ten_tieu_chi": "Thu ngân sách quý 4",
      "muc_tieu": "Đạt tối thiểu 25% dự toán năm",
      "don_vi_phu_trach": "UBND xã",
      "han_chot": "31/12/2026"
    }
  ],
  "tieu_chi_thang": [
    {
      "ma_tc": "TC-T10-01",
      "ky": "Tháng 10/2026",
      "ten_tieu_chi": "Sinh hoạt Chi bộ định kỳ 08 thôn",
      "muc_tieu": "100% (8/8) Chi bộ thôn tổ chức sinh hoạt vào ngày 03 hàng tháng",
      "don_vi_phu_trach": "Ban Xây dựng Đảng",
      "han_chot": "03/10/2026"
    },
    {
      "ma_tc": "TC-T10-02",
      "ky": "Tháng 10/2026",
      "ten_tieu_chi": "Tỷ lệ hồ sơ trực tuyến toàn trình (Đề án 06)",
      "muc_tieu": "Đạt từ 85% trở lên",
      "don_vi_phu_trach": "Bộ phận Một cửa xã",
      "han_chot": "31/10/2026"
    }
  ]
}
```

---

## III. THIẾT KẾ BỘ HẸN GIỜ TỰ ĐỘNG (SCHEDULER ENGINE)

### 1. Kiến trúc kỹ thuật:
- **Module dự kiến:** `server/services/scheduler_service.py`
- **Công nghệ:** Sử dụng `AsyncIOScheduler` (từ thư viện chuẩn hoặc `APScheduler`) tích hợp trực tiếp vào vòng lặp sự kiện của máy chủ hoặc Zalo Bot Runner.
- **Không block luồng:** Mọi tác vụ quét và gửi tin chạy dưới nền (Background Tasks), không làm chậm tin nhắn chat thường ngày.

### 2. Ma trận Lịch hẹn giờ định kỳ (Schedule Matrix):

| Tần suất | Thời gian | Tác vụ thực hiện | Đối tượng nhận |
| :--- | :---: | :--- | :--- |
| **Hàng ngày** | **07h30 sáng** | Quét các nhiệm vụ có hạn hôm nay & ngày mai $\rightarrow$ Nhắc việc | Gửi tin nhắn riêng (1-1) cho từng cán bộ phụ trách |
| **Hàng ngày** | **16h30 chiều** | Quét các nhiệm vụ hết hạn trong ngày chưa báo cáo hoàn thành | Nhắn tin cảnh báo cán bộ phụ trách & báo Thường trực |
| **Thứ Sáu** | **08h00 sáng** | Đôn đốc 5 cơ quan và 8 thôn gửi Báo cáo tuần trước 11h00 | Gửi tin nhắn vào Nhóm Zalo cơ quan |
| **Thứ Sáu** | **14h00 chiều** | Tự động tổng hợp dữ liệu báo cáo tuần thành bản dự thảo sơ bộ | Báo tin cho Chánh Văn phòng Đảng uỷ |
| **Ngày mùng 1** | **08h00 sáng** | Nhắc các Chi uỷ thôn chuẩn bị sinh hoạt chi bộ ngày mùng 3 | Gửi tin nhắn cho 08 Bí thư Chi bộ thôn |
| **Ngày 25** | **08h30 sáng** | Đôn đốc gửi số liệu Báo cáo tháng của Đảng uỷ xã | Nhắn vào Nhóm chuyên môn |
| **Cuối quý** | **Tuần 11** | Rà soát chỉ tiêu quý $\rightarrow$ Cảnh báo các chỉ tiêu $< 80\%$ | Báo cáo Thường trực Đảng uỷ xã |

---

## IV. KỊCH BẢN TƯƠNG TÁC THÔNG MINH TRÊN ZALO

Khi hoàn thiện, cán bộ chỉ cần nhắn tin thoại hoặc gõ chữ trên Zalo, Bot sẽ tự động truy vấn Sổ nhiệm vụ:

1. **Cán bộ hỏi việc của mình:**
   - Cán bộ nhắn: *"Hôm nay tôi có nhiệm vụ gì cần làm?"*
   - Bot nhận diện `chat_id` $\rightarrow$ Quét `so_nhiem_vu.json` $\rightarrow$ Trả lời:
     > *"Chào đồng chí! Hôm nay 28/10 đồng chí có **01 nhiệm vụ đến hạn**:\n- Báo cáo kết quả thu thuế tháng 10 (Hạn trước 16h00).\nĐồng chí lưu ý hoàn tất nhé."*

2. **Lãnh đạo kiểm tra tiến độ chung:**
   - Bí thư / Phó Bí thư nhắn: *"Hiện tại có những việc nào bị chậm tiến độ?"*
   - Bot quét trạng thái `Quá hạn` $\rightarrow$ Trả về bảng tổng hợp:
     > *"Báo cáo đồng chí Thường trực, hiện có **02 nhiệm vụ chậm tiến độ**:\n1. UBND xã: Kế hoạch đền bù đường Bình Tiên (Quá hạn 2 ngày).\n2. Ban Xây dựng Đảng: Hồ sơ kết nạp Đảng thôn Suối Giếng (Quá hạn 1 ngày)."*

3. **Giao việc nhanh bằng tin nhắn:**
   - Lãnh đạo nhắn: *"Giao UBND xã kiểm tra việc nạo vét mương thôn Ma Trai xong trước 30/10"*
   - Bot tự động:
     - Tạo 1 bản ghi nhiệm vụ mới vào `so_nhiem_vu.json`.
     - Dự thảo một thông báo/công văn giao việc.
     - Tự động gửi tin nhắn báo cho đồng chí phụ trách UBND xã biết.

---

## V. LỘ TRÌNH TRIỂN KHAI 4 BƯỚC (DÀNH CHO LẦN THỰC HIỆN SAU)

Khi Cán bộ muốn triển khai, chỉ cần yêu cầu AI: **"Bắt đầu thực hiện Kế hoạch tại file KE_HOACH_SO_NHIEM_VU_VA_HEN_GIO.md"**, quy trình sẽ lần lượt gồm 4 bước:

* **Bước 1 (Thiết kế Kho Dữ liệu):** Tạo thư mục `data/` với 2 tệp `so_nhiem_vu.json` và `so_tieu_chi.json` cùng module `server/services/task_service.py` để CRUD (Thêm, Sửa, Xoá, Tra cứu).
* **Bước 2 (Tích hợp Tự động Bóc tách từ Văn bản):** Cập nhật `_confirm()` trong `server/chat_engine.py`: Khi Cán bộ bấm "Duyệt" Công văn giao việc hoặc Thông báo kết luận cuộc họp $\rightarrow$ Tự động trích xuất bảng phân công đẩy thẳng vào `so_nhiem_vu.json`.
* **Bước 3 (Xây dựng Bộ Hẹn Giờ Scheduler):** Tạo `server/services/scheduler_service.py` kết nối với `zalo_api.py` để quét và gửi tin nhắn tự động theo bảng ma trận lịch trình.
* **Bước 4 (Nâng cấp Giao diện Web):** Thêm Tab **"Sổ Nhiệm Vụ & Tiến Độ Chỉ Tiêu"** trên Giao diện Web `http://localhost:8000` với giao diện Kanban (Chưa làm - Đang làm - Đã xong) và biểu đồ thanh tiến độ phần trăm chỉ tiêu.

---
*Kế hoạch này đã sẵn sàng và được lưu trữ hoàn chỉnh tại thư mục gốc dự án.*
