import os


DEFAULT_SERVICES = {
    "news",
    "stocks",
    "ai_chat",
    "conversation_memory",
    "group_reports",
    "contacts",
    "subscriptions",
    "admin",
    "settings",
    "help",
    "unknown",
}


def enabled_services(bot_id: str = "default") -> set[str]:
    """รองรับรายบอท เช่น BOT_SERVICES_NEWS_BOT=news,help,unknown"""
    key = "BOT_SERVICES_" + bot_id.upper().replace("-", "_")
    raw = os.getenv(key) or os.getenv("BOT_SERVICES", ",".join(sorted(DEFAULT_SERVICES)))
    return {item.strip() for item in raw.split(",") if item.strip()}
