---
name: boc-tach-van-ban-rag
description: >-
  Kỹ năng bóc tách, sàng lọc, chuẩn hoá thành tệp Markdown (.md) và nạp vào kho
  Hybrid RAG của Văn phòng Đảng uỷ xã Công Hải. Kích hoạt khi cán bộ yêu cầu:
  bóc tách kho văn bản PDF/Word/scan vào RAG, làm mới hoặc nạp lại kho tri thức
  RAG, chuẩn hoá văn bản Đảng thành kho lưu trữ .md theo cây thư mục
  "Văn bản Đảng uỷ Ban hành 25-30/", hoặc xử lý lô văn bản ban hành của Đảng uỷ.
  Quy định bất biến: chia 1 file = 1 chunk với văn bản <= 20 trang và đúng 2 chunk
  với văn bản > 20 trang; lược bỏ tiêu ngữ/nơi nhận/chữ ký thành 1 dòng định danh
  đầu bài kèm Người ký; khớp nối 4 tầng với Excel Master; sàng lọc bỏ văn bản sự
  vụ/giao việc cũ.
---

# KỸ NĂNG: BÓC TÁCH, CHUẨN HOÁ MARKDOWN & NẠP KHO RAG VĂN BẢN ĐẢNG UỶ

> **Skill Name:** `boc-tach-van-ban-rag`  
> **Kế thừa bắt buộc:** [quy-chuan-nen-tang](../quy-chuan-nen-tang/SKILL.md)  
> **Kho nguồn mặc định:** `references/1. ĐẢNG UỶ BAN HÀNH NHIỆM KỲ 2025-2030 (30-9-2026)/`  
> **Kho Markdown đầu ra:** `references/Văn bản Đảng uỷ Ban hành 25-30/`  
> **Bảng đối chiếu Master:** `data/danh_muc_van_ban_di_master.xlsx`  
> **CSDL đích:** `data/chuyen_vien_ao.db` (`so_van_ban`, `van_ban_chunks`, `van_ban_fts`, `van_ban_lien_ket`)

---

## PHẦN I. NGUYÊN TẮC BẤT BIẾN & AN TOÀN DỮ LIỆU

1. **Chốt chặn Độ mật (Secret Gatekeeper):**
   - Trước khi đọc/bóc tách hoặc đưa lên AI, luôn quét dấu `MẬT`, `TỐI MẬT`, `TUYỆT MẬT` (theo Quyết định `37-QĐ/ĐU` và Nghị định `63/2026/NĐ-CP`).
   - Phát hiện độ mật $\rightarrow$ **dừng ngay, tuyệt đối không lưu vào `.md` công cộng và không nạp vào RAG**, lập tức báo cáo cán bộ.
2. **Bảo vệ dữ liệu khi làm mới RAG (Human-in-the-Loop):**
   - Trước khi xoá sạch dữ liệu RAG cũ trong `data/chuyen_vien_ao.db`, phải **sao lưu tệp DB hiện tại** vào `backups/` và **xác nhận rõ với cán bộ** về phạm vi xoá/nạp.
   - Kiểm tra `.gitignore` để bảo đảm thư mục `references/Văn bản Đảng uỷ Ban hành 25-30/` và `data/*.db` **không bị đẩy nhầm** lên kho Git công khai.
3. **Chính tả & Mô hình 02 cấp:**
   - Chuẩn hoá dấu Khối Đảng: `oà`, `uỷ`, `uý` (*Đảng uỷ*, *Khánh Hoà*, *Uỷ ban*); chuẩn Unicode NFC; sửa `Ð` (`U+00D0`) thành `Đ` (`U+0110`).
   - Ngày tháng trong nội dung và dòng định danh ghi dạng số `dd/mm/yyyy`.
   - Mô hình chính quyền địa phương **02 cấp** (Tỉnh Khánh Hoà $\rightarrow$ Xã Công Hải; **không còn cấp huyện**). Giữ nguyên 100% số liệu gốc trong văn bản, không tự làm tròn hay suy đoán.
4. **Ưu tiên AI đọc & biên tập trực tiếp:**
   - Không chạy công cụ chuyển đổi tự động mù quáng lên hàng loạt PDF (tránh dính từ, rớt số hiệu ký số, gãy bảng biểu).
   - Xử lý **theo từng lô** (theo thể loại hoặc 10–15 tệp/đợt): agent trực tiếp đọc nội dung (với PDF scan thì kết xuất trang ảnh bằng PyMuPDF `fitz` để đọc trọn cả tem ký số đè và bảng biểu), tự tay sàng lọc, biên tập, chia chunk và xuất `.md`; chỉ dùng script Python gọn nhẹ cho khâu giải nén trang ảnh và ghi dữ liệu vào SQLite (và tự động xoá script tạm dùng 1 lần sau khi xong).

