# ĐẶC TẢ KỸ THUẬT & KẾ HOẠCH TRIỂN KHAI TỔNG THỂ: SỔ NHIỆM VỤ, SỔ TIÊU CHÍ, BỘ HẸN GIỜ VÀ KIẾN TRÚC HYBRID RAG HÀNH CHÍNH ĐẢNG - NHÀ NƯỚC
**Dự án:** Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà (`chatCHS` / `chuyenvienao`)  
**Tài liệu dành cho Đội Thực Thi (Engineering Blueprint & Checklist):** Thiết kế chuẩn hóa 100% dựa trên cấu trúc văn bản thực tế của Đảng uỷ, HĐND, UBND, UBMTTQVN xã Công Hải sau sáp nhập (mô hình chính quyền địa phương 02 cấp).  
**Quy chuẩn chính tả & dữ liệu:** Tuân thủ tuyệt đối quy định đặt dấu Khối Đảng (`oà`, `uỷ`, `uý`), cơ cấu 08 thôn mới, 21 chi bộ trực thuộc và 382 đảng viên theo Đề án số 03-ĐA/ĐU.

---

## I. PHÂN TÍCH THỰC CHIẾN TỪ KHO VĂN BẢN MẪU (7 BÀI TOÁN BẮT BUỘC PHẢI XỬ LÝ)

Qua rà soát thực tế các văn bản của Đảng uỷ xã Công Hải (như `140-BC/ĐU`, `141-BC/ĐU`, `142-BC/ĐU`, chuỗi Chương trình công tác `42, 48, 55, 67-CTr/ĐU`, `01-KH/ĐU`, `81-KH/ĐU`, `708-CV/ĐU`), đội thực thi **TUYỆT ĐỐI KHÔNG** dùng cách cắt văn bản (chunking) và lọc năm (filtering) thông thường vì 7 đặc thù sống còn sau:

### 1. Biến động Địa giới & Tổ chức sau Sáp nhập (Mốc lịch sử 01/7/2025)
* **Thực tế:** Xã Công Hải mới được thành lập theo Nghị quyết `1667/NQ-UBTVQH15` và Quyết định `3217-QĐ/TU` ngày 18/6/2025 trên cơ sở **sáp nhập xã Công Hải (cũ) và xã Phước Chiến (cũ)**, vận hành mô hình **chính quyền địa phương 02 cấp** (không còn cấp huyện Thuận Bắc, làm việc trực tiếp với Tỉnh uỷ/UBND tỉnh Khánh Hoà) từ ngày **01/7/2025**.
* **Hệ quả dữ liệu:** Các tài liệu cũ trước sáp nhập từng ghi 13 thôn, nhưng theo Đề án số 03-ĐA/ĐU ngày 26/6/2026 của Ban Chấp hành Đảng bộ xã, toàn xã đã sắp xếp lại thành **08 thôn chính thức** (Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng), **21 chi bộ trực thuộc** (08 chi bộ thôn, 03 chi bộ trường học và các chi bộ cơ quan/LLVT) với **382 đảng viên**.
* **Yêu cầu kỹ thuật:** Mọi dữ liệu Danh bạ và RAG phải lấy cơ cấu **08 thôn & 21 chi bộ** làm chuẩn. Văn bản trước `01/7/2025` phải được gắn nhãn `GIAI_DOAN = 'TRUOC_SAP_NHAP'` để AI không lấy nhầm số liệu đơn lẻ của xã cũ làm số liệu toàn xã mới.

### 2. Một File PDF Chứa Nhiều Văn Bản & Phụ Lục Bảng Biểu Phức Tạp (Compound Documents)
* **Thực tế:** File `A32.65-ĐU-BC-0140-2026` dài 42 trang nhưng thực chất chứa **04 báo cáo độc lập** (Trang 1–16: Báo cáo tập thể BTV Đảng uỷ; Trang 17–20: Báo cáo kiểm điểm cá nhân đ/c Trương Minh Vũ - Chủ tịch UBND xã; Trang 21–24: Báo cáo cá nhân đ/c Nguyễn Xuân Hoàng - Phó Bí thư TT; Trang 25–28: Báo cáo cá nhân đ/c Vũ Thị Thuỳ Trang - Bí thư Đảng uỷ) kèm theo **07 Phụ lục bảng biểu ngang** (Trang 29–42).
* **Nguy cơ:** Nếu cắt chunk bình thường, đoạn văn viết *"Bản thân nghiêm túc nhận trách nhiệm..."* ở trang 20 và trang 24 sẽ bị trộn lẫn, AI không biết là lời tự kiểm điểm của đồng chí nào!
* **Yêu cầu kỹ thuật:** Bộ đọc `doc_reader.py` phải nhận diện ranh giới văn bản con (`Sub-document Boundary`) và đóng gói từng dòng trong bảng Phụ lục kèm theo tiêu đề cột (`Table-Row-to-Markdown Serialization`), đồng thời có cơ chế fallback trích xuất khối Markdown khi OCR scan bị lệch bảng.

### 3. Hiện tượng "Trùng Số Hiệu" Giữa Các Cơ Quan Ban Hành Khác Nhau (ID Collision)
* **Thực tế trong `140-BC/ĐU` & `141-BC/ĐU`:**
  * Cùng số `01-QC/ĐU`: Có `01-QC/ĐU ngày 01/7/2025` (Quy chế làm việc của BCH Đảng bộ xã) VÀ `01-QC/ĐU ngày 18/7/2025` (Quy chế làm việc của UBKT Đảng uỷ).
  * Cùng số `01-QĐ/ĐU`: Có `01-QĐ/ĐU ngày 10/7/2025` (Quy định chức năng VP Đảng uỷ), `01-QĐ/ĐU ngày 27/8/2025` (Giải quyết nghỉ chế độ cho đ/c Pinăng Vô) VÀ `01-QĐ/ĐU ngày 24/11/2025` (Quy chế Ban Chỉ đạo 57).
  * Ngoài ra còn có `01-QĐ/UBKTĐU`, `01-QĐ/BCĐ`, `01/QĐ-UBND`, `01-KH/BCĐ` (06/11/2025) và `01-KH/BCĐ57` (12/12/2025).
* **Yêu cầu kỹ thuật:** **CẤM** dùng `so_hieu_vb` làm Khóa chính (Primary Key) hoặc định danh duy nhất. Khóa định danh chuẩn (`canonical_doc_key`) bắt buộc phải tổ hợp từ: `{so_hieu_vb}_{ngay_ban_hanh_ISO}_{co_quan_code}`.

### 4. Nhiệm vụ "Trượt / Chuyển tiếp" Qua Các Tháng & Hợp Nhất Văn Bản
* **Thực tế trong chuỗi `42-CTr/ĐU` (Tháng 1), `48-CTr/ĐU` (Tháng 2), `55-CTr/ĐU` (Tháng 3):**
  * Các Nghị quyết chuyên đề (như *Nghị quyết đẩy mạnh phát triển công nghiệp, năng lượng tái tạo*, *Nghị quyết cơ cấu lại ngành nông nghiệp*) dự kiến trình tháng 02 nhưng sang tháng 03 vẫn tiếp tục nằm trong Chương trình công tác.
  * Tại Mục 11 của `48-CTr/ĐU`: Ban Thường vụ cho ý kiến **hợp nhất 02 Nghị quyết** (*Phát triển KT-XH vùng đồng bào DTTS* và *Xây dựng NTM, giảm nghèo bền vững* vốn tách rời ở `42-CTr/ĐU`).
* **Yêu cầu kỹ thuật:** Khi bóc tách nhiệm vụ từ Chương trình công tác/Kế hoạch vào `so_nhiem_vu`, hệ thống phải có cơ chế **Khử trùng lặp ngữ nghĩa (Task Deduplication)** để cập nhật lùi thời hạn (`Rescheduled`) hoặc gộp nhiệm vụ (`Merged`) chứ không tạo ra 3 nhiệm vụ giống hệt nhau ở 3 tháng.

