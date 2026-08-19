"""สร้างและส่งสรุปรายวัน โดยไม่ผูกกับ web process หรือ scheduler ตัวใดตัวหนึ่ง"""
import logging


logger = logging.getLogger(__name__)


def _looks_like_ticker(topic: str) -> str | None:
    candidate = topic.strip().upper().replace(" ", "")
    if 1 <= len(candidate) <= 12 and all(c.isalnum() or c in ".-" for c in candidate):
        if " " not in topic.strip():
            return candidate
    return None


def send_daily_digest(repository=None, news_provider=None, stock_provider=None, sender=None) -> int:
    """ส่งให้ทุกแชทที่สมัครไว้ และคืนจำนวนข้อความที่ส่งสำเร็จ"""
    if repository is None:
        from app import storage as repository
    if news_provider is None:
        from app import news as news_provider
    if stock_provider is None:
        from app import stock as stock_provider
    if sender is None:
        from app.line_client import push_text as sender

    sent = 0
    for chat_id, chat in repository.all_chats().items():
        if not chat.get("subscribed_daily"):
            continue

        parts = [
            news_provider.format_plain(
                "ข่าวเด่นวันนี้",
                news_provider.fetch_headlines(query=None, limit=5),
            )
        ]
        for topic in chat.get("topics", []):
            ticker = _looks_like_ticker(topic)
            if ticker:
                parts.append(stock_provider.get_stock_price(ticker))
            else:
                items = news_provider.fetch_headlines(query=topic, limit=3)
                parts.append(news_provider.format_plain(f"ติดตาม: {topic}", items))

        try:
            sender(chat_id, "\n\n".join(parts))
            sent += 1
        except Exception:
            logger.exception("ส่งสรุปรายวันไปที่ %s ไม่สำเร็จ", chat_id)
    return sent