---

## PHẦN II. QUY TRÌNH 5 BƯỚC BẮT BUỘC

### Bước 1. Khớp nối 4 Tầng giữa File trên đĩa & Excel Master
Vì tên tệp lưu trên đĩa và cột `File văn bản` trong `data/danh_muc_van_ban_di_master.xlsx` **không giống nhau**, tuyệt đối không so khớp theo tên tệp. Áp dụng tuần tự 4 tầng:

1. **Tầng 1 — Chuẩn hoá `(Số hiệu + Thể loại + Năm)`:**
   - Rút trích `(Cơ quan, Thể loại, Số + hậu tố chữ cái, Năm)` từ tên file; chuẩn hoá `Ð` $\rightarrow$ `Đ`, bỏ khoảng trắng quanh dấu `-`, bỏ số `0` thừa ở đầu (ví dụ `A32.65-ĐU-QÐ-0008-2026` $\rightarrow$ `8-QĐ/ĐU`, năm `2026`).
   - Nếu tên file thiếu mã loại hoặc gõ nhầm (ví dụ `A32.65-ĐU-0150-2026`, `CU`), suy luận thể loại từ tên thư mục cha (`BÁO CÁO` $\rightarrow$ `BC`, `CÔNG VĂN` $\rightarrow$ `CV`).
   - Khớp với cặp **`(Số ký hiệu chuẩn hoá, Năm ban hành)`** trong Excel Master (bắt buộc kèm `Năm` để tránh nhầm `2025` sang `2026`).
2. **Tầng 2 — Khớp theo Trích yếu trang 1:**
   - Với các tệp đặt tên tự do không có mã số (ví dụ `mời dự tập huấn...pdf`), đọc trang đầu để lấy trích yếu/số hiệu rồi đối chiếu với Excel Master.
3. **Tầng 3 — Tự lập hồ sơ trực tiếp từ PDF gốc:**
   - Khoảng ~4–5% tệp trên đĩa không có dòng tương ứng trong Excel Master (hoặc là văn bản lưu trữ/nội bộ riêng). Đọc trực tiếp trang đầu & trang cuối PDF để trích xuất đầy đủ metadata.
4. **Tầng 4 — Quy tắc đối soát nguồn chuẩn:**
   - **Nội dung, thẩm quyền ban hành, danh sách người ký/chức vụ:** lấy từ **văn bản PDF/Word gốc** làm chuẩn.
   - **Số hiệu, Ngày ban hành (khi PDF bị tem ký số VNPT iOffice đè hoặc thiếu):** lấy từ **Excel Master** bổ sung vào cho đầy đủ.
   - Với các tệp nén (`.zip`, `.rar`) hoặc tệp thiếu phần mở rộng: ghi nhận vào danh sách ngoại lệ báo cán bộ trước khi xử lý.

---

### Bước 2. Sàng lọc Giá trị Sử dụng & Phân loại Ngay khi Bóc tách

Đọc nội dung từng tệp và phân loại ngay **3 thuộc tính** (`nhom_vong_doi`, `ma_chuyen_de`, `trang_thai_hieu_luc`) theo bảng quyết định sau:

