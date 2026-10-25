# HỆ THỐNG TRỢ LÝ AI THAM MƯU TỔNG HỢP & SOẠN THẢO VĂN BẢN ĐẢNG UỶ XÃ CÔNG HẢI
*(Chuẩn thể thức Hướng dẫn số 05-HD/VPTW năm 2026 của Văn phòng Trung ương Đảng & Quy chế làm việc Đảng bộ xã)*

Hệ thống được thiết kế theo **Mô hình Hạt nhân & Kỹ năng Chuyên sâu Đa tầng (Core & Multi-Tier Advisory Skills)** trên nền tảng **Google Antigravity 2.0**, đóng vai trò là **Trợ lý Tham mưu Tổng hợp Toàn diện** cho Thường trực Đảng uỷ, Ban Thường vụ Đảng uỷ và Ban Chấp hành Đảng bộ xã Công Hải, tỉnh Khánh Hoà (trực thuộc trực tiếp Tỉnh uỷ Khánh Hoà theo mô hình chính quyền địa phương 02 cấp từ 01/7/2025).

---

## 📂 SƠ ĐỒ CẤU TRÚC THƯ MỤC HỆ THỐNG

```text
e:\Viet Design\Chuyên viên ảo\
│
├── 📜 AGENTS.md                             # QUY TẮC VẬN HÀNH MẶC ĐỊNH (auto-load khi mở workspace)
├── 📖 SETUP.md                              # HƯỚNG DẪN CÀI ĐẶT & TRIỂN KHAI TRÊN MÁY TÍNH MỚI
├── ⚙️ setup.bat / setup.ps1                 # SCRIPT TỰ ĐỘNG THIẾT LẬP MÔI TRƯỜNG & THƯ MỤC
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
│       └── tham-dinh-van-ban/SKILL.md       # Kỹ năng Thẩm định văn bản & Đối soát tiếp thu
│
├── ⚙️ scripts/                              # BỘ CÔNG CỤ TỰ ĐỘNG HÓA VĂN THƯ & KIỂM THỬ
│   ├── __init__.py                          # Package initialization
│   ├── export_docx.py                       # Engine sinh tệp Word (.docx) chuẩn hóa tự động HD 05
│   ├── doc_reader.py                        # Trích xuất và đọc văn bản Office (.docx, .doc, .pdf)
│   ├── build_indicator_registry.py          # Xây dựng sổ đăng ký chỉ tiêu nhiệm kỳ
│   ├── build_plan_registry.py               # Xây dựng sổ kế hoạch chỉ đạo
│   ├── generate_cong_van_lay_y_kien.py      # Sinh Công văn lấy ý kiến BTV kèm Phiếu xin ý kiến
│   ├── test_doc_reader.py                   # Bộ kiểm thử bộ đọc văn bản
│   ├── test_system_integration.py           # Bộ kiểm thử tích hợp hệ thống
│   └── test_workflow.py                     # Kịch bản kiểm thử tích hợp (Integration Tests) tự động
│
├── 📥 van_ban_den/                          # KHO TIẾP NHẬN TÀI LIỆU ĐẦU VÀO
│   └── 2026/                                # Văn bản chỉ đạo cấp trên (Tỉnh uỷ, Trung ương) theo năm
│
├── 📤 van_ban_du_thao/                      # KHO LƯU TRỮ VĂN BẢN SOẠN THẢO ĐẦU RA
│   └── 2026/                                # Quản lý theo năm công tác
│       ├── Cong_van/                        # Lưu trữ toàn bộ Công văn đi (-CV/ĐU)
│       ├── Ke_hoach/                        # Lưu trữ Kế hoạch (-KH/ĐU)
│       ├── Chuong_trinh/                    # Lưu trữ Chương trình hành động, CTr công tác (-CTr/ĐU)
│       ├── Nghi_quyet/                      # Lưu trữ Nghị quyết chuyên đề, Nghị quyết năm (-NQ/ĐU)
│       ├── Quyet_dinh/                      # Lưu trữ Quyết định cán bộ, kết nạp đảng viên (-QĐ/ĐU)
│       ├── Chi_thi/                         # Lưu trữ Chỉ thị công tác (-CT/ĐU)
│       ├── Ket_luan/                        # Lưu trữ Kết luận Hội nghị Ban Chấp hành (-KL/ĐU)
│       ├── Thong_bao/                       # Lưu trữ Thông báo Kết luận họp Thường trực, BTV (-TB/ĐU)
│       ├── Bao_cao/                         # Lưu trữ Báo cáo định kỳ, chuyên đề gửi Tỉnh uỷ (-BC/ĐU)
│       └── To_trinh/                        # Lưu trữ Tờ trình xin chủ trương, nhân sự (-TTr/ĐU, -TTr/...)
│
└── 📚 references/                           # TÀI LIỆU TRA CỨU & QUY PHẠM ĐỊA PHƯƠNG
    ├── Cam_nang_Nghiep_vu_Tham_muu_Cap_uy.md # Cẩm nang tra cứu thẩm quyền, SLA, phân vai 5 cơ quan
    ├── Mẫu văn bản thông dụng/              # Kho mẫu thực tế (-KL/ĐU, -TB/ĐU, họp BTV, họp Thường trực...)
    ├── Thông tin thông dụng/                # Quy chế làm việc 01-QC/ĐU và Quy định chức năng nhiệm vụ
    └── tong_quan_xa_cong_hai.md             # Thông tin tổng quan địa bàn xã Công Hải
```

