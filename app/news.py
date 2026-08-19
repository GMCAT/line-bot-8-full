"""ระบบข่าวจาก Google News RSS จัดรูปแบบด้วย Python และไม่เรียก AI"""
import urllib.parse


def fetch_headlines(query: str | None = None, limit: int = 5) -> list[dict]:
    """
    ดึงหัวข้อข่าวจาก Google News RSS
    query=None -> ข่าวเด่นทั่วไป (ประเทศไทย)
    query="คำค้น" -> ข่าวตามคำค้นนั้น
    """
    import feedparser

    if query:
        q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=th&gl=TH&ceid=TH:th"
    else:
        url = "https://news.google.com/rss?hl=th&gl=TH&ceid=TH:th"

    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        items.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": entry.get("source", {}).get("title", "") if hasattr(entry, "source") else "",
        })
    return items


def _format_plain(topic_label: str, headlines: list[dict]) -> str:
    """โหมดฟรี 100% — จัดรูปแบบข่าวด้วย Python ธรรมดา ไม่พึ่ง AI เลย"""
    lines = [f"🗞️ {topic_label}"]
    for h in headlines:
        source = f" ({h['source']})" if h["source"] else ""
        lines.append(f"• {h['title']}{source}\n  {h['link']}")
    return "\n".join(lines)


def format_plain(topic_label: str, headlines: list[dict]) -> str:
    """Public interface สำหรับ News Service; ไม่เรียก AI"""
    if not headlines:
        return f"ไม่พบข่าวล่าสุดเกี่ยวกับ \"{topic_label}\" ครับ"
    return _format_plain(topic_label, headlines)
