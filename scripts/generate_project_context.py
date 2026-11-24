#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/generate_project_context.py
===================================
Công cụ tổng hợp và đồng bộ ngữ cảnh toàn diện dự án (Master Project Context Synthesizer)
dành cho Hệ thống Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà.

Mục đích:
1. Tổng hợp 100% tri thức dự án (thể chế chính trị, mô hình 2 cấp không còn cấp huyện,
   chính tả Đảng, thể thức HD 05-HD/VPTW, kiến trúc AI Dual-Engine, Streaming SSE,
   Google Search Grounding, SQLite WAL schema, 4 Workflows, hệ thống Skills, VPS Production,
   và sao lưu Google Drive tự động) vào duy nhất một tệp `PROJECT_CONTEXT.md`.
2. Cho phép AI Agent khôi phục toàn bộ ngữ cảnh ngay lập tức trong phiên chat mới
   (Zero-Loss Context Restoration) mà không bị phân mảnh hay quên kiến thức.
3. Đồng bộ song song với `CODEBASE_MAP.md` theo nguyên tắc quản trị dự án bắt buộc.

Chạy:
    python scripts/generate_project_context.py
    python scripts/generate_project_context.py --check
"""

import ast
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
TARGET_FILE = BASE_DIR / "PROJECT_CONTEXT.md"


def get_codebase_stats() -> Dict[str, Any]:
    """Quét nhanh thống kê mã nguồn server và scripts."""
    total_files = 0
    total_lines = 0
    endpoints_count = 0
    files_list = []

    for root_folder in ["server", "scripts"]:
        folder_path = BASE_DIR / root_folder
        if not folder_path.exists():
            continue
        for p in folder_path.rglob("*.py"):
            total_files += 1
            try:
                lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
                total_lines += lines
                rel_path = str(p.relative_to(BASE_DIR)).replace("\\", "/")
                files_list.append((rel_path, lines))
                
                # Đếm nhanh decorator router
                content = p.read_text(encoding="utf-8", errors="ignore")
                endpoints_count += len([l for l in content.splitlines() if "@router." in l or "@app." in l])
            except Exception:
                pass

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "endpoints_count": endpoints_count,
        "files_list": sorted(files_list, key=lambda x: x[0]),
    }


def get_skills_list() -> List[Dict[str, str]]:
    """Liệt kê danh sách skills trong .agents/skills và bóc tách description đầy đủ."""
    skills_dir = BASE_DIR / ".agents" / "skills"
    skills = []
    if skills_dir.exists():
        for skill_folder in sorted(skills_dir.iterdir()):
            if skill_folder.is_dir():
                skill_md = skill_folder / "SKILL.md"
                desc = "Kỹ năng chuyên môn nghiệp vụ Đảng"
                if skill_md.exists():
                    try:
                        content = skill_md.read_text(encoding="utf-8-sig", errors="ignore")
                        lines = content.splitlines()
                        if lines and lines[0].strip() == "---":
                            in_desc = False
                            desc_lines = []
                            for line in lines[1:]:
                                if line.strip() == "---":
                                    break
                                if line.startswith("description:"):
                                    in_desc = True
                                    val = line.replace("description:", "").strip()
                                    if val and val not in (">-", ">", "|", "|-"):
                                        desc_lines.append(val)
                                elif in_desc:
                                    if line.startswith("  "):
                                        desc_lines.append(line.strip())
                                    else:
                                        break
                            if desc_lines:
                                desc = " ".join(desc_lines)
                    except Exception:
                        pass
                skills.append({
                    "name": skill_folder.name,
                    "desc": desc,
                    "path": f".agents/skills/{skill_folder.name}/SKILL.md"
                })
    return skills


def generate_project_context_markdown(stats: Dict[str, Any], skills: List[Dict[str, str]]) -> str:
    """Tạo nội dung tài liệu ngữ cảnh dự án toàn diện PROJECT_CONTEXT.md."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    skills_table_rows = []
    for s in skills:
        skills_table_rows.append(f"| **`{s['name']}`** | {s['desc']} | [`{s['path']}`]({s['path']}) |")
    skills_table = "\n".join(skills_table_rows)

    content = f"""# TÀI LIỆU BỐI CẢNH DỰ ÁN TOÀN DIỆN (PROJECT MASTER CONTEXT DOSSIER)
## HỆ THỐNG CHUYÊN VIÊN ẢO VĂN PHÒNG ĐẢNG UỶ XÃ CÔNG HẢI, TỈNH KHÁNH HOÀ
*(Cập nhật tự động: {now_str} — Mô hình chính quyền địa phương 02 cấp & Thể thức HD 05-HD/VPTW)*

---

> [!IMPORTANT]
> **DÀNH CHO MỌI PHIÊN HỘI THOẠI MỚI (INSTANT ZERO-LOSS CONTEXT RESTORATION):**
> Tệp này tổng hợp 100% bối cảnh chính trị, pháp lý, kiến trúc hệ thống, cơ sở dữ liệu, quy trình chuyên biệt và hướng dẫn vận hành của dự án.
> Khi bắt đầu một phiên chat mới, AI Agent chỉ cần đọc tệp này kết hợp với [`CODEBASE_MAP.md`](file:///e:/Viet%20Design/Chuy%C3%AAn%20vi%C3%AAn%20%E1%BA%A3o/CODEBASE_MAP.md) là có thể **khôi phục toàn bộ ngữ cảnh ngay lập tức mà không bị mất mát thông tin hay ảo giác số liệu**.

---

## 🏛️ PHẦN 1: TÔN CHỈ CHÍNH TRỊ, MÔ HÌNH BỘ MÁY & QUY CHUẨN ĐẢNG

### 1.1. Vị trí Pháp lý & Bộ máy Quản lý
- **Đơn vị chủ quản:** Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà.
- **Mô hình quản trị từ 01/7/2025:**
  - **Chính quyền địa phương 02 cấp:** Cấp tỉnh (tỉnh Khánh Hoà) → Cấp xã (xã Công Hải).
  - **Chính quyền 03 cấp:** Trung ương → Tỉnh → Xã (chữ "địa phương" chỉ dùng cho mô hình 2 cấp Tỉnh - Xã). Đảng bộ xã Công Hải là Đảng bộ cơ sở.
  - **HOÀN TOÀN KHÔNG CÒN CẤP HUYỆN:** Mọi thẩm quyền, báo cáo, liên hệ trực tiếp giữa Xã và Tỉnh uỷ Khánh Hoà / UBND tỉnh Khánh Hoà.
  - **Quy tắc thẩm định khi phát hiện còn cấp huyện:** Chỉ ghi ngắn gọn là **"không còn cấp huyện nữa"**, tuyệt đối không giải thích dài dòng vì cán bộ đã nắm rõ; việc xuất hiện chỉ là sai sót đánh máy (trừ văn bản lịch sử cũ).

### 1.2. Chuẩn Chính tả Khối Đảng & Thể thức Văn bản
- **Quy tắc đặt dấu tiếng Việt:** BẮT BUỘC đặt dấu kiểu mới: **`oà`**, **`uỷ`**, **`uý`** (ví dụ: *Đảng uỷ*, *Ban Thường vụ Tỉnh uỷ*, *kết quả*, *quyền uý*). Tuyệt đối không dùng `òa`, `ủy`, `úy`.
- **Định dạng ngày tháng trong nội dung:** Dạng số `dd/mm/yyyy` (ví dụ: `24/11/2026`). Tuyệt đối không viết rườm rà "ngày... tháng... năm...".
- **Chuẩn thể thức Hướng dẫn số 05-HD/VPTW ngày 12/01/2026:**
  - **Lề trang (Khổ A4 đứng):** Trái 30mm, Phải 15mm, Trên 20mm, Dưới 20mm.
  - **Spacing & Giãn dòng:** Toàn bộ thân bài (đoạn văn, đề mục, gạch đầu dòng, dấu cộng): `Before 6pt`, `After 6pt`, `Line spacing Exactly 18pt`, Font Times New Roman 14pt.
  - **Thụt đầu dòng:** Toàn bộ các đoạn, đề mục (I, II), tiểu mục (1, 2), điểm (a, b), gạch đầu dòng (`- `), dấu cộng (`+ `) **ĐỀU THỤT ĐẦU DÒNG ĐÚNG 1CM (10MM)**.
  - **Khung Header:** Bảng 1 hàng 2 cột ẩn viền. Cỡ chữ 14 cho tất cả các thành phần (chỉ trừ trích yếu công văn cột 1 là cỡ 12 in nghiêng).
  - **Đường kẻ dưới "ĐẢNG CỘNG SẢN VIỆT NAM":** Chiều dài đúng 192pt, nét liền đen dày 0.75pt.
  - **Khối Kính gửi:** Bảng 1 hàng 2 cột ẩn viền (Cột 1 chữ "*Kính gửi:*" in nghiêng canh phải; Cột 2 danh sách cơ quan canh trái). **CHỈ ÁP DỤNG CHO TỜ TRÌNH (-TTr) VÀ CÔNG VĂN (-CV)**; **TUYỆT ĐỐI KHÔNG ĐƯA VÀO BÁO CÁO (-BC)**.
  - **Khung Chữ ký:** Dòng 1 thẩm quyền in hoa đậm (`T/M BAN THƯỜNG VỤ`, `T/M ĐẢNG UỶ`...); Dòng 2 chức vụ in hoa thường (`BÍ THƯ`, `PHÓ BÍ THƯ`...); cách 5 dòng (14pt) đến Họ tên (chữ thường in đậm). Không ghi "VĂN PHÒNG ĐẢNG UỶ" phía trên chức danh.
  - **In đậm chỉ mục:** In đậm cả số và tiêu đề chỉ mục trước dấu `:` (ví dụ: `**1. Thể thức văn bản:**`). Nội dung sau dấu hai chấm là chữ thường không in đậm. Gạch đầu dòng (`- `) và cộng (`+ `) tuyệt đối không in đậm.

### 1.3. Chỉ tiêu Kinh tế - Xã hội Then chốt Xã Công Hải
*(Theo Nghị quyết Đại hội Đảng bộ xã lần thứ I & [tong_quan_xa_cong_hai.md](file:///e:/Viet%20Design/Chuy%C3%AAn%20vi%C3%AAn%20%E1%BA%A3o/references/tong_quan_xa_cong_hai.md))*
- Tốc độ tăng trưởng kinh tế bình quân: **11 - 12%/năm**.
- Thu ngân sách nhà nước trên địa bàn: tăng bình quân **12%/năm**.
- Đến năm 2030: **Hoàn toàn không còn hộ nghèo** trên địa bàn toàn xã.
- Mục tiêu xây dựng nông thôn mới: Đạt chuẩn **Xã Nông thôn mới nâng cao**.
- Cơ cấu tổ chức: Biên chế hành chính - Đảng gồm **72 cán bộ**, 08 thôn, 21 chi bộ trực thuộc.

### 1.4. Bộ 4 Nguyên tắc An toàn Tuyệt đối
1. **Tuyệt đối KHÔNG đụng đến Mật khẩu:** Không đọc, không lưu, không hỏi mật khẩu.
2. **Tuyệt đối KHÔNG tự ý ban hành, gửi đi, ký số, xoá dữ liệu:** Cơ chế Human-in-the-Loop (cán bộ tự duyệt).
3. **Tuyệt đối KHÔNG đưa Bí mật Nhà nước lên AI công cộng.**
4. **Tự động dọn dẹp Script dùng 1 lần:** Xoá ngay các script phát sinh tạm thời sau khi xuất file.

---

## 🤖 PHẦN 2: KIẾN TRÚC TRÍ TUỆ NHÂN TẠO & HYBRID RAG

### 2.1. Động cơ Đa tầng (Dual-Engine AI Failover)
- **Động cơ Chính (Primary Cloud LLM):** Google Gemini (`gemini-3.5-flash-lite`, `gemini-2.5-flash`, `gemini-1.5-pro`). Hỗ trợ cửa sổ ngữ cảnh 1M tokens, tốc độ phản hồi cực nhanh, miễn phí 500 request/ngày.
- **Động cơ Dự phòng (Failover Cloud LLM):** DeepSeek Chat (`deepseek-chat`) và DeepSeek Reasoner (`deepseek-reasoner`) qua OpenAI-compatible API. Tự động kích hoạt khi Gemini gặp lỗi 429 hoặc quá tải.
- **Động cơ Cục bộ (Offline Fallback LLM):** Ollama (`qwen2.5:7b`) chạy qua localhost:11434 trong tình huống mất kết nối mạng Internet.

### 2.2. AI Streaming (Server-Sent Events - SSE)
- **Kiến trúc:** Endpoint `POST /api/chat/stream` phát dữ liệu theo giao thức SSE chunk-by-chunk.
- **Phía Backend:** `server/ai_connector.py` (`_execute_gemini_native_stream`, `_execute_openai_stream`) → `server/chat_engine.py` (`handle_chat_stream`) → Router FastAPI `StreamingResponse(media_type="text/event-stream")`.
- **Phía Frontend:** `server/static/app.js` dùng `ReadableStreamDefaultReader`, giải mã UTF-8 chunk, xử lý sự kiện `data: [DONE]` và render Markdown trực tiếp vào DOM theo thời gian thực.

### 2.3. Tra cứu Internet Tự động (Google Search Grounding)
- **Nguyên lý:** Tích hợp trực tiếp công cụ `google_search` của Google Gemini API Native (`ENABLE_WEB_SEARCH=true`).
- **Ứng dụng:** Tự động tra cứu sự kiện thời sự, thông tin nhân sự lãnh đạo tỉnh mới nhất, văn bản pháp quy mới ban hành khi kho RAG nội bộ chưa kịp cập nhật.
- **Trình bày tinh gọn:** Không hiển thị danh sách link dài chiếm màn hình; chỉ gắn huy hiệu `🌐 Nguồn Internet` gọn gàng ở thanh công cụ tin nhắn kèm tooltip hiển thị nguồn.

### 2.4. True Hybrid RAG (BM25 + Gemini Vector + RRF)
- **Lớp Lexical:** Thuật toán BM25 Okapi phân tích từ khoá, số hiệu văn bản chính xác (`-/.`), không bị nhầm lẫn dấu.
- **Lớp Semantic:** Gemini Embedding (`gemini-embedding-001` / `text-embedding-004`) biến đổi vector BLOB lưu trong SQLite.
- **Dung hợp Điểm số:** Reciprocal Rank Fusion (RRF, tham số $k=60$) kết hợp trọng số thẩm quyền văn bản để xếp hạng đoạn trích chính xác nhất.
- **Quy chuẩn bóc tách RAG (`boc-tach-van-ban-rag`):**
  - Lưu 100% văn bản dạng `.md` trong `references/Văn bản Đảng uỷ Ban hành 25-30/`.
  - Chỉ nạp RAG các văn bản cốt lõi (`CORE_DIRECTIVE`, `THEMATIC_CASE`).
  - Phân đoạn: $\\le 20$ trang = đúng 1 chunk; $> 20$ trang = đúng 2 chunk tự nhiên.

---

## 🗄️ PHẦN 3: THIẾT KẾ CƠ SỞ DỮ LIỆU SQLITE WAL

Hệ thống sử dụng cơ sở dữ liệu SQLite tối ưu chế độ WAL (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) lưu tại `data/chuyen_vien_ao.db` gồm các bảng cốt lõi:

1. **`danh_ba_can_bo`:** Quản lý 72 cán bộ xã, chức vụ, đơn vị, phân quyền (`admin`, `can_bo`), Zalo ID và số điện thoại.
2. **`so_nhiem_vu`:** Quản lý công việc theo nguyên tắc 5 Rõ (Rõ người, việc, tiến độ, kết quả, trách nhiệm), deadline, trạng thái tiến độ.
3. **`lich_su_nhac_nho`:** Nhật ký nhắc việc tự động qua Zalo Bot, chống spam lặp lại.
4. **`so_van_ban`:** Kho văn bản hành chính lưu trữ file_hash, số hiệu, trích yếu, cấp ban hành, vòng đời và hiệu lực.
5. **`van_ban_lien_ket`:** Đồ thị quan hệ căn cứ, thay thế, sửa đổi, huỷ bỏ giữa các văn bản.
6. **`van_ban_chunks`:** Các đoạn văn bản bóc tách kèm vector embedding BLOB và metadata phục vụ RAG.
7. **`van_ban_fts`:** Bảng ảo FTS5 hỗ trợ tìm kiếm full-text tiếng Việt không dấu và có dấu qua tokenizer `unicode61`.
8. **`danh_muc_chuyen_de`:** 08 chuyên đề quản lý trọng tâm của cấp uỷ xã Công Hải.
9. **`xac_thuc_otp`:** Lưu trữ mã OTP đăng nhập 2FA qua số điện thoại Zalo.
10. **`phien_dang_nhap`:** Quản lý Session Tokens đăng nhập bền vững của cán bộ.
11. **`phien_hoi_thoai_state`:** Quản lý trạng thái đính kèm tệp và hội thoại đa luồng.
12. **`nhat_ky_hoi_thoai`:** Lưu trữ lịch sử hỏi đáp đa kênh (Web ChatCHS, Zalo Bot) phục vụ đánh giá và cải tiến.

---

## ⚡ PHẦN 4: 4 QUY TRÌNH CHUYÊN BIỆT & HỆ THỐNG SKILLS

### 4.1. Bốn Quy trình Chuyên biệt Tự động hoá
- **WF1: Tổng hợp Báo cáo Tuần Văn phòng Đảng uỷ (`server/workflows/wf1_synthesizer.py`):** Tiếp nhận báo cáo cơ sở từ các chi bộ/ngành → Phân tích và phát hiện điểm bất thường → Trình cán bộ duyệt → Xuất file Word `-BC/VPĐU`.
- **WF2: Thông báo Kết luận Họp Thường trực Đảng uỷ (`server/workflows/wf2_conclusions.py`):** Tiếp nhận biên bản họp → Bóc tách nhiệm vụ 5 Rõ → Cán bộ kiểm duyệt → Xuất file Word `-TB/ĐU`.
- **WF3: Phân luồng & Giao việc Văn bản Tỉnh uỷ (`server/workflows/wf3_dispatch.py`):** Tiếp nhận văn bản chỉ đạo của Tỉnh uỷ / UBND tỉnh → Bóc tách nhiệm vụ và điều phối tới 5 khối cơ quan cấp xã → Xuất file Word `-CV/ĐU`.
- **WF4: Thẩm định 2 Tầng & Xuất hồ sơ Ban Thường vụ (`server/workflows/wf4_appraisal.py`):** Thẩm định thể thức (Tầng 1) và Thẩm định nội dung/chỉ tiêu Đại hội Đảng bộ (Tầng 2) → Xuất Báo cáo thẩm định + Dự thảo chuẩn hoá + Công văn xin ý kiến BTV.

### 4.2. Danh mục 15 Kỹ năng Nghiệp vụ Đảng (.agents/skills/)
{skills_table}

---

## 🚀 PHẦN 5: MÔI TRƯỜNG TRIỂN KHAI VPS & SAO LƯU GOOGLE DRIVE

### 5.1. Máy chủ Production VPS Ubuntu
- **Địa chỉ IP:** `45.119.82.227` (Cổng 80 HTTP, cổng 8000 Uvicorn).
- **Thư mục cài đặt:** `/opt/chuyenvienao`.
- **Dịch vụ quản trị tiến trình:** Systemd service `chuyenvienao.service`.
- **Reverse Proxy:** Nginx xử lý HTTPS/CORS và điều phối tĩnh / dynamic.

### 5.2. Kịch bản Sao lưu Đêm Tự động (Nightly Offsite Backup)
- **Tập lệnh:** `server/services/backup_service.py` & `scripts/backup_to_gdrive.py`.
- **Cơ chế sao lưu an toàn:** Sử dụng `sqlite3.backup()` trực tiếp trên CSDL đang chạy (không khoá ứng dụng, an toàn tuyệt đối với chế độ WAL).
- **Quy trình nén & Kiểm định:** Nén gzip (`.db.gz`), tính mã băm SHA256 để chống lỗi hỏng dữ liệu.
- **Tải lên Google Drive:** Kết nối qua Google Service Account vào thư mục chỉ định `GDRIVE_BACKUP_FOLDER_ID`.
- **Lập lịch & Tự phục hồi:** Chạy định kỳ lúc 01:00 AM hằng ngày thông qua `scheduler_service.py`. Nếu máy chủ bị tắt vào ban đêm, cơ chế **Catch-up on startup** sẽ tự động phát hiện và sao lưu bù ngay khi khởi động.
- **Chính sách lưu trữ:** Tự động dọn dẹp các bản sao lưu cũ quá 30 ngày trên đám mây.

---

## 📊 PHẦN 6: THỐNG KÊ QUY MÔ MÃ NGUỒN HIỆN TẠI

- **Tổng số tệp mã nguồn Python:** **{stats['total_files']}** tệp
- **Tổng số dòng mã nguồn:** **{stats['total_lines']:,}** dòng
- **Số lượng API Endpoints (FastAPI Routes):** **{stats['endpoints_count']}** endpoints
- **Các thư viện hạt nhân:** FastAPI, Uvicorn, Python-docx, SQLite3, Google-genai, OpenAI SDK, Schedule, Requests, PyCryptodome.

---

## 🔄 PHẦN 7: NGUYÊN TẮC BẮT BUỘC ĐỒNG BỘ SONG SONG (DUAL-MAP SYNCHRONIZATION)

> [!CAUTION]
> **QUY TẮC BẤT BIẾN TOÀN DỰ ÁN DÀNH CHO AI & LẬP TRÌNH VIÊN:**
> Bất kỳ thao tác nào làm **thay đổi, sửa chữa, bổ sung hoặc thay thế** mã nguồn, cấu hình, tính năng, bảng CSDL hoặc API endpoints **BẮT BUỘC** phải thực hiện ngay bước đồng bộ song song cả 2 tệp:
> 1. Cập nhật bản đồ mã nguồn: `python scripts/generate_code_map.py --update-map`
> 2. Cập nhật tài liệu ngữ cảnh dự án: `python scripts/generate_project_context.py`
> 3. Chạy kiểm thử tự động để đảm bảo không phát sinh lỗi hồi quy (regression errors).
>
> **Không có bất kỳ ngoại lệ nào.**

---
*Tài liệu được sinh tự động bởi `scripts/generate_project_context.py`.*
"""
    return content


def update_project_context(check_only: bool = False) -> bool:
    """Tạo hoặc cập nhật tệp PROJECT_CONTEXT.md."""
    print("[*] Đang thu thập thông tin dự án, cấu hình và mã nguồn...")
    stats = get_codebase_stats()
    skills = get_skills_list()
    
    print(f"[✓] Đã phân tích: {stats['total_files']} files | {stats['total_lines']:,} dòng code | {len(skills)} skills")
    
    markdown = generate_project_context_markdown(stats, skills)
    
    if check_only:
        print(f"[✓] Kiểm tra hợp lệ. Dung lượng dự kiến: {len(markdown)} ký tự.")
        return True

    TARGET_FILE.write_text(markdown, encoding="utf-8")
    print(f"[+] Đã tạo / cập nhật thành công: {TARGET_FILE}")
    print(f"    Dung lượng: {len(markdown):,} ký tự | Đường dẫn: file:///{str(TARGET_FILE).replace(chr(92), '/')}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tạo và cập nhật PROJECT_CONTEXT.md")
    parser.add_argument("--check", action="store_true", help="Kiểm tra mà không ghi file")
    args = parser.parse_args()

    success = update_project_context(check_only=args.check)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