---

## 🎯 CÁC NGUYÊN TẮC NGHIỆP VỤ BẮT BUỘC TUÂN THỦ

1. **Mô hình Chính quyền 3 cấp (TW $\Rightarrow$ Tỉnh $\Rightarrow$ Xã):**
   * Vận hành từ ngày **01/7/2025**, hoàn toàn không còn cấp huyện.
   * Cấp trên trực tiếp của xã là **Tỉnh uỷ Khánh Hoà** (Ban Chấp hành, Ban Thường vụ, Thường trực Tỉnh uỷ) và **UBND tỉnh Khánh Hoà**.
   * Loại bỏ triệt để các thông tin, địa danh, tên đơn vị cấp huyện cũ khi tra cứu hoặc viện dẫn.
2. **Nguyên tắc "Thẩm định 2 Tầng" của Văn phòng Đảng uỷ:**
   * **Tầng 1 (Kỹ thuật văn bản $\rightarrow$ Trực tiếp sửa):** Thể thức Hướng dẫn 05, thẩm quyền, căn cứ, chính tả khối Đảng (`uỷ`, `oà`, `uý`). Bắt buộc xuất Báo cáo Thẩm định kèm Bảng kê các điểm đã sửa (Change Log).
   * **Tầng 2 (Nội dung & Số liệu $\rightarrow$ Không tự ý sửa):** Số liệu kinh tế, ngân sách, chỉ tiêu kết nạp đảng viên chỉ được ghi chú vào mục "Ý kiến lưu ý / Khuyến nghị" để báo cáo lãnh đạo làm việc lại với đơn vị chuyên môn.
3. **Chu trình 4 Luồng Tham mưu & Đối soát Tiếp thu:**
   * Luồng 1 (Nghị quyết BCH): Chuyên môn soạn $\rightarrow$ VPĐU thẩm định 1 $\rightarrow$ Họp Thường trực $\rightarrow$ TBKL Thường trực $\rightarrow$ Sửa $\rightarrow$ VPĐU đối soát $\rightarrow$ Họp BTV $\rightarrow$ TBKL BTV $\rightarrow$ Sửa $\rightarrow$ Hội nghị BCH $\rightarrow$ Kết luận BCH $\rightarrow$ VPĐU thẩm định cuối $\rightarrow$ Trình Bí thư ký.
   * Luồng 2 (Nghị quyết BTV): Rút gọn dừng ở cấp Ban Thường vụ.
   * Luồng 3 (Kế hoạch/CTHĐ Tỉnh uỷ): Thường trực duyệt $\rightarrow$ Lấy ý kiến văn bản Ủy viên BTV $\rightarrow$ Tổng hợp tiếp thu $\rightarrow$ Trình ký.
   * Luồng 4 (Họp Tuần Thường trực): Họp nghe báo cáo $\rightarrow$ Ban hành Thông báo Kết luận giao việc trong 24h.
4. **Kỹ thuật Bảng ẩn 2 Cột (Invisible Grid) & Khổ giấy A4:**
   * Header và Footer luôn đặt trong bảng 1 hàng 2 cột ẩn toàn bộ viền chống xô lệch.
   * Lề trang: Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm.
   * Đoạn văn: Căn đều 2 bên (Justified), thụt đầu dòng 1cm, Giãn đoạn Before 6pt / After 6pt, Giãn dòng cố định Exactly 18pt.
5. **Định dạng Ngày tháng trong Thân bài:**
   * Các mốc thời gian viết theo định dạng số `dd/mm/yyyy` (Ví dụ: **trước ngày 10/10/2026**), không ghi chữ "ngày... tháng... năm...".
6. **Cơ chế An toàn Human-in-the-Loop:**
   * Tuyệt đối không đụng mật khẩu (sử dụng Persistent Chrome Profile).
   * Mọi thao tác Ban hành, Phát hành, Ký số trên phần mềm bắt buộc phải dừng lại chờ Cán bộ thẩm định và tự tay bấm nút.
