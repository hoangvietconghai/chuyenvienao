#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
server/chat_engine.py
=====================
BỘ ĐIỀU PHỐI HỘI THOẠI — trái tim của giao diện chat.

Luồng xử lý 1 tin nhắn:
  1. Nếu đang có dự thảo chờ duyệt và cán bộ bấm/gõ "Duyệt" -> xuất Word.
  2. Nếu cán bộ bấm/gõ "Huỷ" -> bỏ dự thảo.
  3. Ngược lại: phân loại câu lệnh (DeepSeek, dự phòng bằng từ khoá)
       - wf1/wf2/wf3/wf4 -> chạy nghiệp vụ, tóm tắt kết quả, hiện cảnh báo số liệu,
                            giữ dự thảo ở trạng thái CHỜ DUYỆT (Human-in-the-Loop).
       - chinh_sua       -> sửa dự thảo đang chờ duyệt theo lệnh.
       - tro_chuyen      -> trả lời tự do.

Phiên làm việc lưu trong bộ nhớ (chạy local 1 người dùng).
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from urllib.parse import quote

from scripts.export_docx import export_party_document
from server.ai_connector import default_ai_client
from server.config import BASE_DIR
from server.prompts.chat_mode import CHAT_SYSTEM_PROMPT
from server.prompts.intent_router import get_intent_messages, get_revise_messages
from server.services.knowledge_loader import (
    build_system_knowledge_prompt,
    get_core_rules,
    get_local_knowledge_summary,
)
from server.workflows.wf1_synthesizer import analyze_weekly_reports, generate_weekly_report_docx
from server.workflows.wf2_conclusions import analyze_meeting_notes, generate_meeting_conclusion_docx
from server.workflows.wf3_dispatch import analyze_provincial_directive, generate_dispatch_docx
from server.workflows.wf4_appraisal import analyze_agency_draft, generate_appraisal_documents

from server.logger import get_logger

logger = get_logger("chat_engine")

MAX_INPUT_CHARS = 35000      # Giới hạn độ dài văn bản an toàn cho context window (tránh quá tải CPU)
MAX_CHAT_ATTACH_CHARS = 20000

WORKFLOWS = {
    "wf3_giao_viec": "Tham mưu Công văn giao việc (-CV/ĐU)",
    "wf1_tong_hop_bao_cao": "Tổng hợp Báo cáo tuần (-BC/VPĐU)",
    "wf2_thong_bao_ket_luan": "Thông báo kết luận cuộc họp (-TB/ĐU)",
    "wf4_tham_dinh": "Thẩm định dự thảo & hồ sơ xin ý kiến BTV",
}

CATEGORY_LABELS = {
    "cap_tren": "Văn bản cấp trên",
    "du_thao_co_quan": "Dự thảo của cơ quan chuyên môn",
    "bao_cao_co_so": "Báo cáo của cơ quan, đơn vị",
    "bien_ban_hop": "Biên bản / ghi chép cuộc họp",
}

NEED_INPUT_HINT = {
    "wf3_giao_viec": "văn bản chỉ đạo của Tỉnh uỷ / UBND tỉnh",
    "wf1_tong_hop_bao_cao": "các báo cáo tuần của UBND xã, Ban Xây dựng Đảng, UBKT, MTTQ...",
    "wf2_thong_bao_ket_luan": "ghi chép / biên bản cuộc họp (hoặc dán trực tiếp nội dung kết luận vào khung chat)",
    "wf4_tham_dinh": "dự thảo văn bản do cơ quan chuyên môn gửi",
}

CONFIRM_RE = re.compile(r"^(ok|oke|được|đồng ý|duyệt|xuất|xuất word|xuất file|giữ nguyên|tiếp tục|chốt)\b", re.IGNORECASE)
CANCEL_RE = re.compile(r"^(huỷ|hủy|thôi|bỏ qua|không cần)\b", re.IGNORECASE)

from server.utils.text_processing import normalize_party_doc_type as _normalize_doc_type

SESSION_TTL_SECONDS = 4 * 3600  # 4 giờ
MAX_SESSIONS = 50

SESSIONS: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# QUẢN LÝ PHIÊN
# ==============================================================================

