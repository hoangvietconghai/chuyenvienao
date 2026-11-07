# -*- coding: utf-8 -*-
"""
server/services/scheduler_service.py
====================================
Bộ lập lịch tự động (Autonomous Administrative Scheduler) cho Văn phòng Đảng uỷ xã Công Hải.
Hỗ trợ:
1. Cơ chế Khởi động bù (catch_up_missed_jobs): Chạy ngay khi máy tính bật lên lúc sáng, bù các lịch bị bỏ lỡ.
2. 07h30 Hàng ngày: Quét nhiệm vụ đến hạn hôm nay & ngày mai -> gửi thông báo đôn đốc (Digest Reminder).
3. 16h30 Hàng ngày: Cảnh báo nhiệm vụ quá hạn chưa hoàn thành cho Chánh Văn phòng & Thường trực.
4. 08h00 Sáng Thứ Sáu: Nhắc UBND xã và 08 thôn gửi Báo cáo tuần trước 11h00.
5. 08h00 Ngày 23 hàng tháng: Nhắc Bộ phận CĐS cập nhật số liệu NQ57 trước ngày 25.
6. Chống gửi lặp bằng khoá acquire_remind_lock trong CSDL SQLite WAL.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from server.logger import get_logger
from server.services import db_service
from server.services import zalo_api

logger = get_logger("scheduler_service")

# Biến cờ kiểm soát vòng lặp scheduler
_SCHEDULER_RUNNING = False
_SCHEDULER_TASK: Optional[asyncio.Task] = None


def _format_task_digest(agency_name: str, tasks: List[Dict[str, Any]], title: str) -> str:
    """Đóng gói danh sách nhiều việc thành một tin nhắn Digest duy nhất cho một cơ quan."""
    lines = [
        f"📋 **{title.upper()}**",
        f"🏛️ **Cơ quan:** {agency_name}",
        f"📅 **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        f"Hiện có **{len(tasks)} đầu việc** cần lưu ý:",
    ]
    for idx, t in enumerate(tasks, 1):
        deadline = t.get("deadline_date", "Chưa rõ")
        nd = t.get("noi_dung_nhiem_vu", "")
        sh = t.get("so_hieu_vb", "")
        sh_str = f" (theo {sh})" if sh else ""
        lines.append(f"{idx}. **Hạn {deadline}:** {nd}{sh_str}")

    lines.append("")
    lines.append("👉 *Kính đề nghị đồng chí quan tâm chỉ đạo thực hiện đúng tiến độ.*")
    return "\n".join(lines)


async def check_morning_reminders() -> int:
    """Quét các nhiệm vụ đến hạn hôm nay hoặc ngày mai để gửi tin đôn đốc buổi sáng."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # Lấy các nhiệm vụ chưa hoàn thành
    active_tasks = db_service.get_tasks(limit=300)
    due_tasks = [
        t for t in active_tasks
        if t.get("trang_thai") not in ["Hoàn thành"] and t.get("deadline_date") in [today_str, tomorrow_str]
    ]

    if not due_tasks:
        logger.info("[Scheduler] Sáng nay không có nhiệm vụ nào đến hạn cần nhắc.")
        return 0

    # Gom nhóm theo cơ quan chủ trì
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for t in due_tasks:
        cq_code = t.get("co_quan_chu_tri_code", "UBND")
        grouped.setdefault(cq_code, []).append(t)

    sent_count = 0
    for cq_code, tasks in grouped.items():
        remind_key = f"MORNING_{today_str}_{cq_code}"
        # Giành khoá chống gửi lặp
        if db_service.acquire_remind_lock(remind_key, None, None, "DUE_SOON"):
            cq_name = tasks[0].get("co_quan_chu_tri", cq_code)
            msg = _format_task_digest(cq_name, tasks, "Nhắc việc đến hạn trong ngày")

            # Gửi tin nhắn qua Zalo (nếu cán bộ/cơ quan có cấu hình zalo_chat_id)
            cadres = db_service.get_cadres_by_agency(cq_code)
            for c in cadres:
                chat_id = c.get("zalo_chat_id")
                if chat_id:
                    zalo_api.send_message(chat_id, msg)

            logger.info(f"[Scheduler] Đã gửi nhắc việc buổi sáng cho {cq_name} ({len(tasks)} việc).")
            sent_count += 1

    return sent_count


