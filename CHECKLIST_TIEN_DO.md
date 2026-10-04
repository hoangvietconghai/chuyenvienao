# BẢNG CHECKLIST TIẾN ĐỘ DỰ ÁN CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI
*(Hệ thống Tham mưu Tổng hợp Tự động hoá — Vận hành Local với DeepSeek API)*

> **Phiên bản:** v2.0  
> **Cập nhật lần cuối:** 03/10/2026  
> **Nguyên tắc cốt lõi:**
> - Triển khai Local trước, sẵn sàng đóng gói lên Server sau.
> - Tạm thời **bỏ Sổ công việc, nhắc việc và nhập giọng nói** để tập trung tuyệt đối vào 4 nghiệp vụ cốt lõi và giao diện giao tiếp.
> - Sử dụng mô hình **DeepSeek** (chi phí tiết kiệm) kết hợp **Bộ Prompt Chuẩn hoá Chuyên sâu** (System Rules + Few-Shot + JSON Schema) để đảm bảo chất lượng tham mưu tương đương chuyên viên cấp uỷ.
> - **Human-in-the-Loop (BẮT BUỘC):** Tuyệt đối tôn trọng nội dung, số liệu của cơ quan chuyên môn; phát hiện sai sót thì dừng lại báo cáo qua giao diện để cán bộ duyệt trước khi tiếp tục.

---

## I. TỔNG QUAN TIẾN ĐỘ THEO CÁC HẠNG MỤC

| Hạng mục | Tình trạng | Tiến độ | Ghi chú |
| :--- | :---: | :---: | :--- |
| **1. Cấu hình Môi trường & Đọc văn bản đa định dạng** | [x] Hoàn thành | 100% | PyMuPDF (PDF), python-docx (DOCX), OLE/DOC, TXT |
| **2. AI Connector & Hệ thống Prompt DeepSeek Chuyên sâu** | [x] Hoàn thành | 100% | System Guardrails + 4 Prompts nghiệp vụ (Strict JSON) |
| **3. Router Phân luồng & Bộ điều phối Chat Engine** | [x] Hoàn thành | 100% | Phân loại intent câu lệnh, tự động chọn và kích hoạt 4 workflow |
| **4. Bộ 4 Workflow Nghiệp vụ Cốt lõi** | [x] Hoàn thành | 100% | WF1 (BC Tuần), WF2 (TBKL), WF3 (Giao việc), WF4 (Thẩm định) |
| **5. FastAPI Backend Server & Chat API** | [x] Hoàn thành | 100% | `/api/chat`, `/api/chat/upload`, `/api/chat/reset`, streaming preview |
| **6. Giao diện Chat Trực quan kiểu Gemini (Frontend)** | [x] Hoàn thành | 100% | Khung chat đơn giản, đính kèm tệp 📎, thẻ xem trước văn bản A4 |
| **7. Khởi động 1-Click & Kiểm thử Tích hợp** | [x] Hoàn thành | 100% | `run.py`, `start_local.bat`, test end-to-end 100% PASS |

---

## II. CHECKLIST CHI TIẾT TỪNG ĐẦU VIỆC (TASK-BY-TASK)

### Hạng mục 1: Môi trường & Trích xuất Văn bản
- [x] **1.1. Cập nhật `requirements.txt`**: Khai báo `python-docx`, `pymupdf`, `fastapi`, `uvicorn`, `httpx`, `python-dotenv`, `python-multipart`.
- [x] **1.2. Tạo file cấu hình `.env.example` & `.env`**: Khai báo `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL=https://api.deepseek.com`, model `deepseek-chat`, cổng `PORT=8000`.
- [x] **1.3. Xây dựng module `scripts/doc_reader.py`**:
  - Đọc PDF bằng `pymupdf` (fitz), giữ cấu trúc đoạn văn, số thứ tự.
  - Đọc DOCX bằng `python-docx`, bóc tách các paragraph và table.
  - Hỗ trợ DOC cũ (olefile/antiword/pywin32) và TXT utf-8.
  - Tự động bóc trích số hiệu, trích yếu, cơ quan ban hành, ngày tháng sơ bộ.
- [x] **1.4. Viết bài test `scripts/test_doc_reader.py`**: Kiểm tra đọc các định dạng và trích xuất text sạch.

### Hạng mục 2: AI Connector & Hệ thống Prompt DeepSeek
- [x] **2.1. Module `server/config.py`**: Quản trị cấu hình hệ thống, đường dẫn kho văn bản, cấu hình DeepSeek API.
- [x] **2.2. Module `server/ai_connector.py`**:
  - Giao tiếp chuẩn OpenAI-compatible format với DeepSeek endpoint (`https://api.deepseek.com/chat/completions`).
  - Hỗ trợ mô hình `deepseek-chat` (v3) và `deepseek-reasoner` (R1).
  - Tự động bóc tách và sửa lỗi cú pháp JSON (loại bỏ markdown wrap ` ```json...``` `, sửa trailing comma, fix lỗi escape).
  - Cơ chế retry tự động khi mạng chập chờn.
