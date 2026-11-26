---
name: xu-ly-van-ban-den
description: >-
  Kỹ năng toàn diện hướng dẫn Chuyên viên ảo thao tác trực tiếp trên Hệ thống
  Thông tin Điều hành tác nghiệp của các cơ quan Đảng (dhtn.dcs.vn) để xử lý văn
  bản đến tại Đảng uỷ xã Công Hải. Hướng dẫn chi tiết: nhận diện URL, cấu trúc DOM
  bảng danh mục; quét 13 cột dữ liệu văn bản chờ xử lý; bóc tách tệp PDF toàn văn;
  giải mã Biểu đồ xử lý (phân định luồng ĐỎ xử lý chính vs luồng XANH LÁ phối
  hợp); kiểm tra mục "Danh sách nhiệm vụ đơn vị" trong chi tiết văn bản để xác
  định văn bản đã giao việc chưa; thao tác tự động hoá form pop-up "Chuyển văn bản"
  giao việc cho chuyên viên (Katơr Vế, Mai Thị Thuỷ, Lê Thị Bích Thuỷ, Hồ Thị
  Thuý Nhi); tự động kích hoạt soạn thảo Công văn giao việc (-CV/ĐU) gửi khối UBND/MTTQ
  xã; định dạng bản tin Zalo cảnh báo hạn xử lý hằng ngày gửi Phó Chánh Văn phòng;
  tuân thủ nghiêm ngặt nguyên tắc Human-in-the-Loop và bảo vệ an toàn dữ liệu Đảng.
---

# KỸ NĂNG: XỬ LÝ VĂN BẢN ĐẾN TRÊN HỆ THỐNG ĐIỀU HÀNH TÁC NGHIỆP CÁC CƠ QUAN ĐẢNG

> **Skill Name:** `xu-ly-van-ban-den`  
> **Kế thừa bắt buộc:** [quy-chuan-nen-tang](../quy-chuan-nen-tang/SKILL.md)  
> **Hệ thống mục tiêu:** Hệ thống Thông tin Điều hành tác nghiệp các cơ quan Đảng (`https://dhtn.dcs.vn`)  
> **Đơn vị áp dụng:** Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà  
> **Chủ tài khoản thụ hưởng:** Đồng chí Ngô Hoàng Việt - Phó Chánh Văn phòng Đảng uỷ (kiêm Quản trị viên hệ thống cấp xã)

---

## PHẦN I. CĂN CỨ PHÁP LÝ, NGUYÊN TẮC BẢO MẬT & MÔ HÌNH VẬN HÀNH

### 1. Căn cứ pháp lý nền tảng
1. **Quy chế số 07-QC/TW** ngày 31/10/2025 của Ban Bí thư về tổ chức, quản lý, sử dụng và bảo vệ hệ thống mạng máy tính của Đảng.
2. **Quy chế số 06-QC/VPTW** ngày 26/4/2025 của Văn phòng Trung ương Đảng về quản lý, sử dụng phần mềm Hệ thống thông tin điều hành tác nghiệp trong các cơ quan đảng.
3. **Hướng dẫn số 09-HD/VPTW** ngày 03/6/2026 của Văn phòng Trung ương Đảng về xử lý văn bản điện tử trên hệ thống thông tin điều hành tác nghiệp trong các cơ quan đảng.
4. **Công văn số 1980-CV/VPTW** ngày 26/11/2025 của Văn phòng Trung ương Đảng kèm Hướng dẫn khai thác sử dụng trí tuệ nhân tạo (AI) cho cán bộ, đảng viên trong các cơ quan đảng.
5. **Quy chuẩn thể thức văn bản Đảng:** Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.

