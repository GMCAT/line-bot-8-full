import logging
import os

from dotenv import load_dotenv

load_dotenv()  # โหลดค่าจาก .env ก่อน import โมดูลอื่นที่ต้องใช้ env vars

from fastapi import FastAPI, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import JoinEvent, LeaveEvent, MessageEvent, TextMessageContent

from app import line_client, storage
from app.core.bot_config import enabled_services
from app.core.contracts import ServiceRequest
from app.services import build_registry


app = FastAPI(title="LINE News Assistant")
parser = WebhookParser(os.environ["LINE_CHANNEL_SECRET"])
service_registry = build_registry()
logger = logging.getLogger(__name__)


def _safe_state_write(operation, *args) -> None:
    """Neon ล่มต้องไม่ทำให้ข่าว/หุ้น/Help และ Service อื่นหยุดตอบ"""
    try:
        operation(*args)
    except Exception:
        logger.exception("บันทึกสถานะบอทลงฐานข้อมูลไม่สำเร็จ")


def _get_chat_id(event: MessageEvent | JoinEvent) -> tuple[str, str]:
    source = event.source
    if source.type == "group":
        return source.group_id, "group"
    if source.type == "room":
        return source.room_id, "room"
    return source.user_id, "user"


def _extract_self_mention(message: TextMessageContent) -> tuple[bool, str]:
    """คืนค่า (แท็กบอทหรือไม่, ข้อความหลังตัด mention)"""
    text = message.text
    mention = message.mention
    if not mention or not mention.mentionees:
        return False, text

    self_mentions = [
        mentionee
        for mentionee in mention.mentionees
        if getattr(mentionee, "type", None) == "user"
        and getattr(mentionee, "is_self", False)
    ]
    if not self_mentions:
        return False, text

    for mentionee in sorted(self_mentions, key=lambda item: item.index, reverse=True):
        text = text[:mentionee.index] + text[mentionee.index + mentionee.length:]
    return True, text.strip()


def _match_trigger_keyword(text: str) -> tuple[bool, str]:
    """รองรับคำนำหน้าในกลุ่ม เช่น บอท, bot และ !"""
    keywords = [
        keyword.strip()
        for keyword in os.getenv("GROUP_TRIGGER_KEYWORDS", "บอท,bot,!").split(",")
        if keyword.strip()
    ]
    lowered = text.lower()
    for keyword in keywords:
        if lowered.startswith(keyword.lower()):
            return True, text[len(keyword):].strip()
    return False, text


def handle_command(
    chat_id: str,
    text: str,
    user_id: str | None,
    bot_id: str = "default",
    chat_type: str = "user",
) -> str | list[str]:
    """ทางเข้ากลาง: ทุกข้อความผ่าน ServiceRegistry"""
    request = ServiceRequest(
        bot_id=bot_id,
        chat_id=chat_id,
        user_id=user_id,
        text=text,
        metadata={"chat_type": chat_type},
    )
    response = service_registry.dispatch(
        request,
        enabled_services(bot_id),
        fallback=lambda _: 'ไม่รู้จักคำสั่งครับ พิมพ์ "ช่วยเหลือ" เพื่อดูคำสั่งที่ใช้ได้',
    )
    return response.message


@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, JoinEvent):
            chat_id, chat_type = _get_chat_id(event)
            _safe_state_write(storage.register_chat, chat_id, chat_type)
            help_text = handle_command(chat_id, "ช่วยเหลือ", None, chat_type=chat_type)
            line_client.reply_text(
                event.reply_token,
                "สวัสดีครับ! ผมเป็นผู้ช่วยรายงานข่าวและค้นข้อมูล\n" + str(help_text),
            )

        elif isinstance(event, LeaveEvent):
            chat_id, _ = _get_chat_id(event)
            _safe_state_write(storage.remove_chat, chat_id)

        elif isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            chat_id, chat_type = _get_chat_id(event)
            _safe_state_write(storage.register_chat, chat_id, chat_type)
            user_id = getattr(event.source, "user_id", None)

            text = event.message.text
            if chat_type in ("group", "room"):
                raw_text = text
                mentioned, text = _extract_self_mention(event.message)
                if not mentioned:
                    mentioned, text = _match_trigger_keyword(text)
                if not mentioned:
                    if "group_reports" in enabled_services("default"):
                        try:
                            from app.group_message_collector import capture_group_message
                            capture_group_message(
                                chat_id,
                                user_id,
                                raw_text,
                                getattr(event.message, "id", None),
                            )
                        except Exception:
                            logger.exception("บันทึกข้อความกลุ่มไม่สำเร็จ; webhook ยังทำงานต่อ")
                    continue
                if not text:
                    text = "ช่วยเหลือ"

            try:
                reply = handle_command(chat_id, text, user_id, chat_type=chat_type)
            except Exception as exc:
                print(f"[webhook] เกิดข้อผิดพลาดตอนประมวลผลข้อความ: {exc}")
                reply = "ขออภัยครับ เกิดข้อผิดพลาดระหว่างประมวลผล ลองใหม่อีกครั้งนะครับ 🙏"

            if isinstance(reply, list):
                line_client.reply_texts(event.reply_token, reply)
            else:
                line_client.reply_text(event.reply_token, reply)

    return "OK"


@app.api_route("/", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok", "service": "line-news-bot"}
