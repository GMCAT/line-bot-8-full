from app.core.bot_config import enabled_services
from app.core.contracts import ServiceRequest, ServiceResponse


SERVICE_HELP = {
    "news": (
        '• ข่าว — ดูข่าวเด่นตอนนี้',
        '• หา <คำค้น> — ค้นข่าว เช่น "หา ราคาน้ำมัน"',
    ),
    "stocks": ('• หุ้น <สัญลักษณ์> — ดูราคาหุ้น เช่น "หุ้น AAPL"',),
    "ai_chat": ('• ถาม <คำถาม> — คุยกับ AI ทั่วไป',),
    "conversation_memory": (
        '• ความจำ — ดูจำนวนข้อความที่ AI จำในแชทนี้',
        '• ล้างความจำ — ลบประวัติที่ใช้กับคำสั่ง "ถาม"',
    ),
    "group_reports": (
        '• สรุปแชท — สรุปบทสนทนาของวันนี้',
        '• สรุปแชท <จำนวน> ชั่วโมง/วัน — เลือกช่วงเวลา เช่น "สรุปแชท 24 ชั่วโมง"',
        '• รายงานแชท — สร้างรายงานประเด็นสำคัญ ข้อสรุป และงานที่ต้องทำ',
        '🔐 เปิดบันทึกแชท / ปิดบันทึกแชท (แอดมิน)',
        '🔐 ล้างประวัติกลุ่ม (แอดมิน)',
    ),
    "contacts": (
        '• ติดต่อ <คำค้น> — ค้นชื่อ เบอร์ อีเมล หน่วยงาน หรือตัวย่อ',
        '• ติดต่อฉุกเฉิน — ดูผู้ติดต่อฉุกเฉิน',
    ),
    "subscriptions": (
        '• ติดตาม <หัวข้อ> / เลิกติดตาม <หัวข้อ>',
        '• รายการติดตาม — ดูหัวข้อที่ติดตาม',
        '• เปิดข่าวประจำวัน / ปิดข่าวประจำวัน',
    ),
    "settings": (
        '• โหมด — ดู AI สำหรับคำสั่ง "ถาม"',
        '• โหมด <none/local/gemini/anthropic> — เปลี่ยน AI ถามตอบ',
    ),
    "admin": (
        '🔐 เพิ่มติดต่อ — เพิ่มผู้ติดต่อ (แอดมิน)',
        '🔐 ข้อมูลทั้งหมด / ตรวจฐานข้อมูล (แอดมิน)',
    ),
}


class HelpService:
    name = "help"
    commands = ("ช่วยเหลือ", "help", "เมนู", "คำสั่ง")

    def __init__(self, enabled_resolver=None):
        self.enabled_resolver = enabled_resolver or enabled_services

    def can_handle(self, request: ServiceRequest) -> bool:
        return request.text.strip().lower() in self.commands

    def handle(self, request: ServiceRequest) -> ServiceResponse:
        enabled = self.enabled_resolver(request.bot_id)
        lines = ["🤖 คำสั่งที่ใช้ได้:"]
        for service_name, help_lines in SERVICE_HELP.items():
            if service_name in enabled:
                lines.extend(help_lines)
        lines.extend(
            [
                "• ช่วยเหลือ — แสดงเมนูนี้",
                "",
                '💡 ในกลุ่มให้พิมพ์ "บอท" หรือ "!" นำหน้าคำสั่ง เช่น "บอท ถาม สวัสดี"',
            ]
        )
        return ServiceResponse(True, self.name, "\n".join(lines))

    def health_check(self) -> bool:
        return True