### 2. Ba nguyên tắc bất biến khi AI tương tác với Hệ thống thật
- **Nguyên tắc môi trường mạng (Internet vs Intranet):** Trên môi trường Internet (`dhtn.dcs.vn`), hệ thống chỉ xử lý văn bản thông thường, hoàn toàn **KHÔNG CÓ VĂN BẢN MẬT**. Văn bản có độ mật ("Mật", "Tối mật") chỉ được hiển thị và xử lý khi người dùng truy cập từ mạng thông tin diện rộng chuyên dùng của Đảng có gắn thiết bị mã hoá của Ban Cơ yếu Chính phủ.
- **Nguyên tắc "Human-in-the-Loop" (Con người quyết định):** Chuyên viên ảo đóng vai trò trợ lý kỹ thuật chuẩn bị dữ liệu, đọc trích xuất, phát hiện hạn xử lý, gợi ý bút phê và tự động điền form. AI **TUYỆT ĐỐI KHÔNG** tự ý bấm các nút xác nhận có tính pháp lý như: nút đỏ `[⏩ Chuyển văn bản]`, nút `[💾 Ghi lại]` ý kiến chỉ đạo, nút `[Hoàn thành]` hoặc `[Trả lại]`. Mọi thao tác gửi đi phải dừng lại để cán bộ kiểm tra và tự tay bấm nút.
- **Tuyệt đối không lưu mật khẩu:** AI hoạt động trên phiên làm việc (session) đã được cán bộ đăng nhập sẵn trên trình duyệt. Tuyệt đối không yêu cầu, không lưu trữ mã PIN, mật khẩu tài khoản hoặc thiết bị lưu khoá bí mật.
- **Nguyên tắc Nhịp độ Thao tác Tự nhiên (Human-Paced Throttling — Chống quá tải & Giám sát ANM):** Theo Quy chế 07-QC/TW, hệ thống mạng của Đảng có giám sát lưu lượng truy cập tập trung. AI **TUYỆT ĐỐI KHÔNG** dùng công cụ bắn request hàng loạt, không chạy đa luồng song song, không thao tác quét quá nhanh. Khi cần đọc nhiều văn bản, bắt buộc chạy tuần tự **1 luồng duy nhất** với khoảng nghỉ tự nhiên từ **4–7 giây giữa mỗi văn bản** (tương đương nhịp đọc của con người), hoặc ưu tiên dùng tính năng `Xuất Excel` tích hợp sẵn của phần mềm.

### 3. Sơ đồ nhân sự & Luồng phân phối tại Văn phòng Đảng uỷ xã Công Hải
- **Đầu mối tiếp nhận ban đầu:** Đồng chí Hồ Thị Thuý Nhi (Văn thư) tiếp nhận văn bản đến điện tử, vào sổ, gắn dấu đến điện tử $\rightarrow$ Chuyển cho Chánh Văn phòng (đồng chí Nguyễn Đăng Quang) hoặc chuyển trực tiếp cho Phó Chánh Văn phòng (đồng chí Ngô Hoàng Việt).
- **Đầu mối phân phối & lãnh đạo:**
  - Đồng chí Nguyễn Đăng Quang (Chánh Văn phòng) và đồng chí Ngô Hoàng Việt (Phó Chánh Văn phòng).
  - Phân công giao việc cho các chuyên viên Văn phòng Đảng uỷ:
    + **Katơr Vế:** Theo dõi, tham mưu mảng **Xây dựng Đảng, Mặt trận đoàn thể, kiểm tra giám sát, công tác chi bộ** (đầu mối theo dõi/tham mưu giao việc cho *Ban Xây dựng Đảng, Uỷ ban MTTQ Việt Nam xã, Uỷ ban Kiểm tra Đảng uỷ xã*).
    + **Mai Thị Thuỷ:** Theo dõi, tham mưu mảng **Kinh tế - Xã hội, nội chính, phòng chống tham nhũng, lãng phí, tiêu cực** (đầu mối theo dõi/tham mưu giao việc cho *UBND xã, Uỷ ban Kiểm tra Đảng uỷ xã*).
    + **Lê Thị Bích Thuỷ:** Theo dõi, tham mưu mảng **Tài chính Đảng, kế toán, chuyển đổi số, công nghệ thông tin**.
    + **Hồ Thị Thuý Nhi:** Văn thư cơ quan (tiếp nhận văn bản đến, vào sổ, cấp số phát hành văn bản đi, lưu trữ).
  - Phân công giao việc cho các cơ quan chuyên trách tham mưu: **Ban Xây dựng Đảng xã**, **Cơ quan Uỷ ban Kiểm tra Đảng uỷ xã**.
- **Đặc thù khối Chính quyền (UBND xã) và Mặt trận (MTTQ xã):** Hệ thống phần mềm ĐHTN của Đảng **không tạo nhiệm vụ trực tiếp** sang khối chính quyền và mặt trận. Do đó, đối với các chỉ đạo của cấp trên cần UBND xã hoặc Mặt trận tổ chức thực hiện, Văn phòng Đảng uỷ bắt buộc phải **ban hành Công văn giao việc (-CV/ĐU)** của Đảng uỷ xã gửi sang.

---

## PHẦN II. ĐẶC TẢ GIAO DIỆN HỆ THỐNG ĐIỀU HÀNH TÁC NGHIỆP (`dhtn.dcs.vn`)

