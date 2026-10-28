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
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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

SESSIONS: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# QUẢN LÝ PHIÊN
# ==============================================================================

def get_session(session_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    if not session_id or session_id not in SESSIONS:
        session_id = session_id or uuid.uuid4().hex
        SESSIONS[session_id] = {"history": [], "attachments": [], "pending": None, "awaiting": None}
    return session_id, SESSIONS[session_id]


def reset_session(session_id: Optional[str]) -> str:
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    new_id, _ = get_session(None)
    return new_id


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
    return session_id, att


def remove_attachment(session_id: str, attachment_id: str) -> bool:
    _, s = get_session(session_id)
    before = len(s["attachments"])
    s["attachments"] = [a for a in s["attachments"] if a["id"] != attachment_id]
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

Nhiệm vụ: Căn cứ vào yêu cầu chỉ đạo của cán bộ và tài liệu đính kèm (nếu có), hãy soạn thảo văn bản Đảng hoàn chỉnh, chuẩn mực theo Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.

QUY TẮC BẮT BUỘC:
1. Mô hình 2 cấp: Tỉnh Khánh Hoà -> Xã Công Hải. TUYỆT ĐỐI KHÔNG CÒN CẤP HUYỆN.
2. Thẩm quyền & Người ký chuẩn:
   - Ban Thường vụ Đảng uỷ: T/M BAN THƯỜNG VỤ, Bí thư Vũ Thị Thuỳ Trang hoặc Phó Bí thư Nguyễn Xuân Hoàng.
   - Ban Chấp hành Đảng bộ: T/M ĐẢNG UỶ, Bí thư Vũ Thị Thuỳ Trang.
   - Văn phòng Đảng uỷ: K/T CHÁNH VĂN PHÒNG (hoặc CHÁNH VĂN PHÒNG) - Hoàng Việt Long.
3. 5 cơ quan chuyên môn cấp xã: Uỷ ban nhân dân xã, Ban Xây dựng Đảng, Uỷ ban Kiểm tra Đảng uỷ, Cơ quan UBMTTQVN xã, Văn phòng Đảng uỷ.
4. Đơn vị hành chính: Gồm 08 thôn chính thức: Bình Tiên, Ma Trai, Suối Vang, Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng.
5. Chính tả khối Đảng: oà, uỷ, uý (Đảng uỷ, Khánh Hoà, Uỷ ban). Ngày tháng dạng dd/mm/yyyy.
6. Thể loại văn bản (doc_type): CV (Công văn), KH (Kế hoạch), BC (Báo cáo), TB (Thông báo), QD (Quyết định), NQ (Nghị quyết), TTr (Tờ trình), CT (Chỉ thị), CTR (Chương trình).
   - Nếu là Công văn (CV) hoặc Tờ trình (TTr): CÓ mục "kinh_gui".
   - Nếu là Kế hoạch (KH), Báo cáo (BC), Thông báo (TB), Quyết định (QD), Nghị quyết (NQ): KHÔNG có kính gửi (kinh_gui để mảng rỗng []).
   - Quyết định (QD): Bắt buộc chia Điều (Điều 1, Điều 2...).
   - Nghị quyết (NQ), Công văn (CV): Tuyệt đối không chia Điều.

ĐẦU RA BẮT BUỘC DẠNG JSON với đúng 2 trường:
{
  "summary": "Tóm tắt ngắn gọn tham mưu để gửi tin nhắn Zalo (gồm: Thể loại văn bản, Trích yếu, Cơ quan chủ trì/thực hiện, Nhiệm vụ trọng tâm, Thời hạn báo cáo/hoàn thành)",
  "doc_payload": {
    "doc_type": "CV",
    "so_hieu": "Số      -CV/ĐU",
    "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
    "trich_yeu": "V/v tham mưu công tác tuyên truyền...",
    "tieu_de": "Tiêu đề văn bản (nếu là KH, BC, TB, NQ, QD...)",
    "kinh_gui": ["Ban Xây dựng Đảng xã."],
    "noi_dung": [
      "Đoạn 1 nêu căn cứ, bối cảnh, lý do...",
      "1. **Chủ trì, phối hợp với...**: nội dung...",
      "2. **Thời hạn**: hoàn thành trước ngày...",
      "Đoạn kết thúc yêu cầu thực hiện..."
    ],
    "noi_nhan": [
      "- Như trên;",
      "- Thường trực Đảng uỷ;",
      "- Lưu VPĐU."
    ],
    "tham_quyen": "T/M BAN THƯỜNG VỤ",
    "chuc_vu": "PHÓ BÍ THƯ",
    "nguoi_ky": "Nguyễn Xuân Hoàng"
  }
}
"""


def _normalize_doc_type(raw: str) -> str:
    r = (raw or "").upper().strip()
    if "CV" in r or "CÔNG VĂN" in r or "GIAO VIỆC" in r:
        return "CV"
    if "KH" in r or "KẾ HOẠCH" in r:
        return "KH"
    if "TB" in r or "THÔNG BÁO" in r:
        return "TB"
    if "KL" in r or "KẾT LUẬN" in r:
        return "KL"
    if "BC" in r or "BÁO CÁO" in r:
        return "BC"
    if "TTR" in r or "TỜ TRÌNH" in r:
        return "TTr"
    if "QĐ" in r or "QD" in r or "QUYẾT ĐỊNH" in r:
        return "QD"
    if "NQ" in r or "NGHỊ QUYẾT" in r:
        return "NQ"
    if "CT" in r or "CHỈ THỊ" in r:
        return "CT"
    if "CTR" in r or "CHƯƠNG TRÌNH" in r:
        return "CTR"
    return "CV"


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
        lines.append("- Tệp dự thảo đã chuẩn hoá kỹ thuật thể thức theo Hướng dẫn số 05-HD/VPTW")
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
    context_text = _build_input_text(message, new_atts)
    detected_type = _normalize_doc_type(message)
    knowledge_context = build_system_knowledge_prompt(detected_type, include_local=True)

    messages = [
        {"role": "system", "content": f"{DRAFT_SYSTEM_PROMPT}\n\n{knowledge_context}"},
        {"role": "user", "content": f"Yêu cầu của cán bộ:\n{context_text}"},
    ]
    res = await default_ai_client.call_chat_async(messages, temperature=0.2, max_tokens=4000, json_mode=True)
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
    return _reply(s, reply_text, actions=_approval_actions(False))


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
        f"📄 Đã xuất **{len(files)}** tệp Word chuẩn thể thức Hướng dẫn 05-HD/VPTW. "
        "Đồng chí tải về, kiểm tra lại lần cuối trước khi trình ký."
        f"{task_notice}\n\n"
        "*Lưu ý: Đây là dự thảo tham mưu — việc ban hành, ký số do cán bộ trực tiếp thực hiện.*",
        files=files,
    )


async def _chat(s: Dict[str, Any], message: str) -> Dict[str, Any]:
    core_rules = get_core_rules()
    local_facts = get_local_knowledge_summary()
    msgs = [{"role": "system", "content": f"{CHAT_SYSTEM_PROMPT}\n\n{core_rules}\n\n{local_facts}"}]

    # 1. Truy xuất Hybrid RAG từ Kho văn bản cấp uỷ (Giỏ Ngữ Cảnh 2 - 4 - 2)
    citations = []
    try:
        from server.services.rag_service import retrieve_hybrid_context
        rag_res = retrieve_hybrid_context(message, max_slots=6)
        if rag_res.get("context_text"):
            msgs.append({"role": "system", "content": f"Dữ liệu tra cứu thực chứng từ Kho văn bản Đảng uỷ & UBND xã:\n{rag_res['context_text']}"})
            citations = rag_res.get("citations", [])
    except Exception as ex:
        logger.warning(f"Lỗi khi tra cứu Hybrid RAG: {ex}")

    new_atts = [a for a in s["attachments"] if not a["used"]]
    if new_atts:
        att_text = "\n\n".join(f"=== TỆP: {a['name']} ===\n{a['text']}" for a in new_atts)[:MAX_CHAT_ATTACH_CHARS]
        msgs.append({"role": "system", "content": f"Cán bộ đã đính kèm các tệp sau, dùng để trả lời nếu liên quan:\n\n{att_text}"})
    msgs.extend(s["history"][-10:])
    res = await default_ai_client.call_chat_async(msgs, temperature=0.3, max_tokens=2000, json_mode=False)

    reply_content = res.get("content", "").strip() or "Xin lỗi, tôi chưa có câu trả lời."
    # Bổ sung trích dẫn nguồn RAG ở cuối câu trả lời nếu có
    if citations:
        cite_lines = ["\n\n📚 **Căn cứ tra cứu thực chứng từ Kho văn bản:**"]
        for c in citations[:3]:
            cite_lines.append(f"• **{c['so_hieu']}** ({c['tier']}): *{c['trich_yeu']}*")
        reply_content += "\n".join(cite_lines)

    return _reply(s, reply_content)


# ==============================================================================
# HÀM CÔNG KHAI
# ==============================================================================

async def handle_chat(session_id: Optional[str], message: str = "", action: str = "") -> Dict[str, Any]:
    session_id, s = get_session(session_id)
    message = (message or "").strip()
    action = (action or "").strip()
    new_atts = [a for a in s["attachments"] if not a["used"]]

    def done(result: Dict[str, Any]) -> Dict[str, Any]:
        result["session_id"] = session_id
        return result

    # Ghi lịch sử phía người dùng
    if message or new_atts:
        names = ", ".join(a["name"] for a in new_atts)
        s["history"].append({"role": "user", "content": (message or "(gửi tệp)") + (f"\n[Đính kèm: {names}]" if names else "")})

    try:
        # 1. Nút bấm / lệnh duyệt - huỷ
        if action == "confirm" or (s["pending"] and len(message) < 40 and CONFIRM_RE.search(message)):
            return done(_confirm(s))
        if action == "cancel" or (s["pending"] and len(message) < 40 and CANCEL_RE.search(message)):
            s["pending"] = None
            return done(_reply(s, "Đã huỷ dự thảo. Đồng chí cần tôi làm việc gì tiếp theo?"))

        if not default_ai_client.is_configured():
            return done(_reply(s, "⚠️ Chưa cấu hình **DEEPSEEK_API_KEY** trong tệp `.env`. Đồng chí điền key rồi khởi động lại hệ thống."))

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
