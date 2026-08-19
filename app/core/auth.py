import os


def configured_admin_ids() -> set[str]:
    return {
        value.strip()
        for value in os.getenv("LINE_ADMIN_USER_IDS", "").split(",")
        if value.strip()
    }


def is_admin(user_id: str | None) -> bool:
    admin_ids = configured_admin_ids()
    # รักษาพฤติกรรมติดตั้งครั้งแรกของระบบเดิม
    return not admin_ids or user_id in admin_ids


def is_configured_admin(user_id: str | None) -> bool:
    """คำสั่งที่เกี่ยวกับความเป็นส่วนตัวต้องตั้ง admin ID จริงก่อน"""
    admin_ids = configured_admin_ids()
    return bool(admin_ids) and user_id in admin_ids