def _cleanup_old_sessions() -> None:
    """Tự động dọn dẹp các session quá hạn để chống rò rỉ RAM."""
    now = datetime.now().timestamp()
    expired = [
        sid for sid, s in SESSIONS.items()
        if now - s.get("last_active", now) > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del SESSIONS[sid]

    # Nếu vẫn vượt quá MAX_SESSIONS, xoá bớt các session cũ nhất
    if len(SESSIONS) > MAX_SESSIONS:
        sorted_sids = sorted(SESSIONS.keys(), key=lambda k: SESSIONS[k].get("last_active", 0))
        for sid in sorted_sids[:(len(SESSIONS) - MAX_SESSIONS)]:
            del SESSIONS[sid]


def _sync_session_to_db(session_id: str, s: Dict[str, Any]) -> None:
    try:
        from server.services import db_service
        db_service.save_chat_session_state(
            session_id=session_id,
            attachments=s.get("attachments", []),
            pending=s.get("pending"),
            awaiting=s.get("awaiting"),
        )
    except Exception as ex:
        logger.warning(f"Lỗi đồng bộ session state vào SQLite: {ex}")


def get_session(session_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    _cleanup_old_sessions()
    now_ts = datetime.now().timestamp()
    if not session_id or session_id not in SESSIONS:
        session_id = session_id or uuid.uuid4().hex
        persisted = None
        if session_id:
            try:
                from server.services import db_service
                persisted = db_service.get_chat_session_state(session_id)
            except Exception:
                persisted = None

        if persisted:
            SESSIONS[session_id] = {
                "history": [],
                "attachments": persisted.get("attachments", []),
                "pending": persisted.get("pending"),
                "awaiting": persisted.get("awaiting"),
                "last_active": now_ts,
            }
        else:
            SESSIONS[session_id] = {
                "history": [],
                "attachments": [],
                "pending": None,
                "awaiting": None,
                "last_active": now_ts,
            }
    else:
        SESSIONS[session_id]["last_active"] = now_ts
        # Đồng bộ từ DB nếu DB có attachments mà memory chưa có (do upload ở worker khác)
        if not SESSIONS[session_id].get("attachments"):
            try:
                from server.services import db_service
                persisted = db_service.get_chat_session_state(session_id)
                if persisted and persisted.get("attachments"):
                    SESSIONS[session_id]["attachments"] = persisted["attachments"]
                    if not SESSIONS[session_id].get("awaiting") and persisted.get("awaiting"):
                        SESSIONS[session_id]["awaiting"] = persisted["awaiting"]
            except Exception:
                pass
    return session_id, SESSIONS[session_id]


def reset_session(session_id: Optional[str], token: Optional[str] = None) -> str:
    saved_auth = None
    if session_id and session_id in SESSIONS:
        old_s = SESSIONS[session_id]
        if old_s.get("authenticated") and old_s.get("can_bo"):
            saved_auth = (True, old_s["can_bo"])
        del SESSIONS[session_id]
        try:
            from server.services import db_service
            db_service.delete_chat_session_state(session_id)
        except Exception:
            pass
    new_id, new_s = get_session(None)
    if saved_auth:
        new_s["authenticated"], new_s["can_bo"] = saved_auth
    elif token:
        try:
            from server.services import db_service
            db_s = db_service.get_auth_session(token)
            if db_s:
                new_s["authenticated"] = True
                new_s["can_bo"] = db_s
        except Exception:
            pass
    return new_id


def clear_session_history(session_id: str, delete_logs_in_db: bool = True) -> bool:
    """Xoá sạch lịch sử tin nhắn, tệp đính kèm và trạng thái đang chờ của phiên."""
    if not session_id:
        return False
    if session_id in SESSIONS:
        s = SESSIONS[session_id]
        s["history"] = []
        s["attachments"] = []
        s["pending"] = None
        s["awaiting"] = None
        _sync_session_to_db(session_id, s)
    else:
        _, s = get_session(session_id)
        s["history"] = []
        s["attachments"] = []
        s["pending"] = None
        s["awaiting"] = None
        _sync_session_to_db(session_id, s)

    if delete_logs_in_db:
        try:
            from server.services import db_service
            db_service.delete_chat_session(session_id)
        except Exception as ex:
            logger.warning(f"Lỗi khi xoá nhật ký phiên {session_id} trong DB: {ex}")

    logger.info(f"Đã xoá sạch lịch sử hội thoại cho phiên: {session_id}")
    return True


def add_attachment(session_id: Optional[str], routing_result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    session_id, s = get_session(session_id)
    att = {
        "id": uuid.uuid4().hex[:10],
        "name": routing_result["file_name"],
        "text": routing_result.get("full_text", ""),
        "category": routing_result.get("category", ""),
        "category_label": CATEGORY_LABELS.get(routing_result.get("category", ""), "Văn bản"),
        "suggested_workflow": routing_result.get("suggested_workflow", ""),
        "saved_path": routing_result.get("saved_path", ""),
        "used": False,
    }
    # Tự động loại bỏ tệp cũ trùng tên trong phiên làm việc để chống tích luỹ nhân bản
    s["attachments"] = [a for a in s["attachments"] if a["name"] != att["name"]]
    s["attachments"].append(att)
    _sync_session_to_db(session_id, s)
    return session_id, att


def remove_attachment(session_id: str, attachment_id: str) -> bool:
    _, s = get_session(session_id)
    before = len(s["attachments"])
    s["attachments"] = [a for a in s["attachments"] if a["id"] != attachment_id]
    _sync_session_to_db(session_id, s)
    return len(s["attachments"]) < before


# ==============================================================================
# TIỆN ÍCH
# ==============================================================================

def _cell(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _download_url(abs_path: str) -> str:
    try:
        rel = Path(abs_path).resolve().relative_to(BASE_DIR.resolve()).as_posix()
    except ValueError:
        rel = abs_path
    return f"/api/download?file_path={quote(rel)}"


def _reply(session: Dict[str, Any], text: str, **extra) -> Dict[str, Any]:
    session["history"].append({"role": "assistant", "content": text[:2000]})
    out = {"reply": text, "actions": [], "files": [], "preview": []}
    out.update(extra)
    return out


DRAFT_SYSTEM_PROMPT = """Bạn là Chuyên viên ảo — Trợ lý AI Tham mưu Tổng hợp, Văn thư và Soạn thảo văn bản chuyên nghiệp của Văn phòng Đảng uỷ xã Công Hải, tỉnh Khánh Hoà (trực thuộc trực tiếp Tỉnh uỷ Khánh Hoà theo mô hình chính quyền địa phương 02 cấp).

Nhiệm vụ: Căn cứ vào yêu cầu chỉ đạo của cán bộ, tài liệu đính kèm và dữ liệu thực chứng RAG (nếu có), hãy soạn thảo văn bản Đảng hoàn chỉnh, sâu sắc, chuẩn mực cao nhất theo Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.

================================================================================
NGUYÊN TẮC BẮT BUỘC SỐ 1: BÁM SÁT TOÀN VĂN VĂN BẢN CẤP TRÊN (GROUND TRUTH FIDELITY)
================================================================================
1. **BẢO ĐẢM ĐẦY ĐỦ CÁC NHÓM NHIỆM VỤ TRỌNG TÂM:**
   - Khi tham mưu văn bản triển khai văn bản cấp trên (Nghị quyết, Kế hoạch, Chỉ thị của Tỉnh uỷ/UBND tỉnh): Nếu văn bản cấp trên có N nhóm nhiệm vụ trọng tâm (ví dụ: 08 nhóm nhiệm vụ CCHC), bản Kế hoạch của xã BẮT BUỘC PHẢI CHUYỂN HOÁ ĐỦ N NHÓM NHIỆM VỤ TƯƠNG ỨNG. Tuyệt đối không được tóm lược hời hợt hoặc gộp bớt làm mất nhiệm vụ chính trị của cấp trên.
2. **BẮT BUỘC CÓ PHỤ LỤC DANH MỤC NHIỆM VỤ (BẢNG 6 RÕ - 1 XUYÊN SUỐT):**
   - Nếu văn bản cấp trên có phân công nhiệm vụ hoặc có bảng phụ lục, bản Kế hoạch của Đảng uỷ xã BẮT BUỘC PHẢI CÓ PHỤ LỤC DANH MỤC NHIỆM VỤ TRỌNG TÂM đính kèm theo nguyên tắc "6 rõ - 1 xuyên suốt" (STT, Tên nhiệm vụ, Bộ phận chủ trì, Bộ phận phối hợp, Sản phẩm/Chỉ tiêu chính, Thời hạn, Nguồn lực).
   - Phụ lục BẮT BUỘC được đưa vào trường riêng "phu_luc" (hoặc nếu để trong "noi_dung" thì bắt đầu bằng từ khoá "PHỤ LỤC") dưới dạng bảng Markdown chuẩn (| STT | Nhiệm vụ | ... |) để hệ thống tự động chèn dấu ngắt trang (PageBreak) độc lập và đặt sau phần ký của Ban Thường vụ Đảng uỷ.
3. **TÔN TRỌNG 100% CHỈ TIÊU ĐỊNH LƯỢNG:**
   - Kế thừa chính xác các chỉ tiêu %, mốc thời gian, số lượng từ văn bản gốc (ví dụ: giảm 10% họp, 15% văn bản; 90% nhiệm vụ đúng hạn; 100% thu nộp đảng phí điện tử; 95% tài sản số...). Tuyệt đối KHÔNG tự sáng tác, bịa đặt chỉ tiêu ngoài văn bản.
4. **QUY TẮC 'HỎI LẠI KHI CHƯA RÕ — NẮM VỮNG RỒI MỚI VIẾT':**
   - Nếu cán bộ yêu cầu triển khai một văn bản cấp trên cụ thể nhưng trong dữ liệu RAG và tài liệu đính kèm HOÀN TOÀN CHƯA CÓ văn bản đó: BẮT BUỘC phải dừng lại, thông báo rõ ràng là hệ thống chưa lưu trữ văn bản nguồn và đề nghị cán bộ cung cấp tệp hoặc số hiệu/ngày ban hành để nạp vào hệ thống; TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ SUY ĐOÁN BỊA ĐẶT NỘI DUNG.

================================================================================
NGUYÊN TẮC BẮT BUỘC SỐ 2: BỘ MÁY CHÍNH QUYỀN 02 CẤP & CHUẨN THẨM QUYỀN
================================================================================
1. **Mô hình chính quyền địa phương 02 cấp:** Cấp tỉnh (Khánh Hoà) -> Cấp xã (Công Hải). HOÀN TOÀN KHÔNG CÒN CẤP HUYỆN.
2. **Chuẩn thẩm quyền khối cơ quan cấp tỉnh:**
   - Cấp tỉnh chỉ có: Ban Tổ chức Tỉnh uỷ, Cơ quan Uỷ ban Kiểm tra Tỉnh uỷ, Ban Tuyên giáo Tỉnh uỷ, Ban Nội chính Tỉnh uỷ, Văn phòng Tỉnh uỷ, UBND tỉnh.
   - TUYỆT ĐỐI KHÔNG CÓ "Ban Xây dựng Đảng Tỉnh uỷ".
3. **Chuẩn phân vai 5 cơ quan chuyên môn cấp xã:**
   - **Văn phòng Đảng uỷ (VPĐU):** Đầu mối thường trực CCHC, chuyển đổi số cấp uỷ; Hệ điều hành tác nghiệp, chữ ký số chuyên dùng, Sổ tay đảng viên điện tử, đảng phí điện tử; quản lý tài chính, số hoá hồ sơ tài sản; tổng hợp báo cáo gửi Tỉnh uỷ trước 15/12 hằng năm.
   - **Ban Xây dựng Đảng xã:** Rà soát bộ máy, vị trí việc làm; tiêu chí năng lực số, đào tạo bồi dưỡng cán bộ; nghiệp vụ 03 TTHC Đảng về tổ chức, đảng viên (theo KH 73-KH/TU); tuyên truyền, nhân rộng mô hình điển hình.
   - **Uỷ ban Kiểm tra Đảng uỷ xã (UBKT):** Tăng cường kỷ luật, kỷ cương; kiểm tra, giám sát dựa trên dữ liệu, tiến độ, sản phẩm thực tế; theo dõi kiến nghị sau kiểm tra; phòng chống tham nhũng, lãng phí, tiêu cực.
   - **Uỷ ban nhân dân xã (UBND):** Cơ quan chính quyền cùng cấp; phối hợp hạ tầng CNTT, an ninh mạng, liên thông quy trình công tác cấp uỷ - chính quyền; bố trí kinh phí hỗ trợ.
   - **Uỷ ban MTTQ và các đoàn thể xã:** Giám sát, phản biện xã hội, tiếp nhận ý kiến của nhân dân, đoàn viên.
   - **Các chi bộ trực thuộc (08 thôn, trường học, trạm y tế, công an, quân sự):** Sinh hoạt chi bộ số, thu nộp đảng phí điện tử, tinh giản báo cáo giấy.
4. **Không báo cáo vượt cấp:** Các cơ quan chuyên môn cấp xã chỉ báo cáo Ban Thường vụ / Thường trực Đảng uỷ xã; tuyệt đối không báo cáo trực tiếp lên Ban Thường vụ Tỉnh uỷ. Ban Thường vụ Đảng uỷ xã là đầu mối ký gửi báo cáo lên Tỉnh uỷ.
5. **Thẩm quyền ký chuẩn:**
   - Ban Thường vụ Đảng uỷ: T/M BAN THƯỜNG VỤ, Bí thư Vũ Thị Thuỳ Trang hoặc Phó Bí thư Nguyễn Xuân Hoàng.
   - Ban Chấp hành Đảng bộ: T/M ĐẢNG UỶ, Bí thư Vũ Thị Thuỳ Trang.
   - Văn phòng Đảng uỷ: K/T CHÁNH VĂN PHÒNG (hoặc PHÓ CHÁNH VĂN PHÒNG) - Ngô Hoàng Việt.
6. **08 thôn chính thức:** Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng.

================================================================================
NGUYÊN TẮC BẮT BUỘC SỐ 3: THỂ THỨC HƯỚNG DẪN 05-HD/VPTW & CHÍNH TẢ
================================================================================
1. **Chính tả khối Đảng:** Đặt dấu chuẩn oà, uỷ, uý (Đảng uỷ, Khánh Hoà, Uỷ ban). Ngày tháng dạng dd/mm/yyyy.
2. **Thể loại & Khối Kính gửi:**
   - Nếu là Công văn (CV) hoặc Tờ trình (TTr): BẮT BUỘC CÓ khối "kinh_gui" dạng mảng danh sách.
   - Nếu là Kế hoạch (KH), Báo cáo (BC), Thông báo (TB), Quyết định (QD), Nghị quyết (NQ), Kết luận (KL): TUYỆT ĐỐI KHÔNG CÓ KÍNH GỬI (kinh_gui để mảng rỗng []).
3. **Quy chuẩn Kế hoạch (-KH/ĐU):**
   - Kết cấu 5 phần La Mã chuẩn:
     I- MỤC ĐÍCH, YÊU CẦU
     II- PHẠM VI, ĐỐI TƯỢNG VÀ NGUYÊN TẮC THỰC HIỆN (hoặc MỤC TIÊU, CHỈ TIÊU CHỦ YẾU)
     III- MỤC TIÊU, CHỈ TIÊU CHỦ YẾU (hoặc NHIỆM VỤ, GIẢI PHÁP TRỌNG TÂM)
     IV- NHIỆM VỤ, GIẢI PHÁP TRỌNG TÂM (hoặc KINH PHÍ THỰC HIỆN)
     V- KINH PHÍ THỰC HIỆN (nếu có)
     VI- TỔ CHỨC THỰC HIỆN (Phân công cụ thể 5 khối cơ quan xã và chế độ báo cáo)
4. **Quy chuẩn in đậm chỉ mục:**
   - Số chỉ mục và tiêu đề trước dấu hai chấm in đậm đồng bộ: `1. **Nội dung:** ...`, `a) **Về cán bộ:** ...`
   - Nội dung diễn giải sau dấu hai chấm là chữ in thường. Dấu gạch (-) và cộng (+) KHÔNG in đậm.

================================================================================
ĐẦU RA BẮT BUỘC DẠNG JSON VỚI ĐÚNG 2 TRƯỜNG:
================================================================================
{
  "summary": "Tóm tắt ngắn gọn tham mưu để gửi tin nhắn Zalo/Web (gồm: Thể loại văn bản, Trích yếu, Cơ quan chủ trì/thực hiện, Nhiệm vụ trọng tâm, Thời hạn hoàn thành/báo cáo, Phụ lục đính kèm)",
  "doc_payload": {
    "doc_type": "KH",
    "so_hieu": "Số      -KH/ĐU",
    "dia_danh_ngay": "Công Hải, ngày   tháng 11 năm 2026",
    "trich_yeu": "thực hiện Kế hoạch số ... của Ban Thường vụ Tỉnh uỷ về...",
    "tieu_de": "thực hiện Kế hoạch số ... của Ban Thường vụ Tỉnh uỷ về...",
    "kinh_gui": [],
    "noi_dung": [
      "Thực hiện [Căn cứ pháp lý cấp trên, Ban Bí thư, Tỉnh uỷ]; Ban Thường vụ Đảng uỷ xã Công Hải ban hành Kế hoạch thực hiện như sau:",
      "I- MỤC ĐÍCH, YÊU CẦU",
      "1. ...",
      "2. ...",
      "II- PHẠM VI, ĐỐI TƯỢNG VÀ NGUYÊN TẮC THỰC HIỆN",
      "1. ...",
      "III- MỤC TIÊU, CHỈ TIÊU CHỦ YẾU",
      "1. Mục tiêu tổng quát",
      "...",
      "2. Chỉ tiêu cụ thể...",
      "...",
      "IV- NHIỆM VỤ, GIẢI PHÁP TRỌNG TÂM",
      "1. Đổi mới phương thức lãnh đạo...",
      "2. ...",
      "V- KINH PHÍ THỰC HIỆN",
      "...",
      "VI- TỔ CHỨC THỰC HIỆN",
      "1. Văn phòng Đảng uỷ xã: ...",
      "2. Ban Xây dựng Đảng xã: ...",
      "3. Cơ quan Uỷ ban Kiểm tra Đảng uỷ xã: ...",
      "4. Uỷ ban nhân dân xã: ...",
      "5. Uỷ ban MTTQ và các tổ chức chính trị - xã hội xã: ...",
      "6. Các chi bộ trực thuộc: ...",
      "7. Chế độ thông tin, báo cáo: ..."
    ],
    "noi_nhan": [
      "- Ban Thường vụ Tỉnh uỷ (báo cáo);",
      "- Văn phòng Tỉnh uỷ (báo cáo);",
      "- Các đồng chí Uỷ viên BCH Đảng bộ xã;",
      "- Thường trực HĐND, UBND xã;",
      "- Uỷ ban MTTQ và các đoàn thể xã;",
      "- Các chi bộ trực thuộc;",
      "- Lưu VPĐU."
    ],
    "tham_quyen": "T/M BAN THƯỜNG VỤ",
    "chuc_vu": "BÍ THƯ",
    "nguoi_ky": "Vũ Thị Thuỳ Trang",
    "phu_luc": [
      "PHỤ LỤC",
      "DANH MỤC NHIỆM VỤ TRỌNG TÂM THỰC HIỆN KẾ HOẠCH...",
      "(Kèm theo Kế hoạch số       -KH/ĐU ngày     tháng 11 năm 2026 của Ban Thường vụ Đảng uỷ xã Công Hải)",
      "| STT | Nhiệm vụ | Bộ phận chủ trì | Bộ phận phối hợp | Sản phẩm / Chỉ tiêu chính | Thời gian | Nguồn lực |",
      "|---|---|---|---|---|---|---|",
      "| 1 | ... | ... | ... | ... | ... | ... |"
    ]
  }
}
"""


# _normalize_doc_type đã được import từ server.utils.text_processing


def _keyword_intent(message: str, new_atts: List[Dict], has_pending: bool) -> str:
    """Phân loại dự phòng bằng từ khoá khi DeepSeek lỗi."""
    m = message.lower()
    if has_pending and re.search(r"\b(sửa|đổi|thêm|bớt|bỏ|thay)\b", m):
        return "chinh_sua"
    # Nhận diện lệnh soạn thảo văn bản tự do / chủ động
    if re.search(r"\b(soạn|soan|viết|viet|tạo|tao|dự thảo|chủ động giao|giao việc cho|tham mưu văn bản)\b", m):
        return "soan_thao"
    if re.search(r"giao việc|công văn giao|triển khai văn bản", m):
        return "wf3_giao_viec"
    if re.search(r"báo cáo tuần|báo cáo tháng|tổng hợp báo cáo", m):
        return "wf1_tong_hop_bao_cao"
    if re.search(r"kết luận|biên bản|cuộc họp|giao ban", m):
        return "wf2_thong_bao_ket_luan"
    if re.search(r"thẩm định|rà soát dự thảo|góp ý dự thảo", m):
        return "wf4_tham_dinh"
    if new_atts and len(m) < 40 and new_atts[0]["suggested_workflow"] in WORKFLOWS:
        return new_atts[0]["suggested_workflow"]
    return "tro_chuyen"


async def _classify(message: str, new_atts: List[Dict], has_pending: bool) -> Dict[str, str]:
    hint = [
        {"ten_tep": a["name"], "loai": a["category_label"], "goi_y": a["suggested_workflow"]}
        for a in new_atts
    ]
    try:
        res = await default_ai_client.call_chat_async(
            get_intent_messages(message, hint, has_pending), temperature=0.0, max_tokens=200, json_mode=True
        )
        data = res["data"] if isinstance(res["data"], dict) else {}
        intent = data.get("intent", "")
        valid = set(WORKFLOWS) | {"chinh_sua", "soan_thao", "tro_chuyen"}
        if intent not in valid:
            intent = _keyword_intent(message, new_atts, has_pending)
        if intent == "chinh_sua" and not has_pending:
            intent = "tro_chuyen"
        data["intent"] = intent
        return data
    except Exception as ex:
        logger.warning(f"Phân loại bằng AI thất bại, dùng từ khoá: {ex}")
        return {"intent": _keyword_intent(message, new_atts, has_pending)}


def _build_input_text(message: str, new_atts: List[Dict]) -> str:
    # Lấy danh sách tệp duy nhất theo tên tệp (chống trùng lặp)
    seen_names = set()
    unique_atts = []
    for a in new_atts:
        if a["name"] not in seen_names:
            seen_names.add(a["name"])
            unique_atts.append(a)

    parts = []
    for a in unique_atts:
        parts.append(f"=============== TỆP: {a['name']} ({a['category_label']}) ===============\n{a['text']}")
    # Đưa toàn bộ nội dung hoặc chỉ đạo của cán bộ vào đầu vào (không giới hạn độ dài)
    if message and message.strip():
        parts.append(f"=============== NỘI DUNG / CHỈ ĐẠO CỦA CÁN BỘ ===============\n{message.strip()}")
    text = "\n\n".join(parts).strip()
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS] + "\n\n[... Văn bản quá dài, hệ thống đã cắt bớt phần cuối để đảm bảo an toàn ...]"
    return text


# ==============================================================================
# TÓM TẮT KẾT QUẢ NGHIỆP VỤ THÀNH TIN NHẮN CHAT
# ==============================================================================

def _summarize(wf: str, data: Dict[str, Any]) -> str:
    lines = [f"Tôi đã xử lý xong nghiệp vụ **{WORKFLOWS[wf]}**.", ""]

    if wf == "wf3_giao_viec":
        g = data.get("van_ban_goc") or {}
        if g:
            lines.append(
                f"**Văn bản cấp trên:** {g.get('so_hieu', '')} ngày {g.get('ngay_ban_hanh', '')} "
                f"của {g.get('co_quan_ban_hanh', '')}"
            )
            if g.get("trich_yeu"):
                lines.append(f"**Trích yếu:** {g['trich_yeu']}")
            lines.append("")
        tasks = data.get("phan_cong_nhiem_vu") or []
        if tasks:
            lines.append("**Đề xuất phân công:**")
            lines.append("")
            lines.append("| STT | Cơ quan chủ trì | Nhiệm vụ | Thời hạn |")
            lines.append("|---|---|---|---|")
            for i, t in enumerate(tasks, 1):
                lines.append(f"| {t.get('stt', i)} | {_cell(t.get('co_quan_chu_tri'))} | {_cell(t.get('nhiem_vu'))} | {_cell(t.get('thoi_han'))} |")

    elif wf == "wf2_thong_bao_ket_luan":
        tasks = data.get("danh_sach_5_ro") or []
        if tasks:
            lines.append("**Bóc tách nhiệm vụ theo nguyên tắc 5 Rõ:**")
            lines.append("")
            lines.append("| STT | Chủ trì | Phối hợp | Nội dung | Thời hạn | Báo cáo |")
            lines.append("|---|---|---|---|---|---|")
            for i, t in enumerate(tasks, 1):
                lines.append(
                    f"| {t.get('stt', i)} | {_cell(t.get('co_quan_chu_tri'))} | {_cell(t.get('co_quan_phoi_hop'))} | "
                    f"{_cell(t.get('noi_dung_cong_viec'))} | {_cell(t.get('thoi_han'))} | {_cell(t.get('che_do_bao_cao'))} |"
                )

    elif wf == "wf1_tong_hop_bao_cao":
        so_lieu = data.get("tong_hop_so_lieu_chinh") or {}
        labels = {"thu_ngan_sach": "Thu ngân sách", "ket_nap_dang": "Kết nạp đảng viên", "an_ninh_trat_tu": "An ninh trật tự"}
        rows = [(labels[k], so_lieu.get(k)) for k in labels if so_lieu.get(k)]
        if rows:
            lines.append("**Số liệu chính (giữ nguyên theo báo cáo của các cơ quan):**")
            for lbl, val in rows:
                lines.append(f"- {lbl}: {val}")
        noi_bat = so_lieu.get("hoat_dong_noi_bat") or []
        if noi_bat:
            lines.append("")
            lines.append("**Hoạt động nổi bật:**")
            for x in noi_bat:
                lines.append(f"- {x}")

    elif wf == "wf4_tham_dinh":
        info = data.get("thong_tin_du_thao") or {}
        if info:
            lines.append(f"**Dự thảo:** {info.get('ten_van_ban', '')}")
            lines.append(f"**Cơ quan soạn thảo:** {info.get('co_quan_soan_thao', '')}")
            lines.append("")
        lines.append("**Hồ sơ tham mưu sẽ xuất:**")
        lines.append("- Báo cáo kết quả thẩm định của Văn phòng Đảng uỷ (-BC/VPĐU)")
        lines.append("- Tệp dự thảo văn bản đã được rà soát và chuẩn hoá thể thức (.docx)")
        if data.get("cv_lay_y_kien_btv_payload"):
            lines.append("- Công văn xin ý kiến các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ (-CV/ĐU)")

    warnings = data.get("canh_bao_so_lieu") or []
    if warnings:
        lines.append("")
        lines.append(f"### ⚠️ Có {len(warnings)} điểm cần đồng chí xác nhận")
        lines.append("Theo nguyên tắc, tôi **không tự sửa** nội dung, số liệu của cơ quan. Đồng chí xem xét:")
        lines.append("")
        for i, w in enumerate(warnings, 1):
            where = w.get("co_quan") or w.get("muc_van_ban") or w.get("noi_dung_hop") or "Lưu ý"
            issue = w.get("van_de") or ""
            if w.get("so_lieu_goc"):
                issue = f"{issue} (số liệu gốc: {w['so_lieu_goc']})"
            lines.append(f"{i}. **{_cell(where)}:** {issue}")
            if w.get("de_xuat_hoi"):
                lines.append(f"   - *Đề nghị xác nhận:* {w['de_xuat_hoi']}")
    else:
        lines.append("")
        lines.append("✅ Không phát hiện mâu thuẫn số liệu.")

    lines.append("")
    lines.append(
        "Đồng chí xem trước dự thảo bên dưới. Nếu cần sửa, cứ gõ yêu cầu "
        "(ví dụ: *\"đổi thời hạn của UBND xã thành 20/10/2026\"*). "
        "Nếu đồng ý, bấm **Duyệt & xuất Word**."
    )
    return "\n".join(lines)


def _preview_docs(wf: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if wf == "wf4_tham_dinh":
        pairs = [
            ("Báo cáo thẩm định (-BC/VPĐU)", data.get("bc_tham_dinh_payload")),
            ("Công văn xin ý kiến BTV (-CV/ĐU)", data.get("cv_lay_y_kien_btv_payload")),
        ]
        if data.get("du_thao_hoan_chinh_payload"):
            pairs.insert(1, ("Dự thảo đã chuẩn hoá", data.get("du_thao_hoan_chinh_payload")))
    else:
        pairs = [(WORKFLOWS[wf], data.get("document_payload"))]

    docs = []
    for label, p in pairs:
        if not isinstance(p, dict):
            continue
        docs.append({
            "label": label,
            "doc_type": p.get("doc_type", ""),
            "co_quan_cap_tren": p.get("co_quan_cap_tren", ""),
            "co_quan_ban_hanh": p.get("co_quan_ban_hanh", ""),
            "so_hieu": p.get("so_hieu", ""),
            "ten_loai": p.get("ten_loai", ""),
            "trich_yeu": p.get("trich_yeu", ""),
            "kinh_gui": p.get("kinh_gui", []),
            "can_cu": p.get("can_cu", []),
            "noi_dung": p.get("noi_dung", []),
            "noi_nhan": p.get("noi_nhan", []),
            "tham_quyen": p.get("tham_quyen", ""),
            "chuc_vu": p.get("chuc_vu", ""),
            "nguoi_ky": p.get("nguoi_ky", ""),
        })
    return docs


def _approval_actions(has_warnings: bool) -> List[Dict[str, str]]:
    return [
        {"id": "confirm", "label": "✓ Giữ nguyên số liệu & xuất Word" if has_warnings else "✓ Duyệt & xuất Word", "style": "primary"},
        {"id": "cancel", "label": "Huỷ dự thảo", "style": "ghost"},
    ]


# ==============================================================================
# CÁC BƯỚC XỬ LÝ
# ==============================================================================

async def _draft_party_document(s: Dict[str, Any], message: str, new_atts: List[Dict]) -> Dict[str, Any]:
    """Soạn thảo chủ động mọi thể loại văn bản Đảng theo lệnh của cán bộ với tri thức và kỹ năng được nạp đầy đủ."""
    # Chống ảo giác (Anti-Hallucination Guard): Nếu không có tệp đính kèm và yêu cầu triển khai/giao việc chưa rõ văn bản nguồn
    is_implement_directive = bool(re.search(r'(?:triển\s*khai|giao\s*việc|thực\s*hiện\s*văn\s*bản|soạn\s*công\s*văn\s*triển\s*khai)', message, re.IGNORECASE))
    has_specific_source = bool(re.search(r'(?:số\s*\d+|nghị\s*quyết|chỉ\s*thị|kế\s*hoạch\s*số|kết\s*luận|thông\s*báo\s*số|\d+[-/][A-ZĐ]+)', message, re.IGNORECASE))

    if not new_atts and is_implement_directive and not has_specific_source and len(message.strip()) < 80:
        s["awaiting"] = "wf3_giao_viec"
        ho_ten_xung_ho = f"đồng chí {s['can_bo'].get('ho_ten', '')}" if s.get("can_bo") else "đồng chí"
        return _reply(
            s,
            f"⚠️ **CHƯA CÓ VĂN BẢN NGUỒN CẦN TRIỂN KHAI**\n\n"
            f"Kính thưa {ho_ten_xung_ho}, tôi đã tiếp nhận yêu cầu: *\"{message.strip()}\"*.\n\n"
            "Tuy nhiên, hiện tại trong phiên làm việc **chưa có tệp văn bản đính kèm** hoặc thông tin cụ thể về văn bản cấp trên cần triển khai (như số hiệu, ngày ban hành, nội dung chỉ đạo cốt lõi).\n\n"
            "📌 *Theo Quy tắc 'Hỏi lại khi chưa rõ — Nắm vững rồi mới viết'*, xin đồng chí vui lòng:\n"
            "1️⃣ **Gửi tệp văn bản cấp trên** (file Word, PDF hoặc ảnh chụp) vào đây.\n"
            "2️⃣ Hoặc gõ bổ sung thông tin: *Số hiệu văn bản, ngày ban hành của Tỉnh uỷ/UBND tỉnh, và đơn vị nào chủ trì thực hiện* để tôi tham mưu dự thảo chính xác 100%, tuyệt đối không tự suy đoán."
        )

    context_text = _build_input_text(message, new_atts)
    detected_type = _normalize_doc_type(message)
    knowledge_context = build_system_knowledge_prompt(detected_type, include_local=True)

    # TỰ ĐỘNG KÍCH HOẠT RAG NẾU KHÔNG CÓ TỆP ĐÍNH KÈM NHƯNG CÓ NHẮC TỚI VĂN BẢN TRONG KHO
    rag_citations = []
    rag_context = ""
    if not new_atts:
        try:
            from server.services.query_analyzer import analyze_query
            from server.services.rag_service import retrieve_direct_hit, retrieve_hybrid_context
            analysis = analyze_query(message, history=s.get("history", []))
            if analysis.get("entities"):
                rag_res = retrieve_direct_hit(analysis["entities"])
                if rag_res.get("not_found"):
                    nf_list = ", ".join(rag_res["not_found"])
                    ho_ten_xung_ho = f"đồng chí {s['can_bo'].get('ho_ten', '')}" if s.get("can_bo") else "đồng chí"
                    return _reply(
                        s,
                        f"⚠️ **CHƯA CÓ VĂN BẢN NGUỒN TRONG KHO TRI THỨC**\n\n"
                        f"Kính thưa {ho_ten_xung_ho}, tôi đã tiếp nhận yêu cầu tham mưu triển khai văn bản: **{nf_list}**.\n\n"
                        f"Tuy nhiên, hệ thống đã tra cứu nhưng **chưa tìm thấy toàn văn văn bản này** trong cơ sở dữ liệu của Đảng uỷ xã.\n\n"
                        f"📌 *Theo Quy tắc 'Hỏi lại khi chưa rõ — Nắm vững rồi mới viết' và kỷ luật công vụ:*\n"
                        f"- Chuyên viên ảo **tuyệt đối không tự suy đoán** số liệu, chỉ tiêu và các nhóm nhiệm vụ khi chưa có văn bản gốc của cấp trên.\n"
                        f"- Xin đồng chí vui lòng **đính kèm tệp văn bản** (Word, PDF, ảnh scan) hoặc nạp văn bản này vào kho tri thức RAG để tôi tiến hành tham mưu chính xác 100%."
                    )
                elif rag_res.get("context_text"):
                    rag_context = rag_res["context_text"]
                    rag_citations = rag_res.get("citations", [])
            if not rag_context and analysis.get("enriched_query"):
                rag_res = retrieve_hybrid_context(analysis["enriched_query"], max_slots=2)
                if rag_res.get("context_text"):
                    rag_context = rag_res["context_text"]
                    rag_citations = rag_res.get("citations", [])
            if rag_context:
                context_text += f"\n\n=============== DỮ LIỆU THỰC CHỨNG TỪ KHO RAG (VĂN BẢN NGUỒN CẦN TRIỂN KHAI) ===============\n{rag_context}"
                logger.info(f"Đã tự động nạp văn bản nguồn từ RAG vào ngữ cảnh soạn thảo cho '{detected_type}'")
        except Exception as ex:
            logger.warning(f"Lỗi khi tra cứu RAG trong luồng soạn thảo: {ex}")

    messages = [
        {"role": "system", "content": f"{DRAFT_SYSTEM_PROMPT}\n\n{knowledge_context}"},
        {"role": "user", "content": f"Yêu cầu của cán bộ:\n{context_text}"},
    ]
    res = await default_ai_client.call_chat_async(messages, temperature=0.2, max_tokens=8192, json_mode=True)
    out = res.get("data") if isinstance(res.get("data"), dict) else {}
    doc_payload = out.get("doc_payload")
    summary = out.get("summary") or "Đã dự thảo xong văn bản theo yêu cầu của đồng chí."

    if not isinstance(doc_payload, dict):
        return _reply(s, "Tôi chưa tổng hợp được dự thảo theo cấu trúc chuẩn. Đồng chí vui lòng mô tả rõ hơn hoặc gửi lại yêu cầu.")

    doc_type = _normalize_doc_type(doc_payload.get("doc_type", "CV"))
    doc_payload["doc_type"] = doc_type

    for a in new_atts:
        a["used"] = True

    s["pending"] = {"workflow": "party_doc", "data": doc_payload, "summary": summary}

    reply_text = (
        f"📝 **DỰ THẢO THAM MƯU: {doc_type}**\n\n"
        f"{summary}\n\n"
        f"📌 **Trích yếu:** {doc_payload.get('trich_yeu', '')}\n"
        f"👤 **Thẩm quyền ký:** {doc_payload.get('tham_quyen', 'T/M BAN THƯỜNG VỤ')} - {doc_payload.get('chuc_vu', 'BÍ THƯ')} ({doc_payload.get('nguoi_ky', 'Vũ Thị Thuỳ Trang')})\n\n"
        f"👉 *Đồng chí xem lại nội dung trên. Nếu đồng ý, vui lòng gõ **'Duyệt'** để tôi xuất tệp Word lên Google Drive, hoặc gõ chỉ đạo chỉnh sửa trực tiếp.*"
    )
    return _reply(s, reply_text, actions=_approval_actions(False), preview=[doc_payload], rag_sources=rag_citations)


async def _run_workflow(s: Dict[str, Any], wf: str, message: str, params: Dict[str, str]) -> Dict[str, Any]:
    new_atts = [a for a in s["attachments"] if not a["used"]]
    input_text = _build_input_text(message, new_atts)

    # Nếu chọn wf3_giao_viec mà không có tệp đính kèm nhưng có lệnh trực tiếp -> tự động chuyển sang soạn thảo chủ động
    if wf == "wf3_giao_viec" and not new_atts and message.strip():
        return await _draft_party_document(s, message, new_atts)

    if not input_text:
        s["awaiting"] = wf
        return _reply(
            s,
            f"Để thực hiện **{WORKFLOWS[wf]}**, đồng chí vui lòng bấm 📎 đính kèm {NEED_INPUT_HINT[wf]}, "
            f"rồi bấm gửi (không cần gõ lại lệnh).",
        )

    s["awaiting"] = None
    # Đánh dấu các tệp này đã được đưa vào xử lý
    for a in new_atts:
        a["used"] = True

    if wf == "wf1_tong_hop_bao_cao":
        data = await analyze_weekly_reports(input_text, params.get("tuan_so") or "...")
    elif wf == "wf2_thong_bao_ket_luan":
        data = await analyze_meeting_notes(input_text, params.get("ten_cuoc_hop") or "Họp Thường trực Đảng uỷ")
    elif wf == "wf3_giao_viec":
        data = await analyze_provincial_directive(input_text)
    else:
        source_docx = None
        for a in new_atts:
            sp = a.get("saved_path")
            if sp and str(sp).lower().endswith(".docx") and Path(sp).exists():
                source_docx = str(sp)
                break
        data = await analyze_agency_draft(input_text, params.get("co_quan_trinh") or "cơ quan chuyên môn")
        if isinstance(data, dict) and source_docx:
            data["_source_docx_path"] = source_docx

    if not isinstance(data, dict):
        return _reply(s, "DeepSeek trả kết quả không đúng cấu trúc. Đồng chí vui lòng gửi lại lệnh để tôi thử lại.")
    if wf != "wf4_tham_dinh" and not isinstance(data.get("document_payload"), dict):
        return _reply(s, "Kết quả của DeepSeek thiếu phần dự thảo văn bản. Đồng chí vui lòng gửi lại lệnh để tôi thử lại.")
    if wf == "wf4_tham_dinh" and not isinstance(data.get("bc_tham_dinh_payload"), dict):
        return _reply(s, "Kết quả của DeepSeek thiếu Báo cáo thẩm định. Đồng chí vui lòng gửi lại lệnh để tôi thử lại.")

    for a in new_atts:
        a["used"] = True
    s["pending"] = {"workflow": wf, "data": data}

    has_warnings = bool(data.get("canh_bao_so_lieu"))
    return _reply(
        s,
        _summarize(wf, data),
        actions=_approval_actions(has_warnings),
        preview=_preview_docs(wf, data),
    )


async def _revise(s: Dict[str, Any], instruction: str) -> Dict[str, Any]:
    pending = s["pending"]
    wf = pending["workflow"]

    if wf == "party_doc":
        current_data = pending["data"]
        messages = [
            {
                "role": "system",
                "content": (
                    "Bạn là Chuyên viên ảo Văn phòng Đảng uỷ xã Công Hải. "
                    "Hãy chỉnh sửa cấu trúc dữ liệu doc_payload theo đúng chỉ đạo của cán bộ. "
                    "Đầu ra BẮT BUỘC dạng JSON: {'summary': 'tóm tắt điểm đã sửa ngắn gọn', 'doc_payload': {toàn bộ payload mới theo chuẩn Hướng dẫn 05-HD/VPTW}}"
                ),
            },
            {
                "role": "user",
                "content": f"Dự thảo hiện tại:\n{json.dumps(current_data, ensure_ascii=False)}\n\nChỉ đạo chỉnh sửa của cán bộ:\n{instruction}",
            },
        ]
        res = await default_ai_client.call_chat_async(messages, temperature=0.1, max_tokens=4000, json_mode=True)
        out = res.get("data") if isinstance(res.get("data"), dict) else {}
        new_payload = out.get("doc_payload")
        if isinstance(new_payload, dict):
            new_payload["doc_type"] = _normalize_doc_type(new_payload.get("doc_type", current_data.get("doc_type", "CV")))
            pending["data"] = new_payload
            note = out.get("summary") or "Đã cập nhật dự thảo theo chỉ đạo của đồng chí."
            return _reply(
                s,
                f"✏️ **Đã chỉnh sửa:** {note}\n\n"
                f"📌 **Trích yếu:** {new_payload.get('trich_yeu', '')}\n\n"
                f"Đồng chí kiểm tra lại, nếu đồng ý thì gõ **'Duyệt'** để xuất Word lên Google Drive.",
                actions=_approval_actions(False),
            )
        return _reply(s, "Tôi chưa sửa được theo yêu cầu. Đồng chí vui lòng diễn đạt cụ thể hơn.", actions=_approval_actions(False))

    res = await default_ai_client.call_chat_async(
        get_revise_messages(pending["data"], instruction), temperature=0.1, max_tokens=8000, json_mode=True
    )
    out = res["data"] if isinstance(res["data"], dict) else {}
    new_data = out.get("du_lieu")
    if not isinstance(new_data, dict):
        return _reply(s, "Tôi chưa sửa được theo yêu cầu. Đồng chí vui lòng diễn đạt cụ thể hơn (sửa mục nào, thành nội dung gì).",
                      actions=_approval_actions(bool(pending["data"].get("canh_bao_so_lieu"))))
    pending["data"] = new_data
    note = out.get("ghi_chu_thay_doi") or "Đã cập nhật dự thảo."
    return _reply(
        s,
        f"✏️ **Đã chỉnh sửa:** {note}\n\nĐồng chí xem lại dự thảo bên dưới, nếu đồng ý thì bấm **Duyệt & xuất Word**.",
        actions=_approval_actions(False),
        preview=_preview_docs(wf, new_data),
    )


def _sync_tasks_from_draft(wf: str, data: Dict[str, Any]) -> int:
    """Tự động đồng bộ các nhiệm vụ giao việc từ dự thảo vừa duyệt vào Sổ Nhiệm vụ (SQLite DB)."""
    try:
        from server.services import db_service
        count = 0
        doc_payload = data.get("document_payload") or data
        so_hieu = doc_payload.get("so_hieu", "")

        noi_dung_lines = doc_payload.get("noi_dung", [])
        if isinstance(noi_dung_lines, list):
            for line in noi_dung_lines:
                if not isinstance(line, str):
                    continue
                # Nhận diện dòng giao việc theo cơ quan
                m = re.search(r'(?:Giao\s+|[0-9]+\.\s+)(Uỷ ban nhân dân xã|UBND xã|Ban Xây dựng Đảng|Cơ quan Uỷ ban Kiểm tra|UBKT|MTTQ|Văn phòng Đảng uỷ)\s*[:\-]\s*(.+)', line, re.IGNORECASE)
                if m:
                    cq = m.group(1).strip()
                    nd = m.group(2).strip()
                    cq_code = "UBND" if "UBND" in cq or "Uỷ ban nhân dân" in cq else ("BXDD" if "Xây dựng" in cq else ("UBKT" if "Kiểm tra" in cq else ("MTTQ" if "MTTQ" in cq else "VPDU")))

                    deadline_date = datetime.now().strftime("%Y-%m-%d")
                    dl_match = re.search(r'(?:hoàn thành|báo cáo|trình)?\s*(?:trước|trong)?\s*ngày\s*([0-9]{1,2})[\/\-]([0-9]{1,2})(?:[\/\-]([0-9]{4}))?', nd, re.IGNORECASE)
                    if dl_match:
                        d = int(dl_match.group(1))
                        m_val = int(dl_match.group(2))
                        y = int(dl_match.group(3)) if dl_match.group(3) else datetime.now().year
                        deadline_date = f"{y}-{m_val:02d}-{d:02d}"

                    db_service.add_or_update_task({
                        "so_hieu_vb": so_hieu,
                        "co_quan_chu_tri": cq,
                        "co_quan_chu_tri_code": cq_code,
                        "noi_dung_nhiem_vu": nd[:250],
                        "deadline_date": deadline_date,
                        "created_from_wf": wf,
                    })
                    count += 1
        return count
    except Exception as ex:
        logger.warning(f"Lỗi khi đồng bộ nhiệm vụ vào CSDL: {ex}")
        return 0


def _confirm(s: Dict[str, Any]) -> Dict[str, Any]:
    pending = s["pending"]
    if not pending:
        return _reply(s, "Hiện không có dự thảo nào đang chờ duyệt.")
    wf, data = pending["workflow"], pending["data"]

    files = []
    if wf == "party_doc":
        path = export_party_document(data)
        doc_type_label = data.get("doc_type", "CV")
        files.append({
            "label": f"Văn bản dự thảo ({doc_type_label})",
            "name": Path(path).name,
            "url": _download_url(path),
        })
    elif wf == "wf4_tham_dinh":
        labels = {
            "bc_tham_dinh": "Báo cáo thẩm định (-BC/VPĐU)",
            "du_thao_chuan_hoa": "Dự thảo đã chuẩn hoá (HD 05)",
            "cv_lay_y_kien_btv": "Công văn xin ý kiến BTV (-CV/ĐU)",
        }
        source_docx = data.get("_source_docx_path")
        for key, path in generate_appraisal_documents(data, source_docx_path=source_docx).items():
            files.append({"label": labels.get(key, key), "name": Path(path).name, "url": _download_url(path)})
    else:
        gen = {
            "wf1_tong_hop_bao_cao": generate_weekly_report_docx,
            "wf2_thong_bao_ket_luan": generate_meeting_conclusion_docx,
            "wf3_giao_viec": generate_dispatch_docx,
        }[wf]
        path = gen(data["document_payload"])
        files.append({"label": WORKFLOWS[wf], "name": Path(path).name, "url": _download_url(path)})

    # Tự động đồng bộ các đầu việc mới vào Sổ Nhiệm vụ (SQLite WAL)
    synced_tasks = _sync_tasks_from_draft(wf, data)

    s["pending"] = None
    task_notice = f"\n\n📋 *Đã tự động cập nhật **{synced_tasks}** đầu việc vào Sổ Nhiệm vụ của Đảng uỷ.*" if synced_tasks > 0 else ""
    return _reply(
        s,
        f"📄 Đã xuất **{len(files)}** tệp văn bản dự thảo (.docx). "
        "Đồng chí tải về, rà soát lại trước khi trình ký."
        f"{task_notice}\n\n"
        "*Lưu ý: Đây là dự thảo tham mưu — việc ban hành, ký số do cán bộ trực tiếp thực hiện.*",
        files=files,
    )


def _build_rag_context_messages(message: str, history: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Helper dùng chung cho cả luồng chat đồng bộ và luồng chat Stream:
    Định tuyến truy vấn (DIRECT_HIT / AGGREGATE / THEMATIC) kèm tự động fallback
    sang Hybrid RAG nếu DIRECT_HIT không tìm thấy đích danh.
    """
    from server.services.query_analyzer import analyze_query
    from server.services.rag_service import retrieve_direct_hit, retrieve_hybrid_context, check_and_get_aggregate_stats

    analysis = analyze_query(message, history=history)
    rag_msgs: List[Dict[str, str]] = []
    citations: List[Dict[str, Any]] = []
    stats_info: Optional[Dict[str, Any]] = None

    if analysis["type"] == "DIRECT_HIT":
        logger.info(f"RAG: Kích hoạt nhánh DIRECT_HIT cho thực thể: {analysis.get('primary_canonical')}")
        rag_res = retrieve_direct_hit(analysis["entities"])
        if rag_res.get("context_text"):
            rag_msgs.append({
                "role": "system",
                "content": f"Dữ liệu tra cứu thực chứng đích danh từ Kho văn bản Đảng uỷ & UBND xã:\n{rag_res['context_text']}"
            })
            citations = rag_res.get("citations", [])
        elif rag_res.get("not_found"):
            try:
                hyb_res = retrieve_hybrid_context(analysis["enriched_query"], max_slots=6)
                if hyb_res.get("context_text"):
                    rag_msgs.append({
                        "role": "system",
                        "content": f"Dữ liệu tra cứu thực chứng từ Kho văn bản Đảng uỷ & UBND xã:\n{hyb_res['context_text']}"
                    })
                    citations = hyb_res.get("citations", [])
                else:
                    nf_list = ", ".join(rag_res["not_found"])
                    rag_msgs.append({
                        "role": "system",
                        "content": f"[THÔNG BÁO TRA CỨU]: Cán bộ hỏi thông tin về văn bản '{nf_list}', nhưng Kho CSDL hiện CHƯA LƯU TRỮ văn bản này. Đồng chí hãy trả lời trung thực, rõ ràng rằng hệ thống chưa có dữ liệu văn bản này trong kho và sẵn sàng tiếp nhận để nạp bổ sung nếu cán bộ có văn bản gốc."
                    })
            except Exception as ex:
                logger.warning(f"Lỗi fallback Hybrid RAG sau DIRECT_HIT: {ex}")

    elif analysis["type"] == "AGGREGATE":
        logger.info("RAG: Kích hoạt nhánh AGGREGATE thống kê số lượng văn bản")
        try:
            stats_info = check_and_get_aggregate_stats(message)
            if stats_info and stats_info.get("stats_text"):
                rag_msgs.append({"role": "system", "content": stats_info["stats_text"]})
        except Exception as ex:
            logger.warning(f"Lỗi khi kiểm tra thống kê văn bản: {ex}")

    else:
        logger.info(f"RAG: Kích hoạt nhánh THEMATIC Hybrid RAG với query: '{analysis['enriched_query']}'")
        try:
            rag_res = retrieve_hybrid_context(analysis["enriched_query"], max_slots=6)
            if rag_res.get("context_text"):
                rag_msgs.append({
                    "role": "system",
                    "content": f"Dữ liệu tra cứu thực chứng từ Kho văn bản Đảng uỷ & UBND xã:\n{rag_res['context_text']}"
                })
                citations = rag_res.get("citations", [])
        except Exception as ex:
            logger.warning(f"Lỗi khi tra cứu Hybrid RAG: {ex}")

    return rag_msgs, citations, stats_info


async def _chat(s: Dict[str, Any], message: str) -> Dict[str, Any]:
    core_rules = get_core_rules()
    local_facts = get_local_knowledge_summary()
    msgs = [{"role": "system", "content": f"{CHAT_SYSTEM_PROMPT}\n\n{core_rules}\n\n{local_facts}"}]

    # 1. Phân tích ý định & thực thể câu truy vấn (Query Analyzer & Anaphora Resolver)
    rag_msgs, citations, stats_info = _build_rag_context_messages(message, s.get("history", []))
    msgs.extend(rag_msgs)

    new_atts = [a for a in s["attachments"] if not a["used"]]
    if new_atts:
        att_text = "\n\n".join(f"=== TỆP: {a['name']} ===\n{a['text']}" for a in new_atts)[:MAX_CHAT_ATTACH_CHARS]
        msgs.append({"role": "system", "content": f"Cán bộ đã đính kèm các tệp sau, dùng để trả lời nếu liên quan:\n\n{att_text}"})
    msgs.extend(s["history"][-10:])
    res = await default_ai_client.call_chat_async(msgs, temperature=0.3, max_tokens=2000, json_mode=False)

    reply_content = res.get("content", "").strip() or "Xin lỗi, tôi chưa có câu trả lời."
    web_sources = res.get("web_sources", []) or default_ai_client.get_last_web_sources()
    
    # Khử trùng lặp trích dẫn RAG để lưu ngầm vào audit log (không in ra khung chat để giữ phản hồi ngắn gọn)
    unique_citations = []
    if citations:
        seen_so_hieu = set()
        for c in citations:
            so = (c.get("so_hieu") or "").strip()
            if so and so not in seen_so_hieu:
                seen_so_hieu.add(so)
                unique_citations.append(c)

    # Khuyến cáo trách nhiệm công vụ bắt buộc ở cuối câu trả lời
    disclaimer = "\n\n*Lưu ý: Cán bộ tham mưu chịu trách nhiệm toàn diện về tính chính xác và tính pháp lý của thông tin khi sử dụng thông tin từ AI.*"
    if disclaimer.strip() not in reply_content:
        reply_content += disclaimer

    return _reply(
        s,
        reply_content,
        rag_sources=unique_citations if citations else [],
        web_sources=web_sources if web_sources else [],
    )


# ==============================================================================
# HÀM CÔNG KHAI
# ==============================================================================

async def handle_chat(
    session_id: Optional[str],
    message: str = "",
    action: str = "",
    token: Optional[str] = None,
    attachment_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    session_id, s = get_session(session_id)
    message = (message or "").strip()
    action = (action or "").strip()

    # Nếu cán bộ chủ động gửi kèm tệp trong tin nhắn hiện tại, đảm bảo tệp chưa bị đánh dấu used
    if attachment_ids:
        att_id_set = set(attachment_ids)
        for a in s.get("attachments", []):
            if a.get("id") in att_id_set:
                a["used"] = False

    new_atts = [a for a in s["attachments"] if not a["used"]]
    start_time = time.time()

    # Tự động nạp và duy trì danh tính cán bộ từ token nếu phiên chưa có
    if token and not s.get("can_bo"):
        try:
            from server.routers.auth import ACTIVE_TOKENS
            from server.services import db_service
            can_bo_info = None
            if token in ACTIVE_TOKENS:
                can_bo_info = ACTIVE_TOKENS[token]["can_bo"]
            else:
                db_s = db_service.get_auth_session(token)
                if db_s:
                    can_bo_info = {
                        "can_bo_id": db_s["can_bo_id"],
                        "ho_ten": db_s["ho_ten"],
                        "chuc_vu": db_s["chuc_vu"],
                        "co_quan": db_s["co_quan"],
                        "co_quan_code": db_s["co_quan_code"],
                        "so_dien_thoai": db_s.get("so_dien_thoai"),
                        "vai_tro": db_s.get("vai_tro", "can_bo"),
                    }
                    ACTIVE_TOKENS[token] = {"can_bo": can_bo_info, "created_at": time.time()}
            if can_bo_info:
                s["authenticated"] = True
                s["can_bo"] = can_bo_info
        except Exception as auth_ex:
            logger.warning(f"Lỗi nạp danh tính từ token: {auth_ex}")

    def done(result: Dict[str, Any]) -> Dict[str, Any]:
        result["session_id"] = session_id

        # LƯU TOÀN BỘ NHẬT KÝ HỘI THOẠI 100% ĐẦY ĐỦ (CẢ CÁN BỘ ĐĂNG NHẬP & CHẾ ĐỘ KHÁCH)
        can_bo = s.get("can_bo")
        latency_ms = int((time.time() - start_time) * 1000)
        names = ", ".join(a["name"] for a in s["attachments"])
        reply_text = result.get("reply", "")

        if can_bo:
            ho_ten = can_bo.get("ho_ten", "Cán bộ")
            so_dien_thoai = can_bo.get("so_dien_thoai", "")
            co_quan = can_bo.get("co_quan", "Văn phòng Đảng uỷ")
            vai_tro = can_bo.get("vai_tro", "can_bo")
            can_bo_id = can_bo.get("can_bo_id")
        else:
            ho_ten = "Khách (Chưa đăng nhập)"
            so_dien_thoai = ""
            co_quan = "Truy cập Web"
            vai_tro = "khach"
            can_bo_id = None

        # Ghi nhật ký vào CSDL SQLite WAL (Chỉ ghi kênh Web; kênh Zalo do zalo_webhook.py tự ghi độc quyền để tránh trùng lặp)
        is_zalo_session = bool(session_id and str(session_id).startswith("zalo_"))
        if (message or reply_text or action) and not is_zalo_session:
            try:
                from server.services import db_service
                db_service.save_chat_log({
                    "session_id": session_id,
                    "channel": "web",
                    "can_bo_id": can_bo_id,
                    "so_dien_thoai": so_dien_thoai,
                    "ho_ten": ho_ten,
                    "co_quan": co_quan,
                    "vai_tro": vai_tro,
                    "message_text": message or (f"Thao tác: {action}" if action else "(Gửi tệp đính kèm)"),
                    "attachment_names": names,
                    "bot_reply": reply_text,
                    "model_used": getattr(default_ai_client, "model", "gemini-3.5-flash-lite"),
                    "latency_ms": latency_ms,
                    "rag_sources": json.dumps(result.get("rag_sources", []), ensure_ascii=False) if result.get("rag_sources") else "",
                })
                # Ghi nhật ký audit chuẩn hoá ra log file
                rag_list = result.get("rag_sources", [])
                rag_summary = ", ".join(f"{c.get('so_hieu')} ({c.get('tier')})" for c in rag_list) if rag_list else "Không dùng RAG"
                logger.info(
                    f"[CHAT_AUDIT] Session: {session_id} | Cán bộ: {ho_ten} ({vai_tro}) | Kênh: web | {latency_ms}ms\n"
                    f"  • CÂU HỎI: {message[:120]}\n"
                    f"  • RAG NẠP: {rag_summary}\n"
                    f"  • TRẢ LỜI: {reply_text[:150]}..."
                )
            except Exception as log_ex:
                logger.warning(f"Lỗi lưu nhật ký chat: {log_ex}")

        # Đồng bộ trạng thái phiên (attachments, pending, awaiting) vào SQLite WAL bền vững
        _sync_session_to_db(session_id, s)
        return result

    # 0. Xử lý lệnh xoá lịch sử / làm mới phiên làm việc (Chat Command hoặc Action)
    is_clear_action = action in ("clear_history", "reset", "clear")
    is_clear_cmd = bool(re.search(
        r'^\s*(?:/clear|/reset|xoá\s*lịch\s*sử|xóa\s*lịch\s*sử|xoá\s*tin\s*nhắn|xóa\s*tin\s*nhắn|xoá\s*cuộc\s*trò\s*chuyện|xóa\s*cuộc\s*trò\s*chuyện|xoá\s*hội\s*thoại|xóa\s*hội\s*thoại|làm\s*mới|bắt\s*đầu\s*lại)\s*$',
        message,
        re.IGNORECASE
    ))

    if is_clear_action or is_clear_cmd:
        clear_session_history(session_id, delete_logs_in_db=True)
        reply = (
            "🧹 **ĐÃ XOÁ TOÀN BỘ LỊCH SỬ HỘI THOẠI & LÀM MỚI PHIÊN**\n\n"
            "Toàn bộ ngữ cảnh trao đổi và các tệp đính kèm trước đó đã được dọn sạch hoàn toàn.\n\n"
            "👉 Đồng chí có thể bắt đầu phiên làm việc mới hoặc nhập yêu cầu tham mưu tiếp theo."
        )
        return {"session_id": session_id, "reply": reply, "actions": [], "files": [], "preview": []}

    # Ghi lịch sử phía người dùng
    if message or new_atts:
        names = ", ".join(a["name"] for a in new_atts)
        s["history"].append({"role": "user", "content": (message or "(gửi tệp)") + (f"\n[Đính kèm: {names}]" if names else "")})

    try:
        # 1. Nút bấm / lệnh duyệt - huỷ
        clean_msg = re.sub(r'^\s*\[@[^\]]+\]\s*', '', message)
        clean_msg = re.sub(r'^\s*@Bot(?:\s+VPĐU(?:\s+Công\s+Hải)?)?\s*[:,\-]?\s*', '', clean_msg, flags=re.IGNORECASE)
        clean_msg = re.sub(r'^\s*@[^\s]+\s*', '', clean_msg).strip()
        core_msg = clean_msg.rstrip('.!?,;: ')

        is_confirm = action == "confirm" or (s["pending"] and len(core_msg) < 40 and (CONFIRM_RE.search(core_msg) or CONFIRM_RE.search(message)))
        is_cancel = action == "cancel" or (s["pending"] and len(core_msg) < 40 and (CANCEL_RE.search(core_msg) or CANCEL_RE.search(message)))

        if is_confirm:
            return done(_confirm(s))
        if is_cancel:
            s["pending"] = None
            return done(_reply(s, "Đã huỷ dự thảo. Đồng chí cần tôi làm việc gì tiếp theo?"))

        if not default_ai_client.is_configured():
            return done(_reply(s, "⚠️ Chưa cấu hình API Key (**GEMINI_API_KEY** hoặc **DEEPSEEK_API_KEY**) trong tệp `.env`. Đồng chí điền key rồi khởi động lại hệ thống."))

        # 2. Nút chạy nghiệp vụ trực tiếp (run:wfX)
        if action.startswith("run:") and action[4:] in WORKFLOWS:
            return done(await _run_workflow(s, action[4:], message, {}))

        # 3. Chỉ gửi tệp, không gõ lệnh
        if not message:
            if not new_atts:
                return done(_reply(s, "Đồng chí cần tôi giúp việc gì?"))
            if s.get("awaiting"):
                return done(await _run_workflow(s, s["awaiting"], "", {}))
            files_desc = "\n".join(f"- **{a['name']}** — nhận diện: {a['category_label']}" for a in new_atts)
            suggested = new_atts[0]["suggested_workflow"]
            actions = [{"id": f"run:{suggested}", "label": f"▶ {WORKFLOWS[suggested]}", "style": "primary"}] if suggested in WORKFLOWS else []
            actions += [{"id": f"run:{k}", "label": v, "style": "ghost"} for k, v in WORKFLOWS.items() if k != suggested]
            return done(_reply(s, f"Tôi đã nhận tệp:\n{files_desc}\n\nĐồng chí muốn tôi thực hiện nghiệp vụ nào?", actions=actions))

        # 4. Phân loại câu lệnh
        cls = await _classify(message, new_atts, bool(s["pending"]))
        intent = cls["intent"]
        if intent == "tro_chuyen" and s.get("awaiting") and new_atts:
            intent = s["awaiting"]
        logger.info(f"[chat] intent={intent} | message={message[:80]}")

        if intent == "chinh_sua":
            return done(await _revise(s, message))
        if intent == "soan_thao":
            return done(await _draft_party_document(s, message, new_atts))
        if intent in WORKFLOWS:
            return done(await _run_workflow(s, intent, message, cls))
        return done(await _chat(s, message))

    except Exception as ex:
        logger.exception("Lỗi xử lý tin nhắn")
        advice = (
            "Đồng chí thử gửi lại lệnh hoặc chuyển sang mô hình Qwen 2.5 (3B) / DeepSeek-R1 để thử lại."
            if default_ai_client.is_local()
            else "Đồng chí thử gửi lại lệnh. Nếu lỗi lặp lại, kiểm tra kết nối mạng hoặc số dư DeepSeek."
        )
        result = _reply(s, f"❌ Có lỗi khi xử lý: {ex}\n\n{advice}")
        if s["pending"]:
            result["actions"] = _approval_actions(False)
        return done(result)


async def handle_chat_stream(
    session_id: Optional[str],
    message: str,
    action: str = "",
    token: Optional[str] = None,
    attachment_ids: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    """
    Xử lý hội thoại dạng Streaming SSE (Server-Sent Events) dành cho Web Frontend.
    Phát các sự kiện SSE chuẩn:
      - event: meta -> session_id và trích dẫn RAG
      - event: token -> từng chunk văn bản
      - event: done -> kết quả hoàn tất kèm action, file, preview
    """
    session_id, s = get_session(session_id)
    message = (message or "").strip()
    action = (action or "").strip()

    if attachment_ids:
        att_id_set = set(attachment_ids)
        for a in s.get("attachments", []):
            if a.get("id") in att_id_set:
                a["used"] = False

    new_atts = [a for a in s["attachments"] if not a["used"]]
    start_time = time.time()

    # Nạp danh tính cán bộ từ token nếu có
    if token and not s.get("can_bo"):
        try:
            from server.routers.auth import ACTIVE_TOKENS
            from server.services import db_service
            can_bo_info = None
            if token in ACTIVE_TOKENS:
                can_bo_info = ACTIVE_TOKENS[token]["can_bo"]
            else:
                db_s = db_service.get_auth_session(token)
                if db_s:
                    can_bo_info = {
                        "can_bo_id": db_s["can_bo_id"],
                        "ho_ten": db_s["ho_ten"],
                        "chuc_vu": db_s["chuc_vu"],
                        "co_quan": db_s["co_quan"],
                        "co_quan_code": db_s["co_quan_code"],
                        "so_dien_thoai": db_s.get("so_dien_thoai"),
                        "vai_tro": db_s.get("vai_tro", "can_bo"),
                    }
                    ACTIVE_TOKENS[token] = {"can_bo": can_bo_info, "created_at": time.time()}
            if can_bo_info:
                s["authenticated"] = True
                s["can_bo"] = can_bo_info
        except Exception as auth_ex:
            logger.warning(f"Lỗi nạp danh tính từ token (stream): {auth_ex}")

    # Phát event meta khởi tạo
    yield f"event: meta\ndata: {json.dumps({'session_id': session_id, 'status': 'start'}, ensure_ascii=False)}\n\n"

    # Helper ghi nhận kết quả và lưu log
    def _finalize_and_log(result: Dict[str, Any]) -> Dict[str, Any]:
        result["session_id"] = session_id
        can_bo = s.get("can_bo")
        latency_ms = int((time.time() - start_time) * 1000)
        names = ", ".join(a["name"] for a in s["attachments"])
        reply_text = result.get("reply", "")

        if can_bo:
            ho_ten = can_bo.get("ho_ten", "Cán bộ")
            so_dien_thoai = can_bo.get("so_dien_thoai", "")
            co_quan = can_bo.get("co_quan", "Văn phòng Đảng uỷ")
            vai_tro = can_bo.get("vai_tro", "can_bo")
            can_bo_id = can_bo.get("can_bo_id")
        else:
            ho_ten = "Khách (Chưa đăng nhập)"
            so_dien_thoai = ""
            co_quan = "Truy cập Web"
            vai_tro = "khach"
            can_bo_id = None

        is_zalo_session = bool(session_id and str(session_id).startswith("zalo_"))
        if (message or reply_text or action) and not is_zalo_session:
            try:
                from server.services import db_service
                db_service.save_chat_log({
                    "session_id": session_id,
                    "channel": "web",
                    "can_bo_id": can_bo_id,
                    "so_dien_thoai": so_dien_thoai,
                    "ho_ten": ho_ten,
                    "co_quan": co_quan,
                    "vai_tro": vai_tro,
                    "message_text": message or (f"Thao tác: {action}" if action else "(Gửi tệp đính kèm)"),
                    "attachment_names": names,
                    "bot_reply": reply_text,
                    "model_used": getattr(default_ai_client, "model", "gemini-3.5-flash-lite"),
                    "latency_ms": latency_ms,
                    "rag_sources": json.dumps(result.get("rag_sources", []), ensure_ascii=False) if result.get("rag_sources") else "",
                })
            except Exception as log_ex:
                logger.warning(f"Lỗi lưu nhật ký chat stream: {log_ex}")

        _sync_session_to_db(session_id, s)
        return result

    # 0. Lệnh xoá lịch sử
    is_clear_action = action in ("clear_history", "reset", "clear")
    is_clear_cmd = bool(re.search(
        r'^\s*(?:/clear|/reset|xoá\s*lịch\s*sử|xóa\s*lịch\s*sử|xoá\s*tin\s*nhắn|xóa\s*tin\s*nhắn|xoá\s*cuộc\s*trò\s*chuyện|xóa\s*cuộc\s*trò\s*chuyện|xoá\s*hội\s*thoại|xóa\s*hội\s*thoại|làm\s*mới|bắt\s*đầu\s*lại)\s*$',
        message,
        re.IGNORECASE
    ))
    if is_clear_action or is_clear_cmd:
        clear_session_history(session_id, delete_logs_in_db=True)
        reply = (
            "🧹 **ĐÃ XOÁ TOÀN BỘ LỊCH SỬ HỘI THOẠI & LÀM MỚI PHIÊN**\n\n"
            "Toàn bộ ngữ cảnh trao đổi và các tệp đính kèm trước đó đã được dọn sạch hoàn toàn.\n\n"
            "👉 Đồng chí có thể bắt đầu phiên làm việc mới hoặc nhập yêu cầu tham mưu tiếp theo."
        )
        yield f"event: token\ndata: {json.dumps({'chunk': reply}, ensure_ascii=False)}\n\n"
        res = {"session_id": session_id, "reply": reply, "actions": [], "files": [], "preview": []}
        _finalize_and_log(res)
        yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
        return

    # Ghi lịch sử người dùng
    if message or new_atts:
        names = ", ".join(a["name"] for a in new_atts)
        s["history"].append({"role": "user", "content": (message or "(gửi tệp)") + (f"\n[Đính kèm: {names}]" if names else "")})

    try:
        clean_msg = re.sub(r'^\s*\[@[^\]]+\]\s*', '', message)
        clean_msg = re.sub(r'^\s*@Bot(?:\s+VPĐU(?:\s+Công\s+Hải)?)?\s*[:,\-]?\s*', '', clean_msg, flags=re.IGNORECASE)
        clean_msg = re.sub(r'^\s*@[^\s]+\s*', '', clean_msg).strip()
        core_msg = clean_msg.rstrip('.!?,;: ')

        is_confirm = action == "confirm" or (s["pending"] and len(core_msg) < 40 and (CONFIRM_RE.search(core_msg) or CONFIRM_RE.search(message)))
        is_cancel = action == "cancel" or (s["pending"] and len(core_msg) < 40 and (CANCEL_RE.search(core_msg) or CANCEL_RE.search(message)))

        if is_confirm:
            res = _finalize_and_log(_confirm(s))
            yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
            return

        if is_cancel:
            s["pending"] = None
            res = _finalize_and_log(_reply(s, "Đã huỷ dự thảo. Đồng chí cần tôi làm việc gì tiếp theo?"))
            yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
            return

        if not default_ai_client.is_configured():
            msg_warn = "⚠️ Chưa cấu hình API Key (**GEMINI_API_KEY** hoặc **DEEPSEEK_API_KEY**) trong tệp `.env`. Đồng chí điền key rồi khởi động lại hệ thống."
            res = _finalize_and_log(_reply(s, msg_warn))
            yield f"event: token\ndata: {json.dumps({'chunk': msg_warn}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
            return

        if action.startswith("run:") and action[4:] in WORKFLOWS:
            res = _finalize_and_log(await _run_workflow(s, action[4:], message, {}))
            yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
            return

        if not message:
            if not new_atts:
                res = _finalize_and_log(_reply(s, "Đồng chí cần tôi giúp việc gì?"))
                yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
                return
            if s.get("awaiting"):
                res = _finalize_and_log(await _run_workflow(s, s["awaiting"], "", {}))
                yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
                return
            files_desc = "\n".join(f"- **{a['name']}** — nhận diện: {a['category_label']}" for a in new_atts)
            suggested = new_atts[0]["suggested_workflow"]
            actions = [{"id": f"run:{suggested}", "label": f"▶ {WORKFLOWS[suggested]}", "style": "primary"}] if suggested in WORKFLOWS else []
            actions += [{"id": f"run:{k}", "label": v, "style": "ghost"} for k, v in WORKFLOWS.items() if k != suggested]
            res = _finalize_and_log(_reply(s, f"Tôi đã nhận tệp:\n{files_desc}\n\nĐồng chí muốn tôi thực hiện nghiệp vụ nào?", actions=actions))
            yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
            return

        # Phân loại ý định
        cls = await _classify(message, new_atts, bool(s["pending"]))
        intent = cls["intent"]
        if intent == "tro_chuyen" and s.get("awaiting") and new_atts:
            intent = s["awaiting"]
        logger.info(f"[chat-stream] intent={intent} | message={message[:80]}")

        # LUỒNG STREAMING TRỰC TIẾP CHO Ý ĐỊNH TRÒ CHUYỆN & TRA CỨU
        if intent == "tro_chuyen":
            core_rules = get_core_rules()
            local_facts = get_local_knowledge_summary()
            msgs = [{"role": "system", "content": f"{CHAT_SYSTEM_PROMPT}\n\n{core_rules}\n\n{local_facts}"}]

            rag_msgs, citations, _ = _build_rag_context_messages(message, s.get("history", []))
            msgs.extend(rag_msgs)

            # Đính kèm tệp nếu có
            if new_atts:
                att_text = "\n\n".join(f"=== TỆP: {a['name']} ===\n{a['text']}" for a in new_atts)[:MAX_CHAT_ATTACH_CHARS]
                msgs.append({"role": "system", "content": f"Cán bộ đã đính kèm các tệp sau, dùng để trả lời nếu liên quan:\n\n{att_text}"})
            msgs.extend(s["history"][-10:])

            # Cập nhật danh sách citations qua event meta nếu có
            unique_citations = []
            if citations:
                seen_so_hieu = set()
                for c in citations:
                    so = (c.get("so_hieu") or "").strip()
                    if so and so not in seen_so_hieu:
                        seen_so_hieu.add(so)
                        unique_citations.append(c)
                yield f"event: meta\ndata: {json.dumps({'session_id': session_id, 'rag_sources': unique_citations}, ensure_ascii=False)}\n\n"

            # Bắt đầu stream từng token từ LLM
            chunks = []
            async for chunk in default_ai_client.stream_chat_async(msgs, temperature=0.3, max_tokens=2000):
                chunks.append(chunk)
                yield f"event: token\ndata: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"

            web_sources = default_ai_client.get_last_web_sources()

            full_reply = "".join(chunks).strip() or "Xin lỗi, tôi chưa có câu trả lời."
            disclaimer = "\n\n*Lưu ý: Cán bộ tham mưu chịu trách nhiệm toàn diện về tính chính xác và tính pháp lý của thông tin khi sử dụng thông tin từ AI.*"
            if disclaimer.strip() not in full_reply:
                full_reply += disclaimer
                yield f"event: token\ndata: {json.dumps({'chunk': disclaimer}, ensure_ascii=False)}\n\n"

            res = _reply(
                s,
                full_reply,
                rag_sources=unique_citations if citations else [],
                web_sources=web_sources if web_sources else [],
            )
            _finalize_and_log(res)
            yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
            return

        # VỚI CÁC Ý ĐỊNH SOẠN THẢO / CHỈNH SỬA / WORKFLOWS
        if intent == "chinh_sua":
            res = _finalize_and_log(await _revise(s, message))
        elif intent == "soan_thao":
            res = _finalize_and_log(await _draft_party_document(s, message, new_atts))
        elif intent in WORKFLOWS:
            res = _finalize_and_log(await _run_workflow(s, intent, message, cls))
        else:
            res = _finalize_and_log(await _chat(s, message))

        yield f"event: token\ndata: {json.dumps({'chunk': res.get('reply', '')}, ensure_ascii=False)}\n\n"
        yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"

    except Exception as ex:
        logger.exception("Lỗi xử lý tin nhắn stream")
        advice = (
            "Đồng chí thử gửi lại lệnh hoặc chuyển sang mô hình Qwen 2.5 (3B) / DeepSeek-R1 để thử lại."
            if default_ai_client.is_local()
            else "Đồng chí thử gửi lại lệnh. Nếu lỗi lặp lại, kiểm tra kết nối mạng hoặc số dư DeepSeek."
        )
        err_msg = f"❌ Có lỗi khi xử lý: {ex}\n\n{advice}"
        res = _finalize_and_log(_reply(s, err_msg))
        if s["pending"]:
            res["actions"] = _approval_actions(False)
        yield f"event: token\ndata: {json.dumps({'chunk': err_msg}, ensure_ascii=False)}\n\n"
        yield f"event: done\ndata: {json.dumps(res, ensure_ascii=False)}\n\n"