```mermaid
flowchart TD
    Dashboard["Trang chủ (Dashboard)<br/>URL: /app-view/view/home.html"] --> ListDoc["Danh sách Văn bản chờ xử lý<br/>(Tab con: 'Văn bản chờ xử lý')"]
    ListDoc --> DetailModal["Cửa sổ Thông tin chi tiết văn bản<br/>(Modal chia làm 2 nửa)"]
    DetailModal --> FlowchartModal["Modal Biểu đồ xử lý<br/>(Luồng ĐỎ: Xử lý chính | Luồng XANH LÁ: Phối hợp)"]
    DetailModal --> TaskList["Panel 'Danh sách nhiệm vụ đơn vị (X)'<br/>((0) = Chưa giao | (>0) = Đã giao nhiệm vụ)"]
    DetailModal --> TransferPopup["Pop-up 'Chuyển văn bản'<br/>(Giao việc cho Chuyên viên / Đơn vị)"]
    DetailModal --> DirectivePopup["Pop-up 'Nhập ý kiến chỉ đạo'<br/>(Ghi bút phê Lãnh đạo)"]
```

### 1. Bảng danh sách "Văn bản chờ xử lý" (13 Cột thông tin chuẩn)
Truy cập qua URL chính: `https://dhtn.dcs.vn/app-view/theme/admin-ex/pages/main.zul` (hoặc click widget `Chờ xử lý` trên Dashboard):
- **Cột 1 (Checkbox):** Chọn một hoặc nhiều văn bản phục vụ xử lý hàng loạt.
- **Cột 2 (STT):** Số thứ tự hiển thị (phân trang 10, 20... bản ghi/trang).
- **Cột 3 (Thao tác):** Cụm 8 icon hành động nhanh monochrome phẳng xếp thành 2 hàng:
  + Hàng trên: *[Chuyển văn bản]*, *[Xem chi tiết/xử lý]*, *[Trả lại văn bản]*, *[Chuyển tiếp]*.
  + Hàng dưới: *[Tạo tờ trình]*, *[Nhập ý kiến chỉ đạo/góp ý]*, *[Xem lịch sử luân chuyển]*, *[Chia sẻ/Gán tag]*.
- **Cột 4 (Đơn vị ban hành):** Tên cơ quan gửi (Ví dụ: *UBND xã Công Hải*, *Văn phòng Tỉnh uỷ Khánh Hoà*, *Ban Tuyên giáo Tỉnh uỷ*...). Có ô lọc text trực tiếp trên đầu cột.
- **Cột 5 (Số, ký hiệu):** Số hiệu văn bản gốc (Hyperlink mở chi tiết, kèm ô lọc mã văn bản).
- **Cột 6 (Trích yếu nội dung văn bản):** Nội dung trích yếu, kèm Badge huy hiệu nổi bật: `[CT]` (Chủ trì xử lý chính) hoặc `[PH]` (Phối hợp xử lý). Có ô lọc text trực tiếp.
- **Cột 7 (Thể loại văn bản):** Quyết định, Kế hoạch, Báo cáo, Thông báo, Công văn, Tờ trình... (Kèm dropdown lọc).
- **Cột 8 (Độ khẩn):** Thường, Khẩn, Thượng khẩn, Hoả tốc (Kèm dropdown lọc).
- **Cột 9 (Độ mật):** Thường (trên môi trường Internet luôn là Thường, kèm dropdown lọc).
- **Cột 10 (Trạng thái văn bản):** Chờ xử lý (Kèm dropdown lọc).
- **Cột 11 (Thời gian nhận):** Ngày giờ nhận văn bản (dd/mm/yyyy), kèm Datepicker 📅 chọn khoảng ngày.
- **Cột 12 (Ý kiến chuyển):** Bút phê chỉ đạo luân chuyển dùng chung cho cả một đợt chuyển nhiều người nhận (Ví dụ: *"Trình TTĐU biết; VP cập nhật, lưu hồ sơ"*, *"Cập nhật, tham mưu thực hiện' Lưu HS"*). **⚠️ CẢNH BÁO NGHIỆP VỤ QUAN TRỌNG:** Khi người chuyển chọn nhiều người nhận cùng lúc (ví dụ: Bí thư nhận để biết, Chuyên viên xử lý chính, Phó CVP phối hợp) thì Cột 12 đều hiển thị giống hệt nhau ở tài khoản tất cả mọi người. Vì vậy, **TUYỆT ĐỐI KHÔNG đọc Cột 12 rồi tự suy đoán vai trò của đồng chí Ngô Hoàng Việt**, mà bắt buộc phải kiểm tra đối chiếu trong `Biểu đồ xử lý` (Bước 2).
- **Cột 13 (File văn bản):** Tên file PDF đã đóng dấu điện tử (`*_dadongdau.pdf`), kèm icon tải xuống  và link xem thêm.