| Phân loại | Tiêu chí nhận diện | Hành động với `.md` & RAG |
| :--- | :--- | :--- |
| **1. Nền tảng cốt lõi (`CORE_DIRECTIVE`)**<br>*(Trọng số `80–100`)* | `Nghị quyết`, `Quy định`, `Quy chế`, `Đề án`, `Chỉ thị`, `Phương án`; `Quyết định` thành lập tổ chức/BCĐ, phân công nhiệm vụ cấp uỷ, quy chế nội bộ; `Chương trình` công tác toàn khoá/năm/tháng còn hiệu lực. | **BẮT BUỘC** tạo `.md` sạch & nạp toàn văn vào `van_ban_chunks` + `van_ban_fts`. |
| **2. Chuyên đề còn giá trị (`THEMATIC_CASE`)**<br>*(Trọng số `60–80`)* | `Kế hoạch` triển khai còn hiệu lực; `Báo cáo` tổng hợp, định kỳ (tháng/quý/6 tháng/năm/BCĐ 57/Đoàn kiểm tra-giám sát như `140`, `141`, `142-BC/ĐU`...); `Hướng dẫn` chuyên môn; `Kết luận` hội nghị BCH/BTV còn giá trị chỉ đạo; `Công văn` mang tính chỉ đạo/hướng dẫn khung lâu dài. | **NẠP TOÀN VĂN**: tạo `.md` sạch & nạp vào `van_ban_chunks` + `van_ban_fts`. |
| **3. Giao việc cũ / Sự vụ ngắn hạn (`EPHEMERAL_EVENT` / `HET_HAN_SU_VU`)** | Giấy mời họp (`GM` hoặc CV mời họp); Bản sao chuyển tiếp đơn thuần (`BS`); Giấy nghỉ phép/giới thiệu; Công văn đôn đốc/giao việc thời vụ đã qua hạn hoặc đã hoàn thành; Quyết định khen thưởng/kỷ luật/nhân sự sự vụ cá nhân nhỏ lẻ không mang tính quy phạm. | **LOẠI BỎ khỏi kho toàn văn RAG** (không cắt chunk nội dung để tránh làm nhiễu kết quả tìm kiếm). Ghi vào danh mục tổng kết để cán bộ kiểm soát. |
| **4. Văn bản đã bị thay thế (`BI_THAY_THE`)** | Khi phát hiện văn bản mới có cụm *"thay thế..."*, *"bãi bỏ..."*, *"điều chỉnh, bổ sung..."* văn bản trước đó. | Tạo bản ghi liên kết `THAY_THE` / `SUA_DOI_BO_SUNG` vào `van_ban_lien_ket`, đánh dấu `BI_THAY_THE` cho văn bản cũ. |

#### Quy tắc gắn `ma_chuyen_de`
Gán theo 9 chuyên đề hiện có trong bảng `danh_muc_chuyen_de` (hoặc đề xuất tạo chuyên đề mới nếu cần). Chú ý gán dựa trên **ngữ nghĩa thực của văn bản**, tuyệt đối không gán máy móc theo từ đơn rời rạc (*hoạt, động, nâng, chất...*):
- `CDS_DEAN06`: Chuyển đổi số, NQ 57, Đề án 06, BCĐ 57, IOC, Sổ tay ĐVĐT.
- `XD_DANG_CAN_BO`: Tổ chức, cán bộ, đảng viên, chi bộ, tuyên giáo, dân vận.
- `KT_GIAM_SAT`: Kiểm tra, giám sát, kỷ luật Đảng, phòng chống tham nhũng/tiêu cực.
- `KINH_TE_NGAN_SACH`: Kinh tế, tài chính, ngân sách, đầu tư công, NTM.
- `DAT_DAI_MOI_TRUONG`: Đất đai, GPMB, tài nguyên, khoáng sản, môi trường, xây dựng.
- `VAN_HOA_XA_HOI`: Giáo dục, y tế, văn hoá, an sinh, giảm nghèo, dân tộc Raglai, tôn giáo.
- `QUOC_PHONG_AN_NINH`: Quốc phòng, an ninh trật tự, công an, quân sự, PCCC.
- `VAN_PHONG_THI_DUA`: Quy chế làm việc, văn thư lưu trữ, thi đua khen thưởng, tổng hợp chung của Văn phòng Đảng uỷ.
- `CD_DE_AN_DOI_MOI_NANG_CAO_CH`: Đề án đổi mới, nâng cao chất lượng, hiệu quả hoạt động của xã Công Hải.

---

### Bước 3. Quy chuẩn Rút gọn & Làm sạch Nội dung Văn bản

Khi biên tập nội dung sạch (dùng chung cho cả tệp `.md` và `chunk_text` trong RAG):

1. **Loại bỏ hoàn toàn phần Tiêu đề / Tiêu ngữ khuôn mẫu ở đầu trang:**
   - Xoá: `ĐẢNG BỘ TỈNH KHÁNH HOÀ`, `ĐẢNG UỶ XÃ CÔNG HẢI` (hoặc `VĂN PHÒNG`, `BAN CHỈ ĐẠO...`), dấu `*`, `Số ...-.../ĐU`, `ĐẢNG CỘNG SẢN VIỆT NAM`, đường kẻ dưới tiêu ngữ, `Công Hải, ngày ... tháng ... năm ...`, và tên loại văn bản đứng riêng lẻ (`KẾ HOẠCH`, `NGHỊ QUYẾT`...).