### 5. Lỗi Nhận Diện Chữ Ký Số, Con Dấu Đỏ & Mất Số/Ngày Khi Scan OCR
* **Thực tế:**
  * Các file đã ký số/đóng dấu (`142-BC/ĐU`, `708-CV/ĐU`, `67-CTr/ĐU`) khi qua OCR bị chèn các dòng rác ngay giữa câu: `T/M BAN THƯỜNG VỤ`, `CỘNG SẢN VIỆT NAM`, `24-04-2026 15:21:14+07:00`, `CÔNG HAY`, `NG BỘ TỈNH KH`.
  * Nhiều bản PDF lưu hành nội bộ bị khuyết số hoặc ngày trên mặt văn bản (VD: `Số -CTr/ĐU, ngày tháng 4 năm 2026` trong file `A32.65-ĐU-CTr-0067-2026`, hoặc `ngày Luháng 8 năm 2025` trong `01-KH/ĐU`).
* **Yêu cầu kỹ thuật:** Hỗ trợ linh hoạt 2 luồng nhận diện Metadata:
  1. Trích xuất từ **Tên file chuẩn E-Office** (`A32.65-{Cơ_quan}-{Thể_loại}-{Số_hiệu}-{Năm}`).
  2. Trích xuất từ **Tên file tiếng Việt rút gọn chuẩn AGENTS.md** (VD: `CV triển khai KH 144 ĐU chuẩn hoá dữ liệu ĐV.docx`, `BC tuần 42 VPĐU.docx`).

### 6. Bất nhất Số liệu Giữa Các Báo Cáo (Phải Phân biệt Phạm vi & Kỳ thống kê)
* **Thực tế ngày 21/4/2026 (`140-BC/ĐU`):**
  * Ở trang 9 ghi TTHC Quý I/2026 tiếp nhận `1.026 hồ sơ` (trực tuyến `974 hồ sơ`, đạt `94,93%`). Nhưng ở trang 11 lại ghi Quý I/2026 tiếp nhận `1.005 hồ sơ` (trực tuyến đạt `99%`).
  * Giải ngân đầu tư công Quý I/2026 trong báo cáo cá nhân Chủ tịch UBND xã (`140-BC/ĐU` trang 18) ghi `5,809/20,585 tỷ đồng (28,2%)`, nhưng trong `141-BC/ĐU` trang 1 (ngày 23/4/2026) ghi `7.414/41.046 triệu đồng (18%)`.
* **Yêu cầu kỹ thuật:** Không bao giờ cho AI nuốt con số trần trụi. Mọi con số phải đi kèm ngữ cảnh: `[Theo văn bản nào | Ngày báo cáo | Phạm vi thống kê]`. Nếu có 2 con số khác nhau ở 2 báo cáo gần ngày nhau, AI phải **trình bày cả hai kèm nguồn trích dẫn** để cán bộ chọn, tuyệt đối không tự ý làm tròn hay chọn bừa.

### 7. Ràng buộc An ninh mạng & Bảo vệ Bí mật Nhà nước (Nghị định 63/2026/NĐ-CP & Quyết định 37-QĐ/ĐU)
* **Thực tế trong `141-BC/ĐU` (Mục II.3.8):** Đảng uỷ xã thực hiện nghiêm Quyết định `37-QĐ/ĐU` ngày 29/12/2025 và Nghị định `63/2026/NĐ-CP`: **Cấm tuyệt đối việc soạn thảo, lưu trữ, truyền đưa tài liệu Mật, Tối mật trên môi trường Internet**.
* **Yêu cầu kỹ thuật:** Bộ nạp văn bản (`doc_indexer.py`) phải có chốt chặn đầu tiên là **Secret Document Gatekeeper**: Quét từ khóa đóng dấu độ mật (`MẬT`, `TỐI MẬT`, `TUYỆT MẬT`) ở góc trên văn bản. Nếu phát hiện, lập tức **từ chối nạp vào CSDL và không gửi lên AI**, đồng thời ghi cảnh báo cho Chánh Văn phòng.

### 8. Đánh Giá Công Cụ MarkItDown (Microsoft) & Thách Thức Văn Bản Ký Số
* **Khảo sát ban đầu:** Cân nhắc sử dụng MarkItDown để chuyển đổi nhanh các bảng biểu trong `.docx`, `.xlsx` thành bảng Markdown chuẩn (`| Cột 1 | Cột 2 |`).
* **Hạn chế bộc lộ qua thực tế:**
  1. *Thiếu OCR tiếng Việt:* Các file scan ảnh thuần túy trả về kết quả rỗng (0 ký tự).
  2. *Lỗi dính từ (Kerning Font):* Khi đọc các PDF được in ảo từ Word tiếng Việt, MarkItDown làm mất khoảng trắng giữa các từ (`vụngàycàngtốthơnngườidân...`), gây hỏng hoàn toàn ngữ nghĩa khi đưa vào mô hình Embedding.
  3. *Không tự bóc tách được Metadata:* MarkItDown chỉ đọc luồng text tuần tự, hoàn toàn không có khả năng nhận diện con dấu hay bóc tách Số hiệu/Ngày tháng để gán vào siêu dữ liệu văn bản.

### 9. Bài Học Thực Nghiệm Từ Kho 16 Nghị Quyết & Cảnh Báo Điểm Nghẽn Ký Số Điện Tử (VNPT iOffice)
* **Kết quả thực nghiệm trực tiếp trên toàn bộ 16 tệp Nghị quyết:**
  * **Đặc thù ký số điện tử:** Trong văn bản gốc, dòng tiêu đề luôn để trống: `Số        -NQ/ĐU` và `Công Hải, ngày       tháng ... năm ...`. Số hiệu (ví dụ `11`) và ngày (ví dụ `08`) được hệ thống ký số điện tử (VNPT iOffice / e-Sign) áp một lớp tem đè (overlay text/annotation/widget) lên trên.
  * **Hệ quả khi chuyển sang `.md`:** Các bộ đọc PDF dạng stream (MarkItDown, pdfminer, PyMuPDF thông thường) đọc theo thứ tự luồng đối tượng. Do đó, dòng tiêu đề vẫn giữ nguyên khoảng trắng khuyết (`Số        -NQ/ĐU`), trong khi số `11` và ngày `08` bị đẩy rớt xuống tít tận đáy trang như các con số rời rạc, vô nghĩa; chuỗi thời gian ký số (`08-06-2026 16:34:05 +07:00`) bị ném lẫn vào khối nơi nhận và chữ ký cuối văn bản.
  * **Với văn bản Scan ảnh (NQ 01, NQ 05, NQ 08, NQ 09):** Bắt buộc phải qua OCR. Tuy nhiên OCR offline cục bộ chưa bảo đảm 100% dấu tiếng Việt và bố cục cột, bảng biểu.
* **CẢNH BÁO ĐIỂM NGHẼN KỸ THUẬT TRỌNG YẾU (UNRESOLVED TECHNICAL BOTTLENECK):**
  * **Hiện tại hệ thống CHƯA TÌM RA GIẢI PHÁP TỰ ĐỘNG TỐI ƯU để bóc tách chính xác 100% hai trường Số hiệu và Ngày tháng năm từ bên trong file PDF khi 2 trường thông tin này được người dùng ký số điện tử.**
  * Mọi nỗ lực dùng regex bóc thô từ luồng chữ phẳng của file PDF đều tiềm ẩn nguy cơ lệch vị trí, gãy cấu trúc ngữ nghĩa hoặc dính từ, dẫn đến việc chia chunk (chunking) bị sai lệch thông tin đầu vào của RAG.