### 2. Cửa sổ Modal "Thông tin chi tiết văn bản" (Kiến trúc Split-View 50/50 nâng cấp)
Hệ thống nâng cấp thiết kế chia thành 2 nửa màn hình song song:
- **Nửa bên phải (PDF.js Viewer nhúng toàn diện):**
  - Hiển thị trực tiếp toàn văn văn bản PDF có chữ ký số và con dấu đỏ. Cho phép AI/cán bộ đọc ngay văn bản mà không cần mở tab mới, hỗ trợ đầy đủ công cụ zoom, in, tải về.
- **Nửa bên trái (Thông tin & Hệ thống Accordion Panels gập/mở):**
  1. *Accordion Thông tin chi tiết:* Trích yếu, Số ký hiệu, Người ký, Ngày ban hành, Thời gian nhận, Hạn xử lý, Độ khẩn, Độ mật, Loại bản (Bản gốc/Bản sao), Mã định danh (`A32.65-...`), Thể loại, Đơn vị ban hành.
  2. *Accordion File đính kèm (Phân hoá 3 lớp dữ liệu):*
     - File đính kèm chính: File PDF scan gốc đã đóng dấu (`*_dadongdau.pdf`).
     - File biểu mẫu: File Word đính kèm sẵn mẫu dự thảo (`*.docx`).
     - Tài liệu liên quan: File Word/PDF chứa các nghị quyết, kế hoạch căn cứ (`*.docx`).
  3. *Accordion Danh sách đã gửi đi:* Gồm 4 tab con: `[Đơn vị]`, `[Cá nhân]`, `[Nhóm]`, `[Đơn vị liên thông]`.
  4. *Accordion Danh sách người gửi đến:* Thể hiện rõ ai chuyển đến vào ngày giờ nào kèm bút phê.
  5. **`Accordion Danh sách nhiệm vụ đơn vị (X)`:** **Mục cốt lõi xác định văn bản đã giao việc chưa**.
  6. *Accordion Thuộc hồ sơ:* Danh mục hồ sơ công việc lưu trữ văn bản.
  7. *Accordion Sao gửi văn bản (X).*
  8. *Accordion Lịch sử chỉnh sửa văn bản (X).*
  9. *Accordion Dự thảo (X):* **Điểm mới nâng cấp** cho phép quản lý trực tiếp các văn bản đi dự thảo được tạo ra để phản hồi văn bản đến này.
- **Thanh tác vụ cố định dưới đáy (Action Toolbar 17 nút):**
  - Hàng trên (12 nút phụ trợ & lưu trữ): `[✕ Đóng]`, `[🏷 Gán tag văn bản]`, `[⬆ Công khai văn bản]`, `[📅 Tạo lịch họp]`, `[👤+ Lưu tài liệu cá nhân]`, `[📁 Lưu/Tạo hồ sơ]`, `[📝 Ghi chú]`, `[💼 Tạo nhiệm vụ đơn vị]`, `[✉ Chia sẻ]`, `[👁 Xem luân chuyển]`, `[☊ Biểu đồ xử lý]`, `[↩ Trả lại]`.
  - Hàng dưới (5 nút nghiệp vụ trọng tâm):
    1. `[✔ Hoàn thành]` (Nút trắng viền xám).
    2. `[⚙ Nhập ý kiến chỉ đạo]` (Nút trắng viền xám).
    3. `[📋 Tạo phiếu trình]` (Nút trắng viền xám).
    4. `[📝 Tạo dự thảo]` (Nút trắng viền xám - **Nút mới nâng cấp** giúp nhảy nhanh sang soạn thảo văn bản đi trả lời).
    5. `[➤ Chuyển văn bản]` (**NÚT MÀU ĐỎ THẮM NỔI BẬT NHẤT** - Nút hành động chính).

---

## PHẦN III. QUY TRÌNH 5 BƯỚC THAO TÁC CỦA CHUYÊN VIÊN ẢO (ACTIONABLE PLAYBOOK)

Khi được kích hoạt để xử lý văn bản đến, AI Agent thực hiện tuần tự và chính xác theo 5 bước sau:

```mermaid
flowchart TD
    Step1["BƯỚC 1: Quét danh sách Văn bản chờ xử lý<br/>(Thu thập 13 cột dữ liệu, lọc quá hạn & tải PDF)"] --> Step2["BƯỚC 2: Giải mã Biểu đồ xử lý<br/>(Đường ĐỎ: Chủ trì | Đường XANH: Phối hợp)"]
    Step2 --> Step3["BƯỚC 3: Kiểm tra 'Danh sách nhiệm vụ đơn vị'<br/>((0) -> Chưa giao việc | (>0) -> Đã giao việc)"]
    Step3 --> Step4{"BƯỚC 4: Ra quyết định Phân luồng"}
    
    Step4 -->|"Giao việc Chuyên viên VP"| Step4A["Điền Pop-up 'Chuyển văn bản'<br/>(Bút phê + Deadline + Tích chọn cán bộ) -> DỪNG CHỜ DUYỆT"]
    Step4 -->|"Giao việc khối UBND / MTTQ"| Step4B["Kích hoạt Skill cong-van<br/>Soạn thảo CV giao việc (-CV/ĐU) gửi UBND"]
    Step4 -->|"Phối hợp / Theo dõi"| Step4C["Lập lịch theo dõi tiến độ chuyên viên chủ trì"]
    
    Step4A --> Step5["BƯỚC 5: Tổng hợp Morning Brief qua Zalo<br/>Gửi báo cáo ngắn gọn cho Phó Chánh Văn phòng"]
    Step4B --> Step5
    Step4C --> Step5
```

### Bước 1: Quét danh sách "Văn bản chờ xử lý" & Thu thập dữ liệu
1. **Truy cập:** Mở tab `Văn bản chờ xử lý` (từ Dashboard click widget `Chờ xử lý` hoặc Menu Sidebar `Văn bản đến >> Văn bản chờ xử lý`).
2. **Thu thập dữ liệu từng dòng:**
   - Đọc Số ký hiệu (Cột 5), Đơn vị ban hành (Cột 4), Trích yếu (Cột 6), Thời gian nhận (Cột 11), Ý kiến chuyển (Cột 12).
   - Kiểm tra trạng thái màu sắc: Nếu dòng chữ đỏ là `Văn bản quá hạn` (Ưu tiên P0); nếu chữ đen in đậm là `Văn bản chưa đọc`; nếu chữ xám là `Văn bản đã đọc`.
3. **Tải file đính kèm:** Click icon download tại Cột 13 (`File văn bản`) hoặc click mở chi tiết văn bản để đọc tệp PDF nhúng ở nửa màn hình bên phải.

### Bước 2: Giải mã "Biểu đồ xử lý" (Xác định chính xác vai trò từng người nhận)
> **Nguyên tắc đối soát chéo:** Vì Cột 12 (`Ý kiến chuyển`) là chuỗi text dùng chung cho tất cả người nhận trong cùng một đợt chuyển (ví dụ cùng ghi *"Trình TTĐU biết; VP cập nhật, lưu hồ sơ"* cho cả Bí thư, Phó Bí thư và Phó CVP), AI **BẮT BUỘC** phải mở `Biểu đồ xử lý` để biết đích xác người chuyển muốn đồng chí Ngô Hoàng Việt làm gì.

1. **Thao tác:** Click icon `Biểu đồ xử lý` tại Cột 3 (hoặc click nút `Biểu đồ xử lý` tại thanh công cụ dưới đáy cửa sổ chi tiết).
2. **Kiểm tra 2 chế độ hiển thị trong Biểu đồ xử lý:**
   - **Tab `Danh sách` (Ưu tiên cao nhất để đọc chính xác):** Bấm tab `Danh sách` ở góc trên bên trái modal để xem bảng *Danh sách quá trình xử lý*. Lọc theo dòng có `Người nhận = Ngô Hoàng Việt` và đọc cột **`Loại xử lý`**:
     + Nếu là **`Xử lý chính`** (nền đỏ): Đồng chí là người chủ trì trực tiếp thực hiện phần việc giao cho Văn phòng/cá nhân.
     + Nếu là **`Phối hợp`** (nền xanh lá): Đồng chí là người phối hợp hoặc Lãnh đạo theo dõi, giám sát chuyên viên chủ trì (xem ai ở dòng `Xử lý chính` cùng đợt chuyển).
     + Nếu là **`Nhận để biết`** (nền xám tím): Chỉ đọc nắm thông tin, không phải tham mưu giải quyết.
   - **Tab `Biểu đồ` (Xem trực quan đường nối):**
     + **🔴 Đường nối MÀU ĐỎ = XỬ LÝ CHÍNH**
     + **🟢 Đường nối MÀU XANH LÁ = PHỐI HỢP**
     + **⚫ Đường nối MÀU ĐEN = NHẬN ĐỂ BIẾT**
     + Node có **biểu tượng ngôi sao vàng** là vị trí của tài khoản đang đăng nhập (`Ngô Hoàng Việt`).