2. **Thay thế phần đầu bằng ĐÚNG 1 DÒNG ĐỊNH DANH CHUẨN HOÁ:**
   ```text
   [Thể loại] số [Số hiệu] ngày [dd/mm/yyyy] của [Thẩm quyền/Cơ quan ban hành] về [Trích yếu]. Người ký: [Họ tên].
   ```
   - *Ví dụ chuẩn:*  
     `Kế hoạch số 144-KH/ĐU ngày 13/10/2026 của Ban Thường vụ Đảng uỷ xã về triển khai rà soát, làm sạch, chuẩn hoá, đối soát dữ liệu tổ chức đảng, đảng viên trong Đảng bộ xã Công Hải. Người ký: Nguyễn Xuân Hoàng.`
   - **Thẩm quyền/Cơ quan ban hành** xác định từ khối ký gốc trước khi xoá:
     - `T/M BAN THƯỜNG VỤ` $\rightarrow$ `Ban Thường vụ Đảng uỷ xã Công Hải`
     - `T/M ĐẢNG UỶ` $\rightarrow$ `Ban Chấp hành Đảng bộ xã Công Hải`
     - `PHÓ CHÁNH VĂN PHÒNG` / `CHÁNH VĂN PHÒNG` $\rightarrow$ `Văn phòng Đảng uỷ xã Công Hải`
     - `T/M BAN CHỈ ĐẠO` (`BCĐ57`) $\rightarrow$ `Ban Chỉ đạo 57 Đảng uỷ xã Công Hải`
   - **Nếu văn bản có `Kính gửi:`** (Công văn, Tờ trình): nén thành 1 dòng `Gửi: [Danh sách cơ quan].` đặt ngay dưới dòng định danh.
3. **Loại bỏ hoàn toàn phần `Nơi nhận:` và khối `Chữ ký` cuối văn bản:**
   - Xoá toàn bộ danh sách `Nơi nhận:`, cụm `T/M...`, chức vụ, họ tên ký, chữ `Vũ Thị Thuỳ Trang` / `Nguyễn Xuân Hoàng` lặp lại, và toàn bộ rác đóng dấu/timestamp ký số điện tử (VD: `24-04-2026 15:21:14+07:00`, `CÔNG HAY`, `ĐẢNG CỘNG SẢN VIỆT NAM` đè dấu).
   - **CHỐT BẢO VỆ PHỤ LỤC & VĂN BẢN GHÉP (QUAN TRỌNG):** Chỉ cắt **đoạn từ `Nơi nhận:` đến hết cụm chữ ký của phần đó**. Nếu phía dưới còn có **Phụ lục, Quy định/Quy chế ban hành kèm theo, Danh sách, hoặc Báo cáo kiểm điểm cá nhân** (như `140-BC/ĐU`), **bắt buộc giữ nguyên toàn bộ** phần phía sau và đánh tiêu đề phân tách rõ ràng.
4. **Chuẩn hoá trình bày thân bài:**
   - Bảng biểu chuyển về bảng Markdown chuẩn (`| Cột 1 | Cột 2 |`), không làm rơi tiêu đề cột.
   - Giữ nguyên số hiệu các văn bản được viện dẫn ở phần *Căn cứ* / *Thực hiện* để ghi vào `van_ban_lien_ket`.

---

### Bước 4. Quy tắc Chia Chunk (Ngưỡng 20 Trang)

Áp dụng thống nhất trên **số trang gốc của tệp văn bản**:

1. **Văn bản $\le 20$ trang:**
   - **1 văn bản = 1 chunk duy nhất** (toàn bộ nội dung đã làm sạch ở Bước 3).
   - Đặt đầu chunk bằng dòng định danh chuẩn hoá để AI nắm đủ ngữ cảnh.
2. **Văn bản $> 20$ trang:**
   - **Chia làm đúng 2 chunk** (`Chunk 1/2` và `Chunk 2/2`).
   - Chọn **điểm cắt tự nhiên gần giữa văn bản nhất** (tính theo số trang/số từ): ưu tiên ranh giới giữa các **Phần La Mã lớn**, ranh giới giữa **Báo cáo tập thể và Báo cáo cá nhân**, hoặc ranh giới giữa **Nội dung chính và Phần Phụ lục**.
   - **Tuyệt đối không cắt ngang giữa một bảng biểu hoặc giữa một đoạn văn/điều khoản.**
   - **Chunk 2/2 bắt buộc bắt đầu bằng dòng định danh lặp lại** kèm nhãn tiếp nối:
     `[Thể loại] số [Số hiệu] ngày [dd/mm/yyyy] của [Cơ quan] về "[Trích yếu]". Người ký: [Họ tên]. (Phần 2/2 - Tiếp theo: [Tên phần/Phụ lục])`