async def check_afternoon_overdue() -> int:
    """Quét các nhiệm vụ quá hạn chưa hoàn thành lúc 16h30 chiều."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    active_tasks = db_service.get_tasks(limit=300)
    overdue_tasks = [
        t for t in active_tasks
        if t.get("trang_thai") not in ["Hoàn thành"] and t.get("deadline_date") < today_str
    ]

    if not overdue_tasks:
        logger.info("[Scheduler] Chiều nay không có nhiệm vụ nào quá hạn.")
        return 0

    remind_key = f"AFTERNOON_OVERDUE_{today_str}"
    if db_service.acquire_remind_lock(remind_key, None, None, "OVERDUE"):
        summary_lines = [
            "⚠️ **BÁO CÁO NHIỆM VỤ QUÁ HẠN CHƯA HOÀN THÀNH**",
            f"📅 **Thời điểm:** {now.strftime('%d/%m/%Y %H:%M')}",
            f"Tổng số: **{len(overdue_tasks)} nhiệm vụ quá hạn**:",
            "",
        ]
        for idx, t in enumerate(overdue_tasks[:10], 1):
            cq = t.get("co_quan_chu_tri", "")
            dl = t.get("deadline_date", "")
            nd = t.get("noi_dung_nhiem_vu", "")[:100]
            summary_lines.append(f"{idx}. [{cq}] Hạn {dl}: {nd}...")

        summary_msg = "\n".join(summary_lines)

        # Gửi cho Thường trực Đảng uỷ & Chánh Văn phòng
        leadership = db_service.get_leadership_cadres()
        for l in leadership:
            cid = l.get("zalo_chat_id")
            if cid:
                zalo_api.send_message(cid, summary_msg)

        logger.info(f"[Scheduler] Đã cảnh báo {len(overdue_tasks)} nhiệm vụ quá hạn cho Thường trực.")
        return 1

    return 0


async def check_friday_weekly_report() -> bool:
    """Nhắc nộp Báo cáo tuần vào sáng thứ Sáu lúc 08h00."""
    now = datetime.now()
    if now.weekday() != 4:  # Thứ Sáu là 4 (Thứ Hai = 0)
        return False

    today_str = now.strftime("%Y-%m-%d")
    remind_key = f"FRIDAY_REPORT_{today_str}"

    if db_service.acquire_remind_lock(remind_key, None, None, "WEEKLY_REPORT"):
        msg = (
            "📢 **ĐÔN ĐỐC NỘP BÁO CÁO TUẦN VĂN PHÒNG ĐẢNG UỶ**\n\n"
            "Kính gửi các cơ quan chuyên môn và các Chi bộ trực thuộc:\n"
            "- Đề nghị UBND xã, Ban Xây dựng Đảng, UBKT, MTTQ và **08 Chi bộ thôn** "
            "khẩn trương hoàn thiện và gửi Báo cáo công tác tuần về Văn phòng Đảng uỷ **trước 11h00 sáng nay** "
            "để tổng hợp phục vụ cuộc họp giao ban Thường trực Đảng uỷ chiều nay.\n\n"
            "Trân trọng cảm ơn các đồng chí!"
        )
        cadres = db_service.get_all_can_bo(only_active=True)
        for c in cadres:
            cid = c.get("zalo_chat_id")
            if cid:
                zalo_api.send_message(cid, msg)

        logger.info("[Scheduler] Đã gửi thông báo đôn đốc báo cáo tuần sáng thứ Sáu.")
        return True

    return False


async def check_monthly_cds_report() -> bool:
    """Nhắc nhở cập nhật số liệu Chuyển đổi số & NQ57 vào ngày 23 hàng tháng."""
    now = datetime.now()
    if now.day != 23:
        return False

    today_str = now.strftime("%Y-%m-%d")
    remind_key = f"MONTHLY_CDS_{today_str}"

    if db_service.acquire_remind_lock(remind_key, None, None, "MONTHLY_25"):
        msg = (
            "🚀 **NHẮC VIỆC: CẬP NHẬT SỐ LIỆU CHUYỂN ĐỔI SỐ (NQ 57-NQ/TW)**\n\n"
            "Kính gửi Tổ Chuyên trách Chuyển đổi số & Đề án 06 xã Công Hải:\n"
            "- Đề nghị các đồng chí rà soát, cập nhật số liệu tiến độ các chỉ tiêu lên hệ thống **theodoinq.dcs.vn**;\n"
            "- Xử lý dứt điểm các kiến nghị trên cổng **pakn.nq57.vn** trước hạn chót **ngày 25 hàng tháng**.\n\n"
            "Văn phòng Đảng uỷ trân trọng thông báo."
        )
        cadres = db_service.get_cadres_by_agency("VPDU") + db_service.get_cadres_by_agency("UBND")
        for c in cadres:
            cid = c.get("zalo_chat_id")
            if cid:
                zalo_api.send_message(cid, msg)

        logger.info("[Scheduler] Đã gửi thông báo nhắc số liệu CĐS ngày 23.")
        return True

    return False


async def catch_up_missed_jobs():
    """
    CƠ CHẾ KHỞI ĐỘNG BÙ (CATCH-UP):
    Khi bật máy lúc 08h30 sáng (hoặc sau khi khởi động server),
    hệ thống lập tức quét xem sáng nay đã gửi nhắc việc chưa; nếu chưa thì bù ngay!
    """
    logger.info("[Scheduler] Bắt đầu kiểm tra và thực hiện khởi động bù (catch-up)...")
    try:
        now = datetime.now()
        # 1. Nếu bật máy sau 07h30 sáng, bù nhắc việc sáng
        if now.hour >= 7:
            await check_morning_reminders()

        # 2. Nếu là Thứ Sáu và bật máy sau 08h00, bù nhắc báo cáo tuần
        if now.weekday() == 4 and now.hour >= 8:
            await check_friday_weekly_report()

        # 3. Nếu là ngày 23 và bật máy sau 08h00, bù nhắc CĐS
        if now.day == 23 and now.hour >= 8:
            await check_monthly_cds_report()

        # 4. Nếu bật máy sau 16h30 chiều, bù cảnh báo quá hạn
        if now.hour >= 16:
            await check_afternoon_overdue()

        logger.info("[Scheduler] Khởi động bù hoàn tất thành công.")
    except Exception as ex:
        logger.warning(f"[Scheduler] Lỗi trong quá trình khởi động bù: {ex}")


async def _scheduler_loop():
    """Vòng lặp chạy nền định kỳ mỗi 60 giây kiểm tra các mốc thời gian."""
    global _SCHEDULER_RUNNING
    _SCHEDULER_RUNNING = True

    # 1. Chạy khởi động bù ngay khi khởi động
    await catch_up_missed_jobs()

    logger.info("[Scheduler] Bộ hẹn giờ tự động đã kích hoạt và đang giám sát...")
    while _SCHEDULER_RUNNING:
        try:
            now = datetime.now()
            current_hm = now.strftime("%H:%M")

            # 07h30 sáng
            if current_hm == "07:30":
                await check_morning_reminders()

            # 08h00 sáng Thứ Sáu
            if current_hm == "08:00":
                await check_friday_weekly_report()
                await check_monthly_cds_report()

            # 16h30 chiều
            if current_hm == "16:30":
                await check_afternoon_overdue()

        except Exception as ex:
            logger.error(f"[Scheduler] Lỗi trong vòng lặp scheduler: {ex}")

        # Ngủ 60 giây trước lần kiểm tra tiếp theo
        await asyncio.sleep(60)


def start_scheduler():
    """Khởi động bộ lập lịch nền (gắn vào FastAPI startup event)."""
    global _SCHEDULER_TASK
    if _SCHEDULER_TASK is None or _SCHEDULER_TASK.done():
        _SCHEDULER_TASK = asyncio.create_task(_scheduler_loop())
        logger.info("[Scheduler] Đã đăng ký tác vụ nền cho Bộ hẹn giờ tự động.")


def stop_scheduler():
    """Dừng bộ lập lịch khi server tắt."""
    global _SCHEDULER_RUNNING, _SCHEDULER_TASK
    _SCHEDULER_RUNNING = False
    if _SCHEDULER_TASK:
        _SCHEDULER_TASK.cancel()
        _SCHEDULER_TASK = None
        logger.info("[Scheduler] Đã dừng Bộ hẹn giờ tự động.")