3. **Đóng modal:** Bấm nút `[✕]` để quay lại màn hình chi tiết/danh sách an toàn.

### Bước 3: Kiểm tra panel "Danh sách nhiệm vụ đơn vị" trong văn bản đến
1. **Thao tác:** Trong cửa sổ *Thông tin chi tiết văn bản*, cuộn chuột ở khung bên trái xuống dưới mục *Danh sách trình duyệt* để tìm tiêu đề **`Danh sách nhiệm vụ đơn vị (X)`**.
2. **Đánh giá trạng thái:**
   - **Trường hợp (X) = 0 (`Danh sách nhiệm vụ đơn vị (0)`):**
     - Văn bản này **CHƯA ĐƯỢC GIAO NHIỆM VỤ**.
     - AI đánh giá nội dung: Nếu văn bản chứa nhiệm vụ cần triển khai $\rightarrow$ Đưa vào diện đề xuất Lãnh đạo giao việc hoặc tạo nhiệm vụ mới.
   - **Trường hợp (X) > 0 (`Danh sách nhiệm vụ đơn vị (>0)`):**
     - Văn bản này **ĐÃ ĐƯỢC GIAO NHIỆM VỤ THÀNH CÔNG**.
     - AI đọc 7 cột trong bảng: `Tên nhiệm vụ`, `Đơn vị chủ trì`, `Ngày bắt đầu`, `Ngày hoàn thành`, `Kết quả thực hiện`, `Trạng thái`.
     - Tự động trích xuất deadline hoàn thành để đưa vào danh mục theo dõi tiến độ.

### Bước 4: Thao tác tự động hoá Pop-up "Chuyển văn bản" (Giao việc linh hoạt)
Khi đồng chí Phó Chánh Văn phòng yêu cầu chuyển giao văn bản cho chuyên viên hoặc đơn vị:
1. **Mở Pop-up:** Click nút đỏ `[➤ Chuyển văn bản]` ở góc dưới cùng bên phải cửa sổ chi tiết.
2. **Điền thông tin linh hoạt theo ngữ cảnh thực tế:**
   - **Ô `Ý kiến chuyển (2000)`:** AI đọc toàn văn văn bản đến, nắm bắt yêu cầu cốt lõi và **linh hoạt** soạn bút phê chỉ đạo phù hợp với từng tình huống thực tế (không áp đặt khuôn mẫu cứng). Có thể tham khảo cấu trúc ngắn gọn:
     `Giao đ/c [Tên chuyên viên] chủ trì nghiên cứu, tham mưu [hướng xử lý phù hợp với nội dung văn bản]; báo cáo lãnh đạo VP trước ngày [dd/mm/yyyy].`
   - **Ô `Hạn xử lý`:** Chọn ngày deadline qua datepicker phù hợp với độ khẩn và thời hạn quy định trong văn bản gốc.
   - **Mục `Danh sách cá nhân`:** Dựa trên bản đồ lĩnh vực phụ trách tham khảo (có thể điều chỉnh linh hoạt theo chỉ đạo thực tế của đồng chí Phó CVP):
     - Đ/c **Katơr Vế**: Thường theo dõi mảng Xây dựng Đảng, Mặt trận đoàn thể, kiểm tra giám sát, công tác chi bộ (*Ban Xây dựng Đảng, Uỷ ban MTTQ Việt Nam xã, UBKT Đảng uỷ xã*).
     - Đ/c **Mai Thị Thuỷ**: Thường theo dõi mảng Kinh tế - Xã hội, nội chính, phòng chống tham nhũng, lãng phí, tiêu cực (*UBND xã, UBKT Đảng uỷ xã*).
     - Đ/c **Lê Thị Bích Thuỷ**: Thường theo dõi mảng Tài chính Đảng, kế toán, chuyển đổi số, công nghệ thông tin.
     - Đ/c **Hồ Thị Thuý Nhi**: Văn thư, lưu trữ, tiếp nhận và phát hành văn bản.
   - **Tùy chọn `☑️ Gửi tin nhắn thông báo`:** Luôn giữ trạng thái tích chọn để hệ thống gửi thông báo tới điện thoại cán bộ.
3. **QUY TẮC AN TOÀN HUMAN-IN-THE-LOOP (DỪNG CHỜ):**
   - AI điền xong toàn bộ form và **DỪNG LẠI NGAY LẬP TỨC**.
   - Báo cáo đồng chí Phó CVP qua khung chat:
     *"Đã nạp sẵn ý kiến chuyển giao việc cho đ/c [Tên chuyên viên] với hạn chót [dd/mm/yyyy]. Kính mời đồng chí kiểm tra trên màn hình và tự tay bấm nút đỏ [Chuyển văn bản] để phê duyệt."*
   - Tuyệt đối không tự kích hoạt sự kiện click của nút đỏ `Chuyển văn bản`.

