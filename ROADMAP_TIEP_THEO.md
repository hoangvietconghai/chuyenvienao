# LỘ TRÌNH CÔNG VIỆC TIẾP THEO — CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI

> *Tệp theo dõi tiến độ xây dựng hệ thống Skills tác nghiệp thực tế trên Hệ thống Điều hành tác nghiệp (`dhtn.dcs.vn`) và chuẩn hoá kỹ năng soạn thảo văn bản.*

---

## I. CÁC HẠNG MỤC ĐÃ HOÀN THÀNH (ĐẾN 26/11/2026)

1. **Nghiên cứu quy định pháp lý & HDSD ĐHTN:**
   - Đã rà soát toàn diện `07-QC/TW`, `06-QC/VPTW`, `09-HD/VPTW`, `1980-CV/VPTW` (Hướng dẫn AI), và bộ `01–12_hdsd_*.md`.
   - Đã khảo sát thực tế trên giao diện Production `https://dhtn.dcs.vn` (đối chiếu các điểm nâng cấp Split-View 50/50, 17 nút tác vụ, nút đỏ `Chuyển văn bản`, Biểu đồ xử lý luồng ĐỎ/XANH LÁ, cảnh báo bẫy ngữ nghĩa Cột 12 `Ý kiến chuyển`, và panel `Danh sách nhiệm vụ đơn vị (X)`).
2. **Xây dựng hoàn chỉnh Skill `xu-ly-van-ban-den` (`.agents/skills/xu-ly-van-ban-den/SKILL.md`):**
   - Tích hợp 5 bước thao tác thực chiến, ma trận phân công nhân sự Văn phòng (Katơr Vế, Mai Thị Thuỷ, Lê Thị Bích Thuỷ, Hồ Thị Thuý Nhi), mẫu Morning Brief Zalo và 4 mẫu bút phê chỉ đạo thực tế.
3. **Chuẩn hoá phần "Công văn giao việc" trong Skill `cong-van` (`.agents/skills/cong-van/SKILL.md`):**
   - Khắc phục lỗi viết dài dòng và lồng ghép phần triển khai bằng Chế độ A ("3 KHÔNG") vs Chế độ B (Chỉ đạo trực tiếp).
   - Khẳng định nguyên tắc **1 Văn bản đến $\rightarrow$ 1 Công văn giao việc duy nhất**.
   - Cập nhật chuẩn tên người ký (`Nguyễn Xuân Hoàng`), mẫu thực tế (`786-CV/ĐU`, `791-CV/ĐU`) và quy chuẩn đặt tên file.

---

## II. KẾ HOẠCH CÔNG VIỆC CẦN LÀM TIẾP Ở CÁC PHIÊN SAU

### 1. Mở rộng Skill `cong-van` cho 64% các loại Công văn thực tế còn lại
Qua thống kê **553 Công văn ban hành năm 2026**, ngoài Công văn giao việc (35,8%), cần bổ sung cấu trúc & mẫu chuẩn cho 6 nhóm còn lại:
- [ ] **Nhóm 1 — Công văn Mời họp / Triệu tập Hội nghị / Điều chỉnh lịch** (90 văn bản - **16,3%**, cấu trúc 4 mục: *Thành phần, Thời gian, Địa điểm, Chuẩn bị nội dung* theo mẫu `284-CV/ĐU`).
- [ ] **Nhóm 2 — Công văn Đăng ký danh sách / Cử cán bộ / Cấp phát (chứng thư số, kinh phí) / Phúc đáp** (55 văn bản - **9,9%**, theo mẫu `593-CV/ĐU`, `678-CV/ĐU`, `305-CV/ĐU`, `282-CV/ĐU`).
- [ ] **Nhóm 3 — Công văn Báo cáo ngắn / Cung cấp thông tin / Giải trình gửi cấp trên** (35 văn bản - **6,3%**).
- [ ] **Nhóm 4 — Công văn Hiệp y / Trao đổi công tác cán bộ** (kèm nhóm Góp ý/Xin ý kiến 12,1%, theo mẫu `286-CV/ĐU`).
- [ ] **Nhóm 5 — Công văn Hướng dẫn tuyên truyền / Kỷ niệm / Phối hợp liên cơ quan** (60 văn bản - **10,8%**, theo mẫu `459-CV/ĐU`).
- [ ] **Nhóm 6 — Công văn Chấn chỉnh kỷ luật kỷ cương / Công tác Đảng viên, Khen thưởng** (theo mẫu `661-CV/ĐU`).

### 2. Xây dựng Skill "Xử lý Văn bản đi & Tạo dự thảo trình ký trên ĐHTN"
- [ ] Khảo sát thực tế bằng trình duyệt phân hệ **Văn bản đi** (`Dự thảo của tôi`, `Phiếu trình của tôi`, nút `[Tạo dự thảo]` liên kết từ văn bản đến).
- [ ] Xây dựng `SKILL.md` hướng dẫn AI tự động mở form tạo dự thảo trên `dhtn.dcs.vn`, điền thông tin trích yếu, thể loại, người ký, nơi nhận, đính kèm file `.docx` đã xuất và **dừng chờ cán bộ bấm nút `Trình ký`** (tuân thủ Human-in-the-Loop).

### 3. Thực hành chạy thử nghiệm thực tế chuỗi Xử lý Văn bản đến
- [ ] Chạy thử kịch bản quét danh sách `Văn bản chờ xử lý`, đọc PDF, đối soát `Biểu đồ xử lý` + `Danh sách nhiệm vụ đơn vị`, xuất tin nhắn nhắc việc Zalo và soạn sẵn 01 Công văn giao việc mẫu để đồng chí Phó CVP nghiệm thu.