- [x] **2.3. Thiết kế Master System Prompt (`server/prompts/system_base.py`)**:
  - Quy tắc thể thức Hướng dẫn 05-HD/VPTW 2026.
  - Quy tắc mô hình 3 cấp (Trung ương -> Tỉnh Khánh Hoà -> Xã Công Hải; TUYỆT ĐỐI không có huyện Thuận Bắc).
  - Quy tắc chính tả khối Đảng (`oà`, `uỷ`, `uý`), ngày tháng dạng số `dd/mm/yyyy`.
  - Quy tắc An toàn số liệu: TUYỆT ĐỐI giữ nguyên số liệu, tên cơ quan, sự kiện; nếu có bất thường thì lập danh sách cảnh báo `canh_bao_so_lieu` để hỏi cán bộ.
- [x] **2.4. Prompt WF1: Tổng hợp Báo cáo Tuần (`server/prompts/wf1_tong_hop_bao_cao.py`)**:
  - Đọc gộp báo cáo từ các ngành: UBND xã, Ban Xây dựng Đảng, UBKT, MTTQ & đoàn thể.
  - Tổng hợp thành bố cục 4 mảng: (I) Xây dựng Đảng & HTCT, (II) KT-XH, Ngân sách, (III) QP-AN, TTATXH, (IV) Đề xuất kiến nghị & Công tác trọng tâm tuần tới.
  - Bắt lỗi số liệu mâu thuẫn giữa các cơ quan.
- [x] **2.5. Prompt WF2: Thông báo Kết luận Họp Thường trực (`server/prompts/wf2_thong_bao_ket_luan.py`)**:
  - Đọc biên bản/ghi chép cuộc họp tuần hoặc phiên làm việc của Thường trực Đảng uỷ.
  - Bóc tách theo nguyên tắc 5 Rõ (Rõ cơ quan chủ trì, phối hợp, nội dung, mốc thời gian dd/mm/yyyy, chế độ báo cáo).
  - Định dạng chuẩn Thông báo kết luận (-TB/ĐU).
- [x] **2.6. Prompt WF3: Văn bản đến -> Giao việc (`server/prompts/wf3_giao_viec.py`)**:
  - Đọc văn bản chỉ đạo của Tỉnh uỷ / UBND tỉnh.
  - Dynamic Routing: Phân đúng thẩm quyền cho 5 khối cơ quan xã (UBND, UBKT, BXDĐ, MTTQ, VPĐU).
  - Soạn thảo Công văn giao việc (-CV/ĐU) với thời hạn cụ thể (mặc định 10 ngày nếu cấp trên không ghi rõ).
- [x] **2.7. Prompt WF4: Thẩm định 2 Tầng (`server/prompts/wf4_tham_dinh.py`)**:
  - Tầng 1: Thể thức kỹ thuật -> tự động chuẩn hoá vào dự thảo.
  - Tầng 2: Nội dung & số liệu chuyên môn -> TUYỆT ĐỐI KHÔNG TỰ SỬA, xuất danh sách câu hỏi xác nhận cho cán bộ.
  - Tự động nhận diện thể loại văn bản để tạo: Báo cáo Thẩm định (-BC/VPĐU) + Công văn lấy ý kiến BTV kèm Phiếu xin ý kiến (nếu là Kế hoạch/Nghị quyết).

### Hạng mục 3: Phân Luồng Văn Bản Đến (Router)
- [x] **3.1. Module `server/router.py`**:
  - Nhận file upload, tự động phân tích tiêu đề và nội dung ban đầu.
  - Tự động di chuyển/sao chép file vào đúng cấu trúc thư mục `van_ban_den/2026/`:
    * `cap_tren/`: Văn bản Tỉnh uỷ, UBND tỉnh.
    * `du_thao_co_quan/`: Dự thảo từ UBND xã, BXDĐ, UBKT, MTTQ.
    * `bao_cao_co_so/`: Báo cáo tuần/tháng từ các ngành.
    * `bien_ban_hop/`: Ghi chép, biên bản họp Thường trực, BTV.
  - Trả về gợi ý workflow phù hợp nhất cho giao diện web.

### Hạng mục 4: Các Module Thực Thi Workflow
- [x] **4.1. Module WF1 (`server/workflows/wf1_synthesizer.py`)**: Điều phối DeepSeek tổng hợp báo cáo và gọi `PartyDocumentBuilder` xuất file Word `-BC/VPĐU`.
- [x] **4.2. Module WF2 (`server/workflows/wf2_conclusions.py`)**: Điều phối bóc tách biên bản và xuất file Word `-TB/ĐU`.
- [x] **4.3. Module WF3 (`server/workflows/wf3_dispatch.py`)**: Điều phối phân tích văn bản cấp trên và xuất file Word `-CV/ĐU`.
- [x] **4.4. Module WF4 (`server/workflows/wf4_appraisal.py`)**: Điều phối thẩm định 2 tầng, sinh Báo cáo Thẩm định và trọn bộ hồ sơ xin ý kiến BTV.

