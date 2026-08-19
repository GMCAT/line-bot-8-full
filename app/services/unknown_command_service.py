from app.core.contracts import ServiceRequest, ServiceResponse


class UnknownCommandService:
    """Service ตัวสุดท้ายใน Registry สำหรับข้อความที่ไม่มี Service ใดรับผิดชอบ"""

    name = "unknown"
    commands = ()

    def can_handle(self, request: ServiceRequest) -> bool:
        return True

    def handle(self, request: ServiceRequest) -> ServiceResponse:
        text = request.text.strip()
        preview = text if len(text) <= 80 else text[:77] + "..."
        return ServiceResponse(
            False,
            self.name,
            f'ไม่รู้จักคำสั่ง "{preview}" ครับ พิมพ์ "ช่วยเหลือ" เพื่อดูคำสั่งที่ใช้ได้',
            error_code="UNKNOWN_COMMAND",
        )

    def health_check(self) -> bool:
        return True
