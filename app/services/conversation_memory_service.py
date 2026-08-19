from app.core.contracts import ServiceRequest, ServiceResponse


class ConversationMemoryService:
    name = "conversation_memory"
    commands = ("ความจำ", "ล้างความจำ")

    def __init__(self, repository=None):
        self.repository = repository

    def _get_repository(self):
        if self.repository is None:
            from app.repositories.conversation_repository import ConversationRepository
            self.repository = ConversationRepository()
        return self.repository

    def can_handle(self, request: ServiceRequest) -> bool:
        return request.text.strip() in self.commands

    def handle(self, request: ServiceRequest) -> ServiceResponse:
        repository = self._get_repository()
        if request.text.strip() == "ล้างความจำ":
            removed = repository.clear_history(request.chat_id)
            message = (
                "ล้างประวัติ AI ของแชทนี้แล้วครับ"
                if removed
                else "แชทนี้ยังไม่มีประวัติ AI ให้ลบครับ"
            )
            return ServiceResponse(True, self.name, message)

        count = repository.count_messages(request.chat_id)
        if count == 0:
            message = 'AI ยังไม่มีความจำในแชทนี้ครับ เริ่มได้ด้วยคำสั่ง "ถาม <คำถาม>"'
        else:
            message = (
                f"AI จำประวัติของแชทนี้อยู่ {count} ข้อความครับ "
                'ลบได้ด้วยคำสั่ง "ล้างความจำ"'
            )
        return ServiceResponse(True, self.name, message)

    def health_check(self) -> bool:
        return True