### Hạng mục 5: Backend Server (FastAPI)
- [x] **5.1. Module `server/app.py`**:
  - Khởi tạo FastAPI app với CORS, Static Files mounting.
  - Endpoint `GET /api/status`: Kiểm tra trạng thái server và DeepSeek API key.
  - Endpoint `POST /api/upload`: Upload file, trích xuất text, router phân loại, gợi ý workflow.
  - Endpoint `POST /api/workflow/{wf_name}/analyze`: Gửi nội dung sang DeepSeek để phân tích, trả về kết quả dự thảo & danh mục cảnh báo số liệu.
  - Endpoint `POST /api/workflow/{wf_name}/generate`: Nhận dữ liệu đã qua xác nhận của cán bộ -> gọi engine xuất file Word `.docx`.
  - Endpoint `GET /api/documents`: Lấy danh sách văn bản đến và văn bản dự thảo đã xuất.
  - Endpoint `GET /api/download/{folder}/{filename}`: Tải file Word đã sinh.

### Hạng mục 6: Giao Diện Web Trực Quan (Frontend)
- [x] **6.1. File `server/static/index.html`**:
  - Thiết kế bố cục chuyên nghiệp theo chuẩn Văn phòng Đảng:
    * Thanh tiêu đề (Header): Quốc huy/Biểu tượng cờ Đảng, tên cơ quan "ĐẢNG BỘ XÃ CÔNG HẢI - VĂN PHÒNG ĐẢNG UỶ", chỉ báo kết nối DeepSeek.
    * Cột trái (Sidebar): 4 Tab nghiệp vụ (WF1: Báo cáo tuần, WF2: Kết luận họp, WF3: Giao việc, WF4: Thẩm định) + Danh sách văn bản gần đây.
    * Khu vực trung tâm: Khung trò chuyện/Lệnh tương tác + Khu vực Drag-and-Drop tải file + Thẻ trạng thái phân tích.
    * Cột phải: Khung Thẩm định & Xác nhận Human-in-the-Loop (hiển thị rõ các cảnh báo sai sót/mâu thuẫn số liệu để cán bộ bấm [Chấp thuận] hoặc [Yêu cầu chỉnh sửa]) + Khung xem trước văn bản & nút [Xuất file Word].
- [x] **6.2. File `server/static/style.css`**:
  - Tông màu sang trọng, trang nghiêm: Đỏ cờ Đảng (#B91C1C / #991B1B), Vàng kim (#D97706 / #F59E0B), Nền Slate (#0F172A / #1E293B / #F8FAFC), Typography Inter/Times New Roman.
  - Thiết kế Responsive mượt mà, hiệu ứng chuyển động tinh tế, modal popup rõ ràng.
- [x] **6.3. File `server/static/app.js`**:
  - Quản lý logic tải file, gọi API phân tích DeepSeek, render bảng phân tích 5 Rõ / Báo cáo tuần.
  - Quản lý hộp thoại xác nhận khi có cảnh báo số liệu bất thường.
  - Tải file Word về máy chỉ với 1 cú click chuột.

### Hạng mục 7: Kiểm Thử & Chuyển Giao
- [x] **7.1. File `scripts/test_system_integration.py`**: Chạy thử luồng xử lý hoàn chỉnh từ file văn bản đến xuất ra file Word.
- [x] **7.2. Script khởi chạy nhanh `start_local.bat` & `start_local.ps1`**: Cán bộ chỉ cần click đúp chuột là hệ thống tự khởi động server và mở trình duyệt web `http://localhost:8000`.

---

## III. HƯỚNG DẪN KHI BỊ CHẠM QUOTA / TIẾP QUẢN DỰ ÁN

Nếu trong quá trình làm việc, AI trợ lý bị chạm ngưỡng quota hoặc phiên làm việc bị gián đoạn, đồng chí hãy thực hiện tiếp như sau:

1. **Kiểm tra trạng thái tại file này (`CHECKLIST_TIEN_DO.md`)**:
   - Tìm mục đầu tiên có trạng thái `[/] Đang thực hiện` hoặc `[ ] Chưa thực hiện`.
2. **Khởi động server kiểm tra những gì đã xong**:
   ```powershell
   python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload
   ```
   Mở trình duyệt: `http://localhost:8000` để kiểm tra giao diện và API.
3. **Cấu hình DeepSeek API Key**:
   - Mở file `.env` tại thư mục gốc dự án.
   - Điền key: `DEEPSEEK_API_KEY=sk-xxxx`
4. **Yêu cầu AI phiên mới**:
   Chỉ cần gửi lệnh ngắn: *"Đọc file CHECKLIST_TIEN_DO.md và tiếp tục thực hiện mục tiếp theo đang dở dang."*