### Bước 5: Kích hoạt chuyển giao sang Skill Soạn thảo Công văn giao việc (`-CV/ĐU`)
> **Nguyên tắc bất biến (1 Văn bản đến $\rightarrow$ 1 Công văn giao việc duy nhất):** Một văn bản chỉ đạo của cấp trên (Tỉnh uỷ, các Ban Đảng tỉnh...) khi cần cụ thể hoá bằng văn bản giao việc thì chỉ sinh ra **DUY NHẤT 01 Công văn giao việc (`-CV/ĐU`)** của Thường trực/Ban Thường vụ Đảng uỷ, tuyệt đối không tách lẻ thành nhiều công văn riêng rẽ cho từng cơ quan.

1. **Nhận diện nhu cầu ban hành văn bản giao việc:**
   - Khi văn bản cấp trên có yêu cầu địa phương tổ chức quán triệt, tuyên truyền hoặc triển khai thực hiện (đặc biệt là khi giao cho khối chính quyền UBND xã/MTTQ xã vì hệ thống ĐHTN không tạo nhiệm vụ trực tiếp sang được).
2. **Đóng gói ngữ cảnh bàn giao sang Skill `cong-van`:**
   - Trích xuất căn cứ pháp lý (Số hiệu, ngày ban hành, cơ quan ban hành, trích yếu).
   - Chia các gạch đầu dòng giao rõ nhiệm vụ và hạn trình cho từng cơ quan ngay trong cùng một công văn (học theo mẫu thực tế đã ban hành của Đảng uỷ xã: `786-CV/ĐU`, `791-CV/ĐU`, `794-CV/ĐU`).
3. **Sinh tệp dự thảo:**
   - Gọi skill **`cong-van`** để xuất tệp Word lưu tại `van_ban_du_thao/2026/Cong_van/CV giao viec [Trich yeu rut gon].docx` đúng chuẩn thể thức Hướng dẫn số 05-HD/VPTW.

---

## PHẦN IV. MẪU BẢN TIN ZALO NHẮC VIỆC & MẪU BÚT PHÊ CHỈ ĐẠO CHUẨN

### 1. Template Bản tin Morning Brief qua Zalo (Gửi Phó CVP mỗi sáng)
```markdown
🇻🇳 VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI - BẢN TIN ĐIỀU HÀNH TÁC NGHIỆP SÁNG [dd/mm/yyyy]
Kính gửi: Đồng chí Ngô Hoàng Việt - Phó Chánh Văn phòng Đảng uỷ

Hệ thống ĐHTN hiện ghi nhận: [X] văn bản đến chờ xử lý ([Y] quá hạn, [Z] sắp đến hạn).

🚨 1. VĂN BẢN QUÁ HẠN / SẮP ĐẾN HẠN (CẦN XỬ LÝ GẤP):
- [Số hiệu] ([Cơ quan gửi]): [Trích yếu ngắn gọn].
  + Vai trò: [Chủ trì (Luồng đỏ) / Giám sát chuyên viên [Tên] (Luồng xanh)].
  + Hạn chót: [dd/mm/yyyy] (Đã quá hạn / Còn 1 ngày).
  + Đề xuất của AI: [Gợi ý hành động: Đôn đốc chuyên viên / Soạn CV giao việc].

📋 2. VĂN BẢN MỚI TIẾP NHẬN CHƯA GIAO NHIỆM VỤ:
- [Số hiệu]: [Trích yếu].
  + Gợi ý phân công: Giao đ/c [Katơr Vế / Mai Thuỷ / Bích Thuỷ], hạn [dd/mm/yyyy].
- [Số hiệu]: [Trích yếu cần UBND xã thực hiện].
  + Gợi ý hành động: AI đã soạn sẵn dự thảo CV giao việc UBND xã tại thư mục dự thảo.

Kính báo đồng chí xem xét, chỉ đạo!
```

### 2. Thư viện Mẫu Bút phê Chỉ đạo thực chiến trong Pop-up "Chuyển văn bản"
*(Các mẫu tham khảo sát với thực tế điều hành tại Văn phòng Đảng uỷ xã Công Hải, AI vận dụng linh hoạt theo nội dung từng văn bản đến)*:

