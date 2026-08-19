"""Worker สำหรับส่งข่าวรายวัน

ทดสอบหนึ่งรอบ: python -m app.workers.daily_digest_worker --once
รันตามเวลา:    python -m app.workers.daily_digest_worker
"""
import argparse
import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from app.daily_digest import send_daily_digest


def build_scheduler() -> BlockingScheduler:
    hour = int(os.getenv("DAILY_DIGEST_HOUR", "8"))
    minute = int(os.getenv("DAILY_DIGEST_MINUTE", "0"))
    scheduler = BlockingScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(
        send_daily_digest,
        CronTrigger(hour=hour, minute=minute),
        id="daily_digest",
        replace_existing=True,
    )
    return scheduler


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    parser = argparse.ArgumentParser(description="LINE daily digest worker")
    parser.add_argument("--once", action="store_true", help="ส่งหนึ่งรอบแล้วจบ")
    args = parser.parse_args()
    if args.once:
        print(f"ส่งสำเร็จ {send_daily_digest()} แชท")
        return
    build_scheduler().start()


if __name__ == "__main__":
    main()
