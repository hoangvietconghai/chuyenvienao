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

import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from server.ai_connector import default_ai_client
from server.config import BASE_DIR
from server.prompts.chat_mode import CHAT_SYSTEM_PROMPT
from server.prompts.intent_router import get_intent_messages, get_revise_messages
from server.workflows.wf1_synthesizer import analyze_weekly_reports, generate_weekly_report_docx
from server.workflows.wf2_conclusions import analyze_meeting_notes, generate_meeting_conclusion_docx
from server.workflows.wf3_dispatch import analyze_provincial_directive, generate_dispatch_docx
from server.workflows.wf4_appraisal import analyze_agency_draft, generate_appraisal_documents

logger = logging.getLogger("chat_engine")

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

def get_session(session_id: Optional[str]) -> (str, Dict[str, Any]):
    if not session_id or session_id not in SESSIONS:
        session_id = session_id or uuid.uuid4().hex
        SESSIONS[session_id] = {"history": [], "attachments": [], "pending": None, "awaiting": None}
    return session_id, SESSIONS[session_id]


def reset_session(session_id: Optional[str]) -> str:
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    new_id, _ = get_session(None)
    return new_id


def add_attachment(session_id: Optional[str], routing_result: Dict[str, Any]) -> (str, Dict[str, Any]):
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


def _keyword_intent(message: str, new_atts: List[Dict], has_pending: bool) -> str:
    """Phân loại dự phòng bằng từ khoá khi DeepSeek lỗi."""
    m = message.lower()
    if has_pending and re.search(r"\b(sửa|đổi|thêm|bớt|bỏ|thay)\b", m):
        return "chinh_sua"
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
        valid = set(WORKFLOWS) | {"chinh_sua", "tro_chuyen"}
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
    # Nếu cán bộ dán nội dung dài trực tiếp vào khung chat thì dùng luôn làm đầu vào
    if len(message) > 200 or not unique_atts:
        if len(message) > 200:
            parts.append(f"=============== NỘI DUNG CÁN BỘ NHẬP TRỰC TIẾP ===============\n{message}")
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

async def _run_workflow(s: Dict[str, Any], wf: str, message: str, params: Dict[str, str]) -> Dict[str, Any]:
    new_atts = [a for a in s["attachments"] if not a["used"]]
    input_text = _build_input_text(message, new_atts)

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


def _confirm(s: Dict[str, Any]) -> Dict[str, Any]:
    pending = s["pending"]
    if not pending:
        return _reply(s, "Hiện không có dự thảo nào đang chờ duyệt.")
    wf, data = pending["workflow"], pending["data"]

    files = []
    if wf == "wf4_tham_dinh":
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

    s["pending"] = None
    return _reply(
        s,
        f"📄 Đã xuất **{len(files)}** tệp Word chuẩn thể thức Hướng dẫn 05-HD/VPTW. "
        "Đồng chí tải về, kiểm tra lại lần cuối trước khi trình ký.\n\n"
        "*Lưu ý: Đây là dự thảo tham mưu — việc ban hành, ký số do cán bộ trực tiếp thực hiện.*",
        files=files,
    )


async def _chat(s: Dict[str, Any], message: str) -> Dict[str, Any]:
    msgs = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    new_atts = [a for a in s["attachments"] if not a["used"]]
    if new_atts:
        att_text = "\n\n".join(f"=== TỆP: {a['name']} ===\n{a['text']}" for a in new_atts)[:MAX_CHAT_ATTACH_CHARS]
        msgs.append({"role": "system", "content": f"Cán bộ đã đính kèm các tệp sau, dùng để trả lời nếu liên quan:\n\n{att_text}"})
    msgs.extend(s["history"][-10:])
    res = await default_ai_client.call_chat_async(msgs, temperature=0.3, max_tokens=2000, json_mode=False)
    return _reply(s, res.get("content", "").strip() or "Xin lỗi, tôi chưa có câu trả lời.")


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