- **Mẫu 1 (Giao Ban Xây dựng Đảng chủ trì toàn bộ khi thuộc chức năng Ban XDĐ):**
  `Tham mưu Công văn giao Ban Xây dựng Đảng tham mưu Kế hoạch quán triệt, tuyên truyền, đồng thời tham mưu văn bản triển khai thực hiện; trình lãnh đạo Văn phòng trước ngày [dd/mm/yyyy].`
- **Mẫu 2 (Giao phối hợp 2 cơ quan: Ban Xây dựng Đảng quán triệt + UBND xã triển khai):**
  `Tham mưu Công văn giao Ban Xây dựng Đảng tham mưu Kế hoạch quán triệt, tuyên truyền; giao UBND xã tham mưu văn bản triển khai thực hiện; trình lãnh đạo Văn phòng trước ngày [dd/mm/yyyy].`
- **Mẫu 3 (Khi thuộc chức năng trực tiếp của Văn phòng Đảng uỷ):**
  `Tham mưu Văn bản triển khai thực hiện; trình lãnh đạo Văn phòng trước ngày [dd/mm/yyyy].`
- **Mẫu 4 (Đối với văn bản từ các cơ quan thuộc xã gửi đến - UBND xã, MTTQ, các Ban, Chi bộ...):**
  `Theo dõi, cập nhật.`
  *(⚠️ Lưu ý quan trọng: Quy tắc này áp dụng cho báo cáo, quyết định, kế hoạch, công văn thông thường từ các cơ quan thuộc xã; **TRỪ CÁC TỜ TRÌNH (-TTr) CỦA CÁC CƠ QUAN TRÌNH XIN Ý KIẾN/CHỦ TRƯƠNG** — đối với Tờ trình thì phải tham mưu thẩm định, bố trí lịch họp BTV/Thường trực cho ý kiến hoặc tham mưu văn bản trả lời).*

---

## PHẦN V. MA TRẬN XỬ LÝ NGOẠI LỆ & BẢO ĐẢM AN TOÀN HỆ THỐNG

| Tình huống ngoại lệ | Nguy cơ | Biện pháp xử lý của Chuyên viên ảo |
| :--- | :--- | :--- |
| **Văn bản đến có độ Mật** (dù chạy trên mạng Internet) | Vi phạm Luật Bảo vệ BMNN | Nếu phát hiện từ khoá MẬT/TỐI MẬT trên trích yếu hoặc ảnh scan, **dừng đọc ngay lập tức**, không cache, không gửi Zalo, báo đồng chí xử lý thủ công. |
| **Phiên làm việc (Session) hết hạn** | Bị đẩy về màn hình đăng nhập | Không tự ý gõ mật khẩu; thông báo đồng chí đăng nhập lại trên tab ẩn danh rồi AI tiếp tục. |
| **Tệp PDF là bản scan chất lượng thấp** | Không bóc tách được text | Sử dụng module OCR nội bộ (`doc_reader.py`) để nhận dạng ký tự quang học; đối soát kỹ các con số và ngày tháng. |
| **Văn bản có nhiều phụ lục phức tạp** | Bỏ sót bảng số liệu | Mở từng tệp đính kèm trong danh sách `File đính kèm (X)` để phân tích đầy đủ các biểu dự toán/danh sách đi kèm. |
| **Chuyên viên nộp dự thảo tham mưu chậm** | Trễ hạn giao việc của Đảng uỷ | Căn cứ ngày hoàn thành trong `Danh sách nhiệm vụ đơn vị`, AI tự động đưa vào danh sách cảnh báo đôn đốc trước 01 ngày. |

---

## PHẦN VI. VAI TRÒ CHUYÊN VIÊN THAM MƯU ĐỘC LẬP SONG SONG

Nhằm phục vụ đồng chí Phó Chánh Văn phòng trong việc **rèn luyện, nâng cao năng lực cho đội ngũ chuyên viên Văn phòng Đảng uỷ (Katơr Vế, Mai Thị Thuỷ, Lê Thị Bích Thuỷ)**:
- Đối với mỗi văn bản đến quan trọng được giao cho chuyên viên nghiên cứu, Chuyên viên ảo sẽ **chủ động lập 01 Bản tham mưu độc lập song song** (Đề cương tóm tắt + Các vấn đề trọng tâm cần lưu ý + Dự thảo văn bản mẫu).
- Bản tham mưu này gửi riêng cho đồng chí Phó Chánh Văn phòng để đồng chí dùng làm **thước đo đối chiếu, phản biện và chỉnh sửa** khi các chuyên viên nộp sản phẩm dự thảo lên, bảo đảm chất lượng tham mưu của Văn phòng Đảng uỷ xã Công Hải luôn đạt chuẩn mực chính trị cao nhất.