---

### Bước 5. Lưu trữ Kho Markdown (`.md`) & Nạp vào SQLite RAG

#### 5.1. Cây thư mục lưu trữ chuẩn
Tạo cây thư mục tại `references/Văn bản Đảng uỷ Ban hành 25-30/` khớp đúng 15 thư mục thể loại của kho nguồn:

```text
references/Văn bản Đảng uỷ Ban hành 25-30/
├── Báo cáo/
├── Chỉ thị/
├── Chương trình/
├── Công văn/
├── Đề án/
├── Hướng dẫn/
├── Kế hoạch/
├── Kết luận/
├── Nghị quyết/
├── Phương án/
├── Quy chế/
├── Quy định/
├── Quyết định/
├── Thông báo/
└── Tờ trình/
```

#### 5.2. Quy tắc đặt tên tệp `.md` thống nhất
Đặt tên đồng bộ chuẩn mã định danh eOffice của Đảng uỷ xã Công Hải (`A32.65`), gọn gàng, sắp xếp thẳng hàng theo số hiệu/năm và dễ tra cứu:

```text
A32.65-[Cơ_quan]-[Thể_loại]-[Số_4_chữ_số]-[Năm] [Trích yếu rút gọn].md
```
- **Quy ước viết:**
  - `A32.65`: Mã định danh đơn vị cố định của Đảng uỷ xã Công Hải.
  - `[Cơ_quan]`: Mã cơ quan ban hành chuẩn (`ĐU` với Đảng uỷ/BTV/TTĐU; `VPĐU` với Văn phòng; `BCĐ57` với Ban Chỉ đạo 57; `UBKTĐU` với UBKT).
  - `[Thể_loại]`: Ký hiệu thể loại chuẩn (`BC`, `CT`, `CTr`, `CV`, `ĐA`, `HD`, `KH`, `KL`, `NQ`, `PA`, `QC`, `QĐi`, `QĐ`, `TB`, `TTr` — dùng chữ `Đ` chuẩn `U+0110`, không dùng `Ð` `U+00D0`).
  - `[Số_4_chữ_số]`: Đệm số hiệu lên đủ **4 chữ số** (ví dụ `0001`, `0069`, `0144`; nếu có hậu tố chữ cái giữ nguyên như `0137a`).
  - `[Năm]`: Năm ban hành gồm 4 chữ số (`2025`, `2026`...).
  - `[Trích yếu rút gọn]`: Tóm tắt nội dung chính bằng tiếng Việt chuẩn Khối Đảng (`oà`, `uỷ`, `uý`), dài tối đa ~60–70 ký tự (viết tắt chuẩn: `ĐV`, `CB`, `CĐS`, `BTV`, `BCH`, `NTM`, `KTGS`), không chứa ký tự cấm của Windows (`\/:*?"<>|`).
  - *Xử lý ngoại lệ trùng số trong cùng năm (ID Collision):* Nếu có 2 văn bản trùng cả mã `A32.65-[Cơ_quan]-[Thể_loại]-[Số]-[Năm]` (như `01-QĐ/ĐU` năm 2025), thêm ngày `(dd-mm)` ngay sau năm để không ghi đè file.
- **Ví dụ tên tệp chuẩn:**
  - `Kế hoạch/A32.65-ĐU-KH-0069-2026 Rà soát làm sạch dữ liệu ĐV.md`
  - `Nghị quyết/A32.65-ĐU-NQ-0001-2025 Nghị quyết Đại hội Đảng bộ xã lần thứ I.md`
  - `Báo cáo/A32.65-ĐU-BC-0140-2026 Phục vụ Đoàn giám sát 327 TU.md`
  - `Quyết định/A32.65-ĐU-QĐ-0001-2025 (10-07) Chức năng nhiệm vụ Văn phòng Đảng uỷ.md`

#### 5.3. Mẫu chuẩn nội dung tệp `.md`

