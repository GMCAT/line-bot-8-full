import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import ai_chat
from app.core.auth import is_configured_admin
from app.core.contracts import ServiceRequest, ServiceResponse


REPORT_COMMANDS = (
    "สรุปแชท",
    "รายงานแชท",
    "เปิดบันทึกแชท",
    "ปิดบันทึกแชท",
    "ล้างประวัติกลุ่ม",
)


def _period_start(text: str, now: datetime | None = None) -> tuple[datetime, str]:
    now = now or datetime.now(ZoneInfo("Asia/Bangkok"))
    match = re.search(r"(\d+)\s*(ชั่วโมง|ชม\.?|วัน)", text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit.startswith("วัน"):
            amount = max(1, min(amount, 30))
            return now - timedelta(days=amount), f"{amount} วันล่าสุด"
        amount = max(1, min(amount, 720))
        return now - timedelta(hours=amount), f"{amount} ชั่วโมงล่าสุด"
    if text.startswith("สรุปแชท"):
        return now.replace(hour=0, minute=0, second=0, microsecond=0), "วันนี้"
    return now - timedelta(hours=24), "24 ชั่วโมงล่าสุด"


def _build_prompt(messages: list[dict], period_label: str, detailed: bool) -> str:
    rows = []
    for message in messages:
        timestamp = message["created_at"]
        time_label = timestamp.astimezone(ZoneInfo("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M")
        member = message.get("user_id") or "ไม่ทราบผู้ส่ง"
        rows.append(f"[{time_label}] สมาชิก {member}: {message['content']}")
    transcript = "\n".join(rows)
    max_chars = max(1000, int(os.getenv("GROUP_REPORT_MAX_CHARS", "30000")))
    if len(transcript) > max_chars:
        transcript = "[ตัดข้อความเก่าบางส่วนเนื่องจากรายงานยาวเกินไป]\n" + transcript[-max_chars:]
    if detailed:
        instruction = (
            "สร้างรายงานภาษาไทยโดยมีหัวข้อ: ภาพรวม, ประเด็นสำคัญ, ข้อสรุป/การตัดสินใจ, "
            "งานที่ต้องทำ, ผู้รับผิดชอบและกำหนดเวลา (ถ้ามี), ประเด็นที่ยังค้าง"
        )
    else:
        instruction = "สรุปภาษาไทยแบบกระชับ แยกประเด็นสำคัญ ข้อสรุป และงานที่ต้องทำ"
    return (
        "คุณกำลังสรุปบทสนทนากลุ่ม LINE กรุณาใช้เฉพาะข้อความที่ให้มา "
        "ห้ามแต่งข้อมูล หากไม่ทราบชื่อให้ใช้รหัสสมาชิกตามข้อความ และระบุว่าไม่พบข้อมูลเมื่อไม่มีหลักฐาน\n"
        f"ช่วงเวลา: {period_label}\nคำสั่ง: {instruction}\n\nข้อความ:\n{transcript}"
    )


class GroupReportService:
    name = "group_reports"
    commands = REPORT_COMMANDS

    def __init__(self, repository=None, authorizer=None, ai_provider=None, clock=None):
        self.repository = repository
        self.authorizer = authorizer or is_configured_admin
        self.ai_provider = ai_provider or ai_chat
        self.clock = clock

    def _get_repository(self):
        if self.repository is None:
            from app.repositories.group_message_repository import GroupMessageRepository
            self.repository = GroupMessageRepository()
        return self.repository

    def can_handle(self, request: ServiceRequest) -> bool:
        text = request.text.strip()
        return any(text == command or text.startswith(command + " ") for command in REPORT_COMMANDS)

    @staticmethod
    def _is_group(request: ServiceRequest) -> bool:
        return request.metadata.get("chat_type") in ("group", "room")

    def handle(self, request: ServiceRequest) -> ServiceResponse:
        if not self._is_group(request):
            return ServiceResponse(
                False,
                self.name,
                "คำสั่งรายงานแชทใช้ได้เฉพาะในกลุ่มหรือห้องแชทครับ",
                error_code="GROUP_ONLY",
            )

        text = request.text.strip()
        repository = self._get_repository()
        if text in ("เปิดบันทึกแชท", "ปิดบันทึกแชท", "ล้างประวัติกลุ่ม"):
            if not self.authorizer(request.user_id):
                return ServiceResponse(
                    False,
                    self.name,
                    "คำสั่งนี้ใช้ได้เฉพาะแอดมินที่กำหนดใน LINE_ADMIN_USER_IDS ครับ",
                    error_code="FORBIDDEN",
                )
            if text == "เปิดบันทึกแชท":
                repository.set_recording(
                    request.chat_id,
                    True,
                    request.user_id,
                    request.metadata.get("chat_type", "group"),
                )
                return ServiceResponse(
                    True,
                    self.name,
                    "✅ เปิดบันทึกข้อความกลุ่มแล้วครับ\n"
                    "บอทจะเก็บเฉพาะข้อความตัวอักษรเพื่อนำมาสรุป และเก็บย้อนหลังตามระยะเวลาที่ระบบกำหนด",
                )
            if text == "ปิดบันทึกแชท":
                repository.set_recording(
                    request.chat_id,
                    False,
                    request.user_id,
                    request.metadata.get("chat_type", "group"),
                )
                return ServiceResponse(True, self.name, "ปิดการบันทึกข้อความกลุ่มแล้วครับ")
            removed = repository.clear_messages(request.chat_id)
            return ServiceResponse(
                True, self.name, f"ล้างประวัติข้อความกลุ่มแล้ว {removed} ข้อความครับ"
            )

        if not repository.is_recording_enabled(request.chat_id):
            return ServiceResponse(
                False,
                self.name,
                'กลุ่มนี้ยังไม่ได้เปิดบันทึกแชทครับ ให้แอดมินสั่ง "เปิดบันทึกแชท" ก่อน',
                error_code="RECORDING_DISABLED",
            )
        now = self.clock() if self.clock else datetime.now(ZoneInfo("Asia/Bangkok"))
        since, period_label = _period_start(text, now)
        messages = repository.get_messages_since(request.chat_id, since, limit=500)
        if not messages:
            return ServiceResponse(
                True, self.name, f"ไม่พบข้อความที่บันทึกไว้ในช่วง {period_label} ครับ"
            )
        prompt = _build_prompt(messages, period_label, detailed=text.startswith("รายงานแชท"))
        result = self.ai_provider.ask(prompt, conversation_id=None, history=[])
        title = "📋 รายงานบทสนทนากลุ่ม" if text.startswith("รายงานแชท") else "📝 สรุปบทสนทนากลุ่ม"
        return ServiceResponse(
            True,
            self.name,
            f"{title}\nช่วงเวลา: {period_label}\n\n{result['answer']}",
            metadata={"provider": result["provider"], "model": result["model"], "messages": len(messages)},
        )

    def health_check(self) -> bool:
        return True