* **QUYẾT ĐỊNH CHIẾN LƯỢC CỦA ĐỘI THỰC THI:**
  * **TẠM DỪNG ngay phương án tự động chuyển đổi toàn bộ kho văn bản sang file `.md` bằng một công cụ đơn lẻ để chia chunk.**
  * Giữ nguyên vẹn toàn bộ kho văn bản gốc (`.pdf`, `.docx`) trong thư mục `references/` và `van_ban_den/`.
  * Đặt bài toán bóc tách trường ký số vào diện nghiên cứu chuyên sâu (phân tích cấu trúc Signature Widget / Form Field tọa độ của PDF hoặc bổ sung giao diện đối soát bán tự động Human-in-the-Loop) trước khi quyết định tái khởi động khâu nạp và chia chunk hàng loạt.

---

## II. KIẾN TRÚC TỔNG THỂ: "DOSSIER & CITATION-AWARE HYBRID RAG" TRÊN SQLITE (WAL MODE)

Giải pháp tối ưu nhất cho quy mô 1.000 – 10.000 văn bản cấp xã trên máy tính Windows là sử dụng duy nhất 01 tệp **`data/chuyen_vien_ao.db` (SQLite WAL Mode + FTS5 BM25 + Vector BLOB + Bảng Đồ thị Liên kết Văn bản)**, kết hợp tính toán Cosine Similarity trực tiếp trên RAM bằng Python để tránh phụ thuộc vào các thư viện C/DLL dễ lỗi:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│        ĐẦU VÀO: KHO 1.000+ VĂN BẢN (.docx, .doc, .pdf, .xlsx, .md)         │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  TẦNG 1: TIỀN XỬ LÝ & LÀM SẠCH ĐẶC THÙ HÀNH CHÍNH (INGESTION PIPELINE)     │
│  1. Secret Gatekeeper: Chặn tuyệt đối văn bản có dấu MẬT / TỐI MẬT         │
│  2. Dual Filename Parser: Hỗ trợ cả mã E-Office và tên tiếng Việt chuẩn     │
│  3. Red-Stamp & OCR Cleaner: Xóa rác con dấu đỏ, chuẩn hóa Unicode NFC     │
│  4. Sub-Document & Table Serializer: Tách báo cáo cá nhân & bảng Phụ lục   │
│  5. Citation & Replacement Extractor: Bóc "Căn cứ", "Thực hiện", "Thay thế"│
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  TẦNG 2: CƠ SỞ DỮ LIỆU HỢP NHẤT SQLITE (`data/chuyen_vien_ao.db` - WAL)    │
│  • Nhóm Quản trị Việc: `danh_ba_can_bo`, `so_nhiem_vu`, `lich_su_nhac_nho` │
│  • Nhóm Giám sát KPI : `so_tieu_chi` (Đại hội Đảng bộ khóa I & NQ57)       │
│  • Nhóm Kho Văn bản  : `so_van_ban` (Phân 3 tầng vòng đời + Mã chuyên đề)  │
│  • Nhóm Đồ thị Căn cứ: `van_ban_lien_ket` (Mạng lưới Thay thế/Sửa đổi/Căn cứ│
│  • Nhóm Tìm kiếm Lai : `van_ban_fts` (BM25) + `van_ban_chunks` (Vector BLOB│
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  TẦNG 3: CHIẾN LƯỢC TRUY XUẤT ĐA TẦNG "GIỎ NGỮ CẢNH 2 - 4 - 2"             │
│  • Bước 1: FTS5 BM25 lọc nhanh Top 30-50 ứng viên (< 2ms)                  │
│  • Bước 2: Python In-Memory Vector Rerank (Tính Cosine trên RAM an toàn)   │
│  • 02 Đoạn từ Tầng Nền tảng (`CORE_DIRECTIVE`: Quy chế, NQ Đại hội, NQ57)  │
│  • 04 Đoạn từ Tầng Chuyên đề mới nhất (`THEMATIC_CASE`: KH, BC, KL hiện tại│
│  • 02 Đoạn kéo theo từ Đồ thị Căn cứ (`1-Hop Citation`: Văn bản gốc năm cũ)│
│  * Loại bỏ tự động các văn bản đã bị THAY THẾ hoặc Sự vụ hết hạn           │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## III. THIẾT KẾ SCHEMA SQLITE CHI TIẾT (CHUẨN HÓA CHO ĐỘI CODE)

Toàn bộ các bảng dưới đây được khởi tạo trong `server/services/db_service.py` với `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON;`:

### 1. Bảng Danh bạ Cán bộ & Tổ chức (`danh_ba_can_bo`)
Đã cập nhật chuẩn hóa cơ cấu **03 cơ quan tham mưu Đảng uỷ, HĐND (02 Ban), UBND (04 phòng/trung tâm), MTTQ (04 đoàn thể) và 08 thôn, 21 chi bộ trực thuộc**:
```sql
CREATE TABLE IF NOT EXISTS danh_ba_can_bo (
    can_bo_id TEXT PRIMARY KEY,          -- VD: 'CB-TTDU-01', 'CB-UBND-01', 'CB-THON-01'
    ho_ten TEXT NOT NULL,                -- VD: 'Vũ Thị Thuỳ Trang', 'Nguyễn Xuân Hoàng', 'Trương Minh Vũ'
    chuc_vu TEXT NOT NULL,               -- VD: 'Bí thư Đảng uỷ, Chủ tịch HĐND xã'
    co_quan TEXT NOT NULL,               -- VD: 'Thường trực Đảng uỷ', 'UBND xã', 'Chi bộ thôn Ma Trai'
    co_quan_code TEXT NOT NULL,          -- VD: 'TTDU', 'VPDU', 'BXDD', 'UBKT', 'UBND', 'MTTQ', 'THON_MA_TRAI'
    co_quan_loai TEXT NOT NULL,          -- 'thuong_truc' | 'co_quan_dang' | 'chinh_quyen' | 'mttq' | 'chi_bo_thon' | 'chi_bo_truong'
    zalo_chat_id TEXT,                   -- ID chat Zalo 1-1 để gửi nhắc việc
    zalo_user_id TEXT,
    so_dien_thoai TEXT,
    vai_tro TEXT DEFAULT 'chuyen_vien',  -- 'lanh_dao_thuong_truc' | 'lanh_dao_co_quan' | 'chuyen_vien' | 'bi_thu_chi_bo'
    is_active INTEGER DEFAULT 1,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Bảng Sổ Nhiệm vụ Cơ quan (`so_nhiem_vu`)
Hỗ trợ cả nhiệm vụ giao theo ngày cụ thể (Công văn/Thông báo) và nhiệm vụ giao theo tháng/quý (Chương trình công tác `-CTr/ĐU`):
```sql
CREATE TABLE IF NOT EXISTS so_nhiem_vu (
    task_id TEXT PRIMARY KEY,            -- VD: 'NV-2026-001'
    task_fingerprint TEXT UNIQUE,        -- Mã băm chuẩn hóa (co_quan_code + nội dung rút gọn) để chống tạo trùng khi trượt tháng
    so_hieu_vb TEXT,                     -- VD: '708-CV/ĐU', '67-CTr/ĐU'
    doc_id TEXT,                         -- FK mềm trỏ tới bảng so_van_ban
    can_bo_id TEXT,                      -- FK trỏ tới danh_ba_can_bo
    co_quan_chu_tri TEXT NOT NULL,       -- VD: 'Ban Xây dựng Đảng', 'UBND xã'
    co_quan_chu_tri_code TEXT NOT NULL,  -- VD: 'BXDD', 'UBND'
    co_quan_phoi_hop TEXT DEFAULT '[]',  -- JSON Array: '["UBKT Đảng uỷ", "MTTQVN xã"]'
    lanh_dao_chi_dao TEXT,               -- VD: 'Bí thư Đảng uỷ', 'Phó Bí thư TTĐU', 'Chủ tịch UBND xã'
    cap_trinh TEXT,                      -- VD: 'Thường trực, BTV, BCH Đảng uỷ' (Đặc thù của Chương trình công tác)
    noi_dung_nhiem_vu TEXT NOT NULL,     -- Nội dung công việc chuẩn 5 Rõ
    ngay_giao TEXT NOT NULL,             -- Chuẩn ISO-8601: 'YYYY-MM-DD'
    deadline_date TEXT NOT NULL,         -- Chuẩn ISO-8601: 'YYYY-MM-DD' (Nếu văn bản chỉ ghi "Tháng 4/2026" -> quy về '2026-04-25')
    deadline_time TEXT DEFAULT '17:00',  -- Chuẩn 'HH:MM' (VD: '11:00' cho báo cáo tuần sáng thứ Sáu)
    deadline_type TEXT DEFAULT 'EXACT',  -- 'EXACT' (Ngày cụ thể) | 'MONTH_END' (Theo tháng CTr) | 'RECURRING' (Thường xuyên)
    che_do_bao_cao TEXT,
    trang_thai TEXT DEFAULT 'Chưa thực hiện', -- 'Chưa thực hiện' | 'Đang thực hiện' | 'Hoàn thành' | 'Quá hạn' | 'Chuyển tiếp tháng sau'
    muc_do_uu_tien TEXT DEFAULT 'Bình thường',-- 'Bình thường' | 'Cao' | 'Khẩn'
    linh_vuc TEXT,                       -- 'Xây dựng Đảng' | 'Kinh tế - Xã hội' | 'Chuyển đổi số & NQ57' | 'Nội chính - KTGS'
    ket_qua_bao_cao TEXT,
    created_from_wf TEXT DEFAULT 'manual',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (can_bo_id) REFERENCES danh_ba_can_bo(can_bo_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON so_nhiem_vu(deadline_date, trang_thai);
CREATE INDEX IF NOT EXISTS idx_tasks_unit ON so_nhiem_vu(co_quan_chu_tri_code, trang_thai);
```

### 3. Bảng Lịch sử Nhắc việc Chống Gửi Lặp (`lich_su_nhac_nho`)
```sql
CREATE TABLE IF NOT EXISTS lich_su_nhac_nho (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    remind_key TEXT UNIQUE NOT NULL,     -- Khóa chống gửi lặp: 'MORNING_2026-10-26_CB-BXDD-01'
    task_id TEXT,
    can_bo_id TEXT,
    loai_nhac TEXT NOT NULL,             -- 'DUE_SOON' | 'OVERDUE' | 'WEEKLY_REPORT' | 'PARTY_MEETING_03' | 'MONTHLY_25'
    hinh_thuc TEXT DEFAULT 'zalo_1_1',   -- 'zalo_1_1' | 'zalo_group'
    noi_dung_nhac TEXT,
    thoi_gian_nhac TEXT DEFAULT CURRENT_TIMESTAMP,
    ket_qua TEXT DEFAULT 'pending'       -- 'pending' | 'success' | 'failed'
);
```

### 4. Bảng Sổ Tiêu chí Nghị quyết Đại hội & NQ57 (`so_tieu_chi`)
Lưu trữ 20 chỉ tiêu Nghị quyết Đại hội Đảng bộ xã khóa I (`01-NQ/ĐH`) và 19 chỉ tiêu Chuyển đổi số (`Phụ lục 2 - Báo cáo 141-BC/ĐU`):
```sql
CREATE TABLE IF NOT EXISTS so_tieu_chi (
    kpi_id TEXT PRIMARY KEY,             -- VD: 'KPI-DH-01', 'KPI-NQ57-08'
    nguon_nghi_quyet TEXT NOT NULL,      -- 'NQ_DAI_HOI_I' | 'NQ57_CDS' | 'KTXH_NAM_2026'
    nhom_chi_tieu TEXT NOT NULL,         -- VD: 'Chính quyền số và Dịch vụ công', 'Xây dựng Đảng'
    ten_chi_tieu TEXT NOT NULL,          -- VD: 'Tỷ lệ giải quyết hồ sơ TTHC trực tuyến'
    don_vi_tinh TEXT NOT NULL,           -- '%' | 'triệu đồng' | 'tỷ đồng' | 'đảng viên' | 'thôn'
    chi_tieu_nam_2026 REAL,              -- VD: 90.0 (Tối thiểu 90%)
    chi_tieu_nhiem_ky_2030 REAL,         -- VD: 95.0
    gia_tri_hien_tai REAL DEFAULT 0,     -- VD: 94.93
    bieu_thuc_chi_tiet TEXT,             -- VD: '974/1.026 hồ sơ (Quý I/2026)'
    ky_danh_gia TEXT DEFAULT 'Quy',      -- 'Thang' | 'Quy' | 'Nam'
    co_quan_phu_trach TEXT,              -- VD: 'UBND xã, TT Phục vụ HCC'
    trang_thai_anh_sang TEXT DEFAULT 'XANH', -- 'XANH' (Đạt/Vượt) | 'VANG' (Cần đôn đốc) | 'DO' (Nguy cơ hụt)
    ghi_chu_vuong_mac TEXT,              -- VD: 'Còn 86 đảng viên lớn tuổi chưa đăng nhập Sổ tay ĐVĐT'
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Bảng Kho Văn bản Hành chính (`so_van_ban`) — Trái tim của Hybrid RAG
Giải quyết triệt để bài toán trùng số hiệu, phân tầng vòng đời và quản lý hiệu lực:
```sql
CREATE TABLE IF NOT EXISTS so_van_ban (
    doc_id TEXT PRIMARY KEY,             -- UUID hoặc Canonical Key: '140-BC/DU_2026-04-21_DU'
    file_hash TEXT UNIQUE NOT NULL,      -- SHA-256 của file vật lý (Chống nạp trùng 100%)
    ma_ho_so_eoffice TEXT,               -- Bóc từ tên file: 'A32.65-ĐU-BC-0140-2026' (nếu có)
    so_hieu_vb TEXT NOT NULL,            -- Chuẩn hóa: '140-BC/ĐU', '116/QĐ-UBND', '01-KH/BCĐ57'
    loai_luong TEXT NOT NULL,            -- 'VAN_BAN_DI' (Xã ban hành) | 'VAN_BAN_DEN' (Tỉnh/TW gửi về) | 'NOI_BO'
    the_loai_vb TEXT NOT NULL,           -- 'NQ' | 'CT' | 'QC' | 'QD' | 'CTr' | 'KH' | 'BC' | 'TB' | 'KL' | 'CV' | 'BS' | 'GM'
    cap_ban_hanh TEXT NOT NULL,          -- 'TRUNG_UONG' | 'TINH_KHANH_HOA' | 'XA_CONG_HAI'
    co_quan_ban_hanh TEXT NOT NULL,      -- 'Đảng uỷ xã', 'UBND xã', 'HĐND xã', 'UBKT Đảng uỷ', 'Ban Chỉ đạo 57', 'BTV Tỉnh uỷ'
    co_quan_ban_hanh_code TEXT NOT NULL, -- 'DU', 'UBND', 'HDND', 'UBKT', 'BCD57', 'TU', 'BTGDVTU'
    ngay_ban_hanh TEXT NOT NULL,         -- Chuẩn ISO-8601: 'YYYY-MM-DD'
    nam_ban_hanh INTEGER NOT NULL,       -- 2024, 2025, 2026
    giai_doan_lich_su TEXT DEFAULT 'SAU_SAP_NHAP', -- 'TRUOC_SAP_NHAP' (< 2025-07-01) | 'SAU_SAP_NHAP' (>= 2025-07-01)
    trich_yeu TEXT NOT NULL,
    nhom_vong_doi TEXT NOT NULL,         -- 'CORE_DIRECTIVE' (Tầng 1: Nền tảng) | 'THEMATIC_CASE' (Tầng 2: Chuyên đề) | 'EPHEMERAL_EVENT' (Tầng 3: Sự vụ ngắn hạn)
    trong_so_tham_quyen INTEGER DEFAULT 50, -- Điểm ưu tiên: NQ/QC/QĐ (100) > CTr/KH/KL (80) > BC/TB (60) > CV (40) > BS/GM (10)
    ma_chuyen_de TEXT,                   -- Gom hồ sơ: 'CD_CHINH_QUYEN_2_CAP', 'CD_NQ57_CDS', 'CD_PHAT_TRIEN_DANG', 'CD_KTGS', 'CD_KTXH_NGAN_SACH'
    trang_thai_hieu_luc TEXT DEFAULT 'CON_HIEU_LUC', -- 'CON_HIEU_LUC' | 'BI_THAY_THE' | 'DA_SUA_DOI_BO_SUNG' | 'HET_HAN_SU_VU'
    bi_thay_the_boi_so_hieu TEXT,        -- VD: '08-TB/ĐU' bị thay thế bởi '19-TB/ĐU' -> sau đó bởi '72-TB/ĐU'
    nguoi_ky TEXT,                       -- VD: 'Vũ Thị Thuỳ Trang', 'Nguyễn Xuân Hoàng', 'Trương Minh Vũ'
    file_path TEXT NOT NULL,
    gdrive_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_vb_so_hieu ON so_van_ban(so_hieu_vb);
CREATE INDEX IF NOT EXISTS idx_vb_filter ON so_van_ban(trang_thai_hieu_luc, nhom_vong_doi, ma_chuyen_de, ngay_ban_hanh DESC);
```

### 6. Bảng Đồ thị Liên kết & Kế thừa Văn bản (`van_ban_lien_ket`)
Đây là chìa khóa giải quyết bài toán **văn bản năm mới sửa đổi/kế thừa văn bản năm cũ** (VD: `708-CV/ĐU` triển khai `90-KH/TU`; `116/QĐ-UBND` thay thế `43/QĐ-UBND`; `19-TB/ĐU` thay thế `08-TB/ĐU`):
```sql
CREATE TABLE IF NOT EXISTS van_ban_lien_ket (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vb_nguon_doc_id TEXT NOT NULL,       -- doc_id của văn bản mới
    vb_nguon_so_hieu TEXT NOT NULL,      -- VD: '116/QĐ-UBND'
    vb_dich_so_hieu TEXT NOT NULL,       -- VD: '43/QĐ-UBND' (hoặc văn bản cấp trên '57-NQ/TW', '327-QĐ/TU')
    loai_quan_he TEXT NOT NULL,          -- 'THAY_THE' | 'SUA_DOI_BO_SUNG' | 'THUC_HIEN_CHI_DAO' | 'CAN_CU_PHAP_LY' | 'BAO_CAO_CHO'
    ghi_chu_quan_he TEXT,
    UNIQUE(vb_nguon_doc_id, vb_dich_so_hieu, loai_quan_he)
);
CREATE INDEX IF NOT EXISTS idx_link_nguon ON van_ban_lien_ket(vb_nguon_so_hieu);
CREATE INDEX IF NOT EXISTS idx_link_dich ON van_ban_lien_ket(vb_dich_so_hieu);
```

### 7. Bảng Phân đoạn Văn bản (`van_ban_chunks`) & Tìm kiếm Toàn văn (`van_ban_fts`)
```sql
CREATE TABLE IF NOT EXISTS van_ban_chunks (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    sub_doc_owner TEXT DEFAULT 'TAP_THE',-- 'TAP_THE' | 'CA_NHAN: Trương Minh Vũ' | 'PHU_LUC_1'
    section_path TEXT,                   -- VD: 'Phần A > Mục III > 1.1. Tổ chức bộ máy'
    chunk_type TEXT DEFAULT 'PROSE',     -- 'PROSE' (Văn xuôi) | 'TABLE_ROW' (Dòng bảng biểu/Phụ lục) | 'TASK_ITEM' (Mục giao việc)
    context_header TEXT NOT NULL,        -- Thẻ căn cước đóng cứng vào đầu mỗi đoạn
    chunk_text TEXT NOT NULL,            -- Nội dung sạch đã gắn context_header
    embedding BLOB,                      -- Vector float32 nén nhị phân (dùng Python RAM tính Cosine similarity)
    FOREIGN KEY (doc_id) REFERENCES so_van_ban(doc_id) ON DELETE CASCADE
);

-- Bảng ảo FTS5 sử dụng bộ tách từ unicode61 hỗ trợ tiếng Việt có dấu & ký hiệu văn bản
CREATE VIRTUAL TABLE IF NOT EXISTS van_ban_fts USING fts5(
    chunk_id UNINDEXED,
    doc_id UNINDEXED,
    so_hieu_vb,
    trich_yeu,
    section_path,
    chunk_text,
    tokenize='unicode61 remove_diacritics 0 tokenchars "-/."'
);
```
*(Lưu ý kỹ thuật: Cấu hình `tokenchars "-/."` trong FTS5 giúp SQLite coi `140-BC/ĐU` hoặc `1667/NQ-UBTVQH15` là **01 từ khóa nguyên vẹn**, khi cán bộ gõ tìm `140-BC/ĐU` sẽ khớp chính xác 100% trong 1ms mà không bị tách vụn thành `140`, `BC`, `ĐU`).*

---

## IV. THUẬT TOÁN XỬ LÝ VĂN BẢN & CHUNKING HÀNH CHÍNH (`rag_service.py`)

Đội thực thi cần tuân thủ nghiêm ngặt 5 quy tắc xử lý trong `server/services/rag_service.py`:

### 1. Bộ lọc Làm sạch Rác Con Dấu Đỏ & Chữ Ký Số (OCR Stamp Sanitizer)
Khi đọc văn bản từ PDF đã ký số (`.signed.pdf` hoặc bản scan có đóng dấu đỏ), phải chạy bước lọc Regex loại bỏ các dòng nhiễu trước khi cắt chunk:
* Loại bỏ các dòng rời rạc chỉ chứa mảnh vỡ của con dấu: `r"^(ĐẢNG CỘNG SẢN VIỆT NAM|CỘNG SẢN VIỆT|ĐẢNG BỘ TỈNH KHÁNH|CÔNG HAY|TẠM BAN THƯỜNG VỤ|VIPHÓ BÍ THƯ).*$"` khi nằm gần cụm chữ ký cuối trang.
* Chuẩn hóa chính tả Khối Đảng: `Ủy` $\rightarrow$ `Uỷ`, `ủy` $\rightarrow$ `uỷ`, `Hòa` $\rightarrow$ `Hoà`, `hòa` $\rightarrow$ `hoà`, `Úy` $\rightarrow$ `Uý`, `úy` $\rightarrow$ `uý` (Đồng nhất toàn bộ về chuẩn Unicode NFC).

### 2. Kỹ thuật Cắt Văn bản Đa tầng (Multi-Document & Table-Aware Chunking)
* **Tách Văn bản con (Sub-document Splitting):** Nếu trong 1 file PDF xuất hiện lặp lại Quốc hiệu / Tiêu ngữ (`ĐẢNG BỘ TỈNH KHÁNH HOÀ - ĐẢNG UỶ XÃ CÔNG HẢI`) hoặc xuất hiện tiêu đề `B. ĐỐI VỚI CÁ NHÂN - I. SƠ YẾU LÝ LỊCH - Họ và tên: [Tên Cán Bộ]`, thuật toán lập tức cập nhật biến `sub_doc_owner = "CA_NHAN: {Tên Cán Bộ}"`. Mọi đoạn văn phía dưới đều mang tên cán bộ đó trong `context_header`.
* **Biến Dòng Bảng Biểu thành Câu Hoàn chỉnh (Table Row Contextualization):**
  Với các bảng trong Chương trình công tác (`42, 48, 55, 67-CTr/ĐU`) hoặc Phụ lục Báo cáo (`140, 141-BC/ĐU`), **không cắt ngang bảng làm mất tiêu đề cột**. Mỗi dòng (row) hoặc nhóm 3 dòng của bảng phải được chuyển thành cấu trúc tự sự:
  > `[Văn bản: 141-BC/ĐU | Phụ lục 2: Các chỉ tiêu cụ thể NQ57 | Nhóm II: Chính quyền số] Chỉ tiêu số 8: Tỷ lệ giải quyết hồ sơ thủ tục hành chính trực tuyến | Yêu cầu 2026: Tối thiểu 90% | Kết quả Quý I/2026: Đạt 94,93% (974/1.026 hồ sơ) | Cơ quan chủ trì: UBND xã, TT Phục vụ Hành chính công.`
  * *Cơ chế Fallback:* Với bảng scan quá mờ hoặc phức tạp, hệ thống chuyển nguyên khối bảng sang Markdown format để giữ nguyên liên kết hàng/cột.

### 3. Tự động Cập nhật Hiệu lực Văn bản Dây chuyền (Auto-Invalidation Trigger)
Khi nạp một văn bản mới vào `so_van_ban`:
* Nếu trích yếu hoặc nội dung có cụm: `"thay thế {Loại VB} số {X}"` (Ví dụ: Quyết định `116/QĐ-UBND` ngày 05/02/2026 *thay thế* Quyết định `43/QĐ-UBND` ngày 01/7/2025; hoặc Thông báo `72-TB/ĐU` *điều chỉnh, bổ sung* `19-TB/ĐU` và `08-TB/ĐU`):
  1. Ghi quan hệ `THAY_THE` hoặc `SUA_DOI_BO_SUNG` vào bảng `van_ban_lien_ket`.
  2. Tự động chạy lệnh SQL cập nhật văn bản cũ (`43/QĐ-UBND`, `08-TB/ĐU`): `SET trang_thai_hieu_luc = 'BI_THAY_THE', bi_thay_the_boi_so_hieu = '116/QĐ-UBND'`.
* Nhờ vậy, kho văn bản vẫn giữ nguyên văn bản cũ để tra cứu lịch sử khi cần, nhưng AI sẽ **không bao giờ lấy nhầm văn bản đã bị thay thế** để làm căn cứ hiện hành.

### 4. Chiến lược Truy xuất "Giỏ Ngữ Cảnh 2 - 4 - 2" (Không lo mất văn bản cũ quan trọng, không sợ rác sự vụ)
Khi AI cần trả lời câu hỏi hoặc tham mưu dự thảo văn bản về chủ đề $Q$:
* **Bước 1 (Loại bỏ nhiễu):** Câu lệnh SQL chỉ loại bỏ các văn bản có `trang_thai_hieu_luc = 'BI_THAY_THE'` và các văn bản thuộc tầng sự vụ (`nhom_vong_doi = 'EPHEMERAL_EVENT'`) đã qua hạn. **KHÔNG lọc bỏ theo năm** đối với tầng Nền tảng và Chuyên đề.
* **Bước 2 (Lấy Giỏ 2 - 4 - 2 = Tối đa 8 đoạn trích chất lượng cao nhất):**
  * **Slot 1–2 (02 đoạn Nền tảng - `CORE_DIRECTIVE`):** Tìm trong các Nghị quyết Đại hội, Nghị quyết chuyên đề (`02-NQ/ĐU`, `11-NQ/TU`), Quy chế làm việc (`01-QC/ĐU`, `116/QĐ-UBND`), Quyết định chức năng nhiệm vụ còn hiệu lực.
  * **Slot 3–6 (04 đoạn Chuyên đề mới nhất - `THEMATIC_CASE`):** Dùng FTS5 BM25 lọc ra Top 30 ứng viên, sau đó Python tính điểm Cosine Similarity trên RAM kết hợp điểm ưu tiên độ mới để lấy 04 đoạn sát nhất từ các Báo cáo (`140, 141, 142-BC/ĐU`), Kế hoạch (`45, 81-KH/ĐU`), Chương trình công tác mới nhất.
  * **Slot 7–8 (02 đoạn Kéo theo từ Mạng lưới Căn cứ - `1-Hop Citation Expansion`):** Từ các văn bản tìm được ở Slot 3–6, hệ thống tra bảng `van_ban_lien_ket` để tự động lôi thêm 02 đoạn từ **văn bản gốc năm trước** hoặc **văn bản được sửa đổi, bổ sung** đi kèm.

---

## V. CHECKLIST THỰC THI TỪNG BƯỚC CHO ĐỘI PHÁT TRIỂN (5 GIAI ĐOẠN)

### GIAI ĐOẠN 1: Khởi tạo SQLite Hợp nhất & Chuẩn hóa Dữ liệu Xã Công Hải Sau Sáp Nhập
- [ ] **1.1. Xây dựng `server/services/db_service.py`:**
  - [ ] Khởi tạo `data/chuyen_vien_ao.db` với `WAL mode` và đầy đủ 07 bảng (`danh_ba_can_bo`, `so_nhiem_vu`, `lich_su_nhac_nho`, `so_tieu_chi`, `so_van_ban`, `van_ban_lien_ket`, `van_ban_chunks` + `van_ban_fts`).
  - [ ] Cung cấp trọn bộ hàm CRUD cho Cán bộ, Nhiệm vụ, Chỉ tiêu, Văn bản RAG và Khóa chống trùng Zalo (`acquire_remind_lock`).
- [ ] **1.2. Xây dựng `scripts/seed_database.py` (Chuẩn hóa dữ liệu theo Đề án 03-ĐA/ĐU & các báo cáo thực tế):**
  - [ ] **Nạp Thường trực & Lãnh đạo chủ chốt:**
    - Đ/c **Vũ Thị Thuỳ Trang** — Bí thư Đảng uỷ, Chủ tịch HĐND xã, Trưởng BCĐ 57 (`CB-TTDU-01`).
    - Đ/c **Nguyễn Xuân Hoàng** — Phó Bí thư Thường trực Đảng uỷ, Chủ nhiệm UBKT Đảng uỷ (`CB-TTDU-02`).
    - Đ/c **Trương Minh Vũ** — Phó Bí thư Đảng uỷ, Chủ tịch UBND xã (`CB-UBND-01`).
    - Đ/c **Ngô Hoàng Việt** — Phó Chánh Văn phòng Đảng uỷ (`CB-VPDU-02`).
  - [ ] **Nạp các Cơ quan chuyên môn & Đơn vị:**
    - Khối Đảng (03 cơ quan): Văn phòng Đảng uỷ (`VPDU`), Ban Xây dựng Đảng (`BXDD`), Cơ quan UBKT Đảng uỷ (`UBKT`).
    - Khối Chính quyền: HĐND xã (Ban Kinh tế - Ngân sách, Ban Văn hóa - Xã hội), UBND xã (Văn phòng HĐND & UBND, Phòng Kinh tế, Phòng Văn hóa - Xã hội, Trung tâm Phục vụ hành chính công, Ban Chỉ huy Quân sự xã, Công an xã, Trung tâm Dịch vụ nông nghiệp / Sự nghiệp công, Trạm Y tế).
    - Khối Mặt trận & Đoàn thể: Cơ quan UBMTTQVN xã (Hội Nông dân, Hội Phụ nữ, Hội Cựu chiến binh, Đoàn Thanh niên).
    - Khối Chi bộ trực thuộc: **08 Chi bộ thôn chính thức** (Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng), **03 Chi bộ trường học** (Trường Mầm non Công Hải, Trường Tiểu học Công Hải, Trường THCS Hùng Vương) và các chi bộ cơ quan/LLVT (Tổng số **21 chi bộ trực thuộc**, **382 đảng viên**).
  - [ ] **Nạp Hệ thống Chỉ tiêu (`so_tieu_chi`):** Nạp 20 chỉ tiêu Nghị quyết Đại hội Đảng bộ xã khóa I (`01-NQ/ĐH`) và 19 chỉ tiêu Chuyển đổi số NQ57 từ Phụ lục 2 Báo cáo `141-BC/ĐU`.
  - [ ] **Nạp Sổ Nhiệm vụ ban đầu (`so_nhiem_vu`):** Đồng bộ từ `so_ke_hoach_chi_dao.json`, 02 file Excel phân công CĐS và các nhiệm vụ Quý II/2026 trong Chương trình `67-CTr/ĐU`, Công văn `708-CV/ĐU` (hạn 15/8/2026).
- [ ] **1.3. Giữ tương thích ngược cho `server/plan_registry.py`:**
  - [ ] Chuyển các hàm trong `plan_registry.py` sang gọi `db_service.py` để các workflow hiện tại chạy thông suốt.

---

### GIAI ĐOẠN 2: Xây dựng Đường ống Nạp Văn bản & Hybrid RAG (`rag_service.py`)
> [!WARNING]
> **LƯU Ý ĐIỂM NGHẼN & TẠM DỪNG CHUYỂN ĐỔI .MD HÀNG LOẠT:**
> Qua thực nghiệm trên kho 16 Nghị quyết, hệ thống **chưa có phương án tối ưu** để bóc tách Số hiệu và Ngày tháng khi người dùng ký số điện tử (2 trường này bị khuyết trên bản Word gốc và bị đẩy rớt xuống đáy trang khi convert sang Markdown). Đồng thời xảy ra hiện tượng dính từ (kerning font) làm hỏng ngữ nghĩa chunking.
> **Hiện trạng:** Tạm dừng quy trình chuyển đổi tự động hàng loạt kho văn bản sang `.md` để chia chunk; bảo toàn nguyên trạng kho văn bản gốc (`.pdf`, `.docx`) trong khi tiếp tục nghiên cứu cơ chế bóc tách tọa độ lớp chữ ký số.

- [ ] **2.1. Nâng cấp `scripts/doc_reader.py` & Xây dựng `server/services/rag_service.py`:**
  - [ ] Tích hợp **Secret Gatekeeper**: Từ chối nạp văn bản có dấu `MẬT`, `TỐI MẬT`, `TUYỆT MẬT` (tuân thủ Quyết định `37-QĐ/ĐU` và Nghị định `63/2026/NĐ-CP`).
  - [ ] Tích hợp **Dual Filename Parser**: Tự động bóc tách cả 2 chuẩn tên file: dạng mã E-Office (`A32.65-...`) và dạng tiếng Việt rút gọn chuẩn `AGENTS.md` (`CV triển khai NQ 19 TU...`, `BC tuần 42 VPĐU...`).
  - [ ] Tích hợp **OCR & Stamp Cleaner**: Xóa nhiễu chữ ký số/con dấu đỏ, chuẩn hóa Unicode NFC và chính tả Khối Đảng (`uỷ`, `oà`).
  - [ ] Tích hợp **Sub-Document & Table Parser**: Tách riêng phần báo cáo tập thể, báo cáo cá nhân từng lãnh đạo và chuyển đổi từng dòng bảng Phụ lục thành câu văn hoàn chỉnh có tiêu đề cột (kèm fallback block Markdown).
- [ ] **2.2. Xây dựng Bộ Trích xuất Đồ thị Liên kết (`Citation Graph Builder`):**
  - [ ] Tự động dùng Regex quét các cụm *"Thực hiện..."*, *"Căn cứ..."*, *"Thay thế..."*, *"Điều chỉnh, bổ sung..."* để điền vào bảng `van_ban_lien_ket` và tự động đánh dấu `BI_THAY_THE` cho văn bản cũ.
  - [ ] Tự động đọc các **Bảng Phụ lục thống kê văn bản** (như Phụ lục 1, 2 của `140-BC/ĐU` và Phụ lục 1 của `141-BC/ĐU`) để tạo bản ghi giữ chỗ (`Placeholder Metadata`) cho toàn bộ các văn bản được liệt kê trong bảng dù file gốc chưa được tải lên.
- [ ] **2.3. Xây dựng Hàm Truy xuất `retrieve_hybrid_context(query, workflow_type)`:**
  - [ ] Thực thi thuật toán kết hợp FTS5 BM25 + Python In-Memory Vector Cosine Rerank + Đồ thị liên kết theo đúng công thức **Giỏ Ngữ Cảnh 2 - 4 - 2**.
- [ ] **2.4. Viết Script Đánh chỉ mục Hàng loạt (`scripts/index_all_documents.py`):**
  - [ ] Quét toàn bộ thư mục `van_ban_den/`, `van_ban_du_thao/`, `references/` (hỗ trợ `.pdf`, `.docx`, `.doc`, `.xlsx`, `.md`), có cơ chế xử lý ngoại lệ khi thiếu file.

---

### GIAI ĐOẠN 3: Tự động Bóc tách "5 Rõ", Khử Trùng Lặp & Tích hợp 4 Workflows
- [ ] **3.1. Bóc tách Nhiệm vụ Tự động kèm Khử Trùng Lặp (`server/chat_engine.py`):**
  - [ ] Khi Cán bộ bấm "Duyệt" văn bản ở WF2 (Kết luận), WF3 (Công văn giao việc / Kế hoạch / Chương trình công tác), AI trích xuất danh sách nhiệm vụ JSON.
  - [ ] Kiểm tra `task_fingerprint`: Nếu nhiệm vụ đã tồn tại trong tháng trước (trượt tiến độ sang tháng này như trong `42, 48, 55-CTr/ĐU`), hệ thống cập nhật lùi `deadline_date` và ghi lịch sử thay vì tạo bản ghi trùng lặp.
- [ ] **3.2. Nâng cấp 4 Workflows sử dụng Kho Tri thức Hybrid RAG & Sổ Nhiệm vụ:**
  - [ ] **WF1 (`wf1_synthesizer.py` - Tổng hợp Báo cáo):** Tự động lấy nhiệm vụ đã hoàn thành/đang làm từ `so_nhiem_vu` + số liệu KPI từ `so_tieu_chi` + các báo cáo liên quan từ `rag_service.py`.
  - [ ] **WF2 & WF3 (`wf2_conclusions.py`, `wf3_dispatch.py`):** Tự động tra cứu văn bản chỉ đạo cấp trên (Tỉnh uỷ, BCĐ 57) trong kho RAG để trích dẫn chính xác vào phần *"Thực hiện..."* và phân công đúng chức năng nhiệm vụ theo Quyết định `01, 02, 03-QĐ/ĐU`.
  - [ ] **WF4 (`wf4_appraisal.py` - Thẩm định Văn bản):** Đối chiếu dự thảo với các Quy chế làm việc hiện hành (`01-QC/ĐU`, `116/QĐ-UBND`), phát hiện ngay nếu dự thảo trích dẫn văn bản đã hết hiệu lực (VD: trích dẫn nhầm `43/QĐ-UBND` hoặc `08-TB/ĐU`) hoặc lệch số liệu so với Báo cáo gần nhất.

---

### GIAI ĐOẠN 4: Bộ Hẹn Giờ Tự Động & Tương tác Zalo 2 Chiều (`scheduler_service.py`)
- [ ] **4.1. Xây dựng `server/services/scheduler_service.py`:**
  - [ ] Sử dụng `AsyncIOScheduler` kèm cơ chế **Khởi động bù (`catch_up_missed_jobs`)** khi máy tính văn phòng bật muộn sau 07h30 sáng.
  - [ ] Cơ chế **Gom nhóm thông báo (`Digest Reminder`)**: Gom tất cả đầu việc sắp đến hạn/quá hạn của 01 cơ quan hoặc cá nhân thành 01 tin nhắn Zalo duy nhất trong ngày.
- [ ] **4.2. Thiết lập Ma trận Lịch Hẹn Giờ Đặc Thù của Đảng uỷ xã Công Hải:**
  - [ ] **07h30 Hàng ngày:** Nhắc các nhiệm vụ đến hạn hôm nay & ngày mai (VD: Nhắc Ban Xây dựng Đảng trình Kế hoạch tuyên truyền KH 90 trước ngày 15/8 theo `708-CV/ĐU`).
  - [ ] **16h30 Hàng ngày:** Cảnh báo nhiệm vụ quá hạn chưa báo cáo cho Chánh Văn phòng & Thường trực Đảng uỷ.
  - [ ] **08h00 Thứ Sáu:** Đôn đốc các cơ quan và **08 thôn** gửi Báo cáo tuần trước 11h00.
  - [ ] **14h00 Thứ Sáu:** Tự động chạy WF1 tạo bản nháp Báo cáo tuần gửi Chánh Văn phòng.
  - [ ] **08h00 Ngày 01 hàng tháng:** Nhắc **08 Chi bộ thôn** và các chi bộ trực thuộc chuẩn bị sinh hoạt chi bộ định kỳ ngày 03.
  - [ ] **08h00 Ngày 23 hàng tháng:** Nhắc Bộ phận chuyên trách CĐS cập nhật số liệu lên hệ thống `theodoinq.dcs.vn` và rà soát `pakn.nq57.vn` trước hạn ngày 25 hàng tháng (theo `141-BC/ĐU`).
- [ ] **4.3. Nâng cấp Webhook Zalo (`server/routers/zalo_webhook.py`):**
  - [ ] Hỗ trợ tra cứu nhanh: *"Việc của tôi"*, *"Việc quá hạn"*, *"Xong NV-2026-xxx"*, và hỏi đáp trực tiếp với kho 1.000+ văn bản RAG ngay trên Zalo.

---

### GIAI ĐOẠN 5: Giao diện Quản trị Web 05 Tab (`index.html`, `style.css`, `app.js`)
- [ ] **5.1. Xây dựng hệ thống RESTful API trong `server/app.py`:**
  - [ ] Nhóm API Nhiệm vụ: `/api/tasks` (GET, POST, PUT, DELETE) & `/api/tasks/export-excel`.
  - [ ] Nhóm API Kho Văn bản RAG: `/api/documents` (Tìm kiếm Hybrid, Xem chi tiết văn bản & mạng lưới văn bản liên quan, Upload văn bản mới tự động bóc tách).
  - [ ] Nhóm API Chỉ tiêu KPI: `/api/kpis` (GET, PUT cập nhật tiến độ).
  - [ ] Nhóm API Danh bạ & Hẹn giờ: `/api/directory` & `/api/scheduler/run-now`.
- [ ] **5.2. Thiết kế 05 Tab Chuyên nghiệp trên Topbar Giao diện Web:**
  - [ ] **Tab 1 `[💬 Trợ lý Soạn thảo]`:** Khung chat AI & 4 Workflows hiện tại, bổ sung hiển thị thẻ trích dẫn nguồn RAG bên dưới câu trả lời.
  - [ ] **Tab 2 `[📋 Sổ Nhiệm Vụ]`:** Quản lý công việc theo 2 chế độ **Kanban 3 cột** và **Bảng dữ liệu**, lọc theo Cơ quan (VPĐU, BXĐĐ, UBKT, UBND, MTTQ, 08 thôn), lọc theo Cấp trình (Thường trực, BTV, BCH), xuất Excel phục vụ họp giao ban.
  - [ ] **Tab 3 `[📚 Kho Văn Bản & Hồ Sơ RAG]`:** Tra cứu siêu tốc 1.000+ văn bản theo Số hiệu, Chuyên đề (`Chính quyền 2 cấp`, `Nghị quyết 57`, `Phát triển Đảng`...), hiển thị nhãn trạng thái (`Còn hiệu lực` / `Bị thay thế bởi...`) và sơ đồ các văn bản liên quan.
  - [ ] **Tab 4 `[🎯 Giám sát Chỉ tiêu]`:** Trực quan hóa 20 chỉ tiêu Nghị quyết Đại hội & 19 chỉ tiêu NQ57 bằng thanh tiến độ phần trăm đổi màu tự động.
  - [ ] **Tab 5 `[👥 Danh Bạ Hệ Thống]`:** Quản lý cán bộ các phòng, ban, 08 thôn, 21 chi bộ trực thuộc và cấu hình Zalo Chat ID.

---

## VI. TIÊU CHÍ NGHIỆM THU BẮT BUỘC DÀNH CHO ĐỘI THỰC THI (DEFINITION OF DONE)

1. **Nghiệm thu Chống Trùng Số Hiệu:** Khi hỏi *"Quy định số 01-QĐ/ĐU quy định nội dung gì?"*, hệ thống phải liệt kê rõ cả 3 văn bản (`01-QĐ/ĐU ngày 10/7/2025` về Văn phòng Đảng uỷ, `01-QĐ/ĐU ngày 27/8/2025` về giải quyết chế độ, và `01-QĐ/ĐU ngày 24/11/2025` về Ban Chỉ đạo 57) chứ không được ghi đè mất văn bản.
2. **Nghiệm thu Hiệu Lực Thay Thế:** Khi hỏi *"Quy chế làm việc hiện hành của UBND xã Công Hải là văn bản nào?"*, hệ thống phải trả lời là **Quyết định số `116/QĐ-UBND` ngày 05/02/2026** (đã thay thế Quyết định `43/QĐ-UBND` ngày 01/7/2025).
3. **Nghiệm thu Phân tách Văn bản Con:** Khi hỏi *"Đồng chí Nguyễn Xuân Hoàng phụ trách những lĩnh vực gì và tự đánh giá hạn chế như thế nào?"*, hệ thống chỉ trích xuất đúng phần B (Trang 21–24 của `140-BC/ĐU`), tuyệt đối không lấy nhầm phần tự kiểm điểm của đồng chí Trương Minh Vũ hay đồng chí Vũ Thị Thuỳ Trang.
4. **Nghiệm thu Bóc tách Giao việc 5 Rõ:** Khi nạp Công văn `708-CV/ĐU ngày 04/8/2026`, hệ thống phải tự động tạo nhiệm vụ: *Cơ quan chủ trì: Ban Xây dựng Đảng | Nội dung: Tham mưu Kế hoạch tuyên truyền, triển khai KH 90-KH/TU về Phong trào Bình dân học vụ số | Hạn chót: `2026-08-15`*.
5. **Nghiệm thu Chuẩn hóa 08 Thôn & Khối Đảng:** Kiểm tra toàn bộ giao diện Web, Zalo và SQLite: Chỉ hiển thị đúng 08 thôn chính thức theo Đề án 03-ĐA/ĐU, 21 chi bộ trực thuộc (382 đảng viên); toàn bộ văn bản và nhãn dữ liệu hiển thị đúng chính tả Khối Đảng (`uỷ`, `oà`).