```markdown
---
doc_id: "144-KH/ĐU_2026-10-13_DU"
so_hieu: "144-KH/ĐU"
the_loai: "KH"
co_quan_ban_hanh: "Ban Thường vụ Đảng uỷ xã Công Hải"
ngay_ban_hanh: "13/10/2026"
nguoi_ky: "Nguyễn Xuân Hoàng"
nhom_vong_doi: "THEMATIC_CASE"
ma_chuyen_de: "XD_DANG_CAN_BO"
trang_thai_hieu_luc: "CON_HIEU_LUC"
thay_the_so_hieu: ""
can_cu_lien_ket:
  - "81-KH/TU"
so_trang_goc: 5
so_chunks: 1
nguon_file: "A32.65-ĐU-KH-0144-2026 ..."
---

Kế hoạch số 144-KH/ĐU ngày 13/10/2026 của Ban Thường vụ Đảng uỷ xã Công Hải về "Triển khai rà soát, làm sạch, chuẩn hoá, đối soát dữ liệu tổ chức đảng, đảng viên trong Đảng bộ xã Công Hải". Người ký: Nguyễn Xuân Hoàng.

[Toàn bộ nội dung sạch từ phần I đến hết nội dung văn bản + Phụ lục nếu có, đã bỏ Quốc hiệu, Tiêu ngữ, Nơi nhận và Chữ ký]
```

*Ghi chú với văn bản $> 20$ trang (2 chunks):* Chèn ranh giới rõ ràng trong tệp `.md` để đồng bộ 1-1 vào `van_ban_chunks`:
```markdown
<!-- CHUNK 1/2 | section: Nội dung chính & Đánh giá kết quả -->
...
<!-- CHUNK 2/2 | section: Phụ lục & Báo cáo kiểm điểm cá nhân -->
Báo cáo số 140-BC/ĐU ngày 21/04/2026 của Ban Thường vụ Đảng uỷ xã Công Hải về "...". Người ký: Vũ Thị Thuỳ Trang. (Phần 2/2 - Tiếp theo: Phụ lục & Báo cáo kiểm điểm cá nhân)
...
```

#### 5.4. Nạp vào `data/chuyen_vien_ao.db`
- Ghi từng văn bản đã chọn vào `so_van_ban`, các chunk tương ứng (1 hoặc 2 chunk) vào `van_ban_chunks` và `van_ban_fts`, các căn cứ/thay thế vào `van_ban_lien_ket`.
- Nếu `embedding_service` khả dụng thì sinh luôn vector vào cột `embedding` của `van_ban_chunks`.

---

## PHẦN III. TIÊU CHÍ NGHIỆM THU (QUALITY GATE) TRƯỚC KHI BÁO CÁO XONG

Mỗi lô hoặc toàn đợt bóc tách chỉ được coi là hoàn thành khi đạt đủ 6 tiêu chí sau:

1. **Không lọt tài liệu MẬT:** 100% văn bản có dấu `MẬT` / `TỐI MẬT` / `TUYỆT MẬT` bị chặn và báo cáo riêng.
2. **Sạch rác hành chính:** Không còn dòng `ĐẢNG CỘNG SẢN VIỆT NAM`, `ĐẢNG BỘ TỈNH KHÁNH HOÀ`, `Nơi nhận:`, chữ ký hoặc chuỗi timestamp ký số nằm lẫn trong thân văn bản `.md` và `chunk_text`.
3. **Đủ dòng định danh đầu bài & đúng người ký:** Mỗi tệp `.md` và mỗi chunk đều mở đầu đúng cấu trúc `[Thể loại] số ... ngày dd/mm/yyyy của ... về "...". Người ký: ...`.
4. **Đúng quy tắc trang:** 100% tệp $\le 20$ trang chỉ có **1 chunk**; 100% tệp $> 20$ trang có **đúng 2 chunk** không gãy bảng.
5. **Khớp cây thư mục & đồng bộ DB:** Số lượng tệp `.md` đã duyệt trong `references/Văn bản Đảng uỷ Ban hành 25-30/` khớp 1-1 với số bản ghi toàn văn trong `so_van_ban` và `van_ban_chunks` / `van_ban_fts`.
6. **Báo cáo kiểm kê minh bạch:** Trả cho cán bộ bảng tổng hợp rõ ràng: Tổng tệp đã quét, Số tệp giữ lại nạp RAG (Tầng 1 / Tầng 2), Số tệp loại bỏ (sự vụ/giao việc cũ), Số tệp `BI_THAY_THE`, và Danh sách tệp ngoại lệ/lỗi/nén (`.zip`, `.rar`) nếu có.

