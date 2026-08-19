"""Compatibility imports; ใช้ Worker แยกแทน scheduler ใน web process"""
from app.daily_digest import send_daily_digest
from app.workers.daily_digest_worker import build_scheduler


def start_scheduler():
    scheduler = build_scheduler()
    scheduler.start()
    return scheduler
