import os

from app import ai_chat
from app.core.bot_config import enabled_services
from app.core.contracts import ServiceRequest, ServiceResponse


class AIChatService:
    name = "ai_chat"
    commands = ("ถาม", "ai")

    def __init__(self, repository=None, enabled_resolver=None):
        self.repository = repository
        self.enabled_resolver = enabled_resolver or enabled_services

    def _get_repository(self):
        if self.repository is None:
            from app.repositories.conversation_repository import ConversationRepository
            self.repository = ConversationRepository()
        return self.repository

    def can_handle(self, request: ServiceRequest) -> bool:
        text = request.text.strip().lower()
        return text in ("ถาม", "ai") or text.startswith("ถาม ") or text.startswith("ai ")

    def handle(self, request: ServiceRequest) -> ServiceResponse:
        parts = request.text.strip().split(maxsplit=1)
        if len(parts) == 1 or not parts[1].strip():
            return ServiceResponse(
                False,
                self.name,
                'กรุณาพิมพ์คำถาม เช่น "ถาม Python คืออะไร"',
                error_code="MISSING_QUESTION",
            )
        question = parts[1].strip()
        if ai_chat.get_provider() == "none":
            return ServiceResponse(
                False,
                self.name,
                'AI ถามตอบถูกปิดอยู่ครับ ใช้คำสั่ง "โหมด gemini" เพื่อเปิด',
                error_code="AI_DISABLED",
            )
        memory_enabled = "conversation_memory" in self.enabled_resolver(request.bot_id)
        history = []
        repository = None
        if memory_enabled:
            try:
                repository = self._get_repository()
                history = repository.get_recent_messages(
                    request.chat_id,
                    limit=int(os.getenv("AI_MEMORY_MESSAGES", "20")),
                )
            except Exception:
                ai_chat.logger.exception("โหลดความจำ AI ไม่สำเร็จ; ตอบแบบไม่ใช้ความจำ")
                repository = None
        result = ai_chat.ask(question, conversation_id=request.chat_id, history=history)
        if memory_enabled and repository is not None:
            try:
                repository.append_exchange(
                    request.chat_id,
                    request.user_id,
                    result["provider"],
                    question,
                    result["answer"],
                )
            except Exception:
                ai_chat.logger.exception("บันทึกความจำ AI ไม่สำเร็จ; คำตอบยังส่งได้ตามปกติ")
        return ServiceResponse(
            True,
            self.name,
            result["answer"],
            metadata={"provider": result["provider"], "model": result["model"]},
        )

    def health_check(self) -> bool:
        return ai_chat.is_configured()
