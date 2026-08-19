import unittest
from unittest.mock import patch

from app.core.contracts import ServiceRequest
from app.services.ai_chat_service import AIChatService


def request(text):
    return ServiceRequest("default", "chat-1", "user-1", text)


class FakeMemoryRepository:
    def __init__(self):
        self.history = [{"role": "user", "content": "ผมชื่อสมชาย"}]
        self.saved = []

    def get_recent_messages(self, chat_id, limit=20):
        return self.history

    def append_exchange(self, chat_id, user_id, provider, question, answer):
        self.saved.append((chat_id, user_id, provider, question, answer))


class BrokenMemoryRepository:
    def get_recent_messages(self, chat_id, limit=20):
        raise RuntimeError("database unavailable")


class AIChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.memory = FakeMemoryRepository()
        self.service = AIChatService(
            self.memory,
            enabled_resolver=lambda _: {"ai_chat", "conversation_memory"},
        )

    def test_recognizes_bare_and_full_question_commands(self):
        self.assertTrue(self.service.can_handle(request("ถาม")))
        self.assertTrue(self.service.can_handle(request("ถาม Python คืออะไร")))
        self.assertTrue(self.service.can_handle(request("ai hello")))
        self.assertFalse(self.service.can_handle(request("ข่าว AI")))

    def test_bare_command_returns_usage_instead_of_news_fallback(self):
        response = self.service.handle(request("ถาม"))
        self.assertFalse(response.success)
        self.assertEqual(response.error_code, "MISSING_QUESTION")
        self.assertIn("กรุณาพิมพ์คำถาม", response.message)

    @patch("app.services.ai_chat_service.ai_chat.get_provider", return_value="none")
    def test_none_mode_disables_only_ai_chat(self, _provider):
        response = self.service.handle(request("ถาม สวัสดี"))
        self.assertFalse(response.success)
        self.assertEqual(response.error_code, "AI_DISABLED")

    @patch("app.services.ai_chat_service.ai_chat.ask")
    @patch("app.services.ai_chat_service.ai_chat.get_provider", return_value="gemini")
    def test_question_uses_selected_ai_provider(self, _provider, ask):
        ask.return_value = {
            "answer": "คำตอบทดสอบ",
            "provider": "gemini",
            "model": "gemini-3.6-flash",
        }
        response = self.service.handle(request("ถาม ทดสอบ"))
        self.assertTrue(response.success)
        self.assertEqual(response.message, "คำตอบทดสอบ")
        self.assertEqual(response.metadata["provider"], "gemini")
        ask.assert_called_once_with(
            "ทดสอบ",
            conversation_id="chat-1",
            history=[{"role": "user", "content": "ผมชื่อสมชาย"}],
        )
        self.assertEqual(
            self.memory.saved,
            [("chat-1", "user-1", "gemini", "ทดสอบ", "คำตอบทดสอบ")],
        )

    @patch("app.services.ai_chat_service.ai_chat.ask")
    @patch("app.services.ai_chat_service.ai_chat.get_provider", return_value="gemini")
    def test_memory_can_be_disabled_per_bot(self, _provider, ask):
        ask.return_value = {"answer": "ตอบ", "provider": "gemini", "model": "model"}
        service = AIChatService(self.memory, enabled_resolver=lambda _: {"ai_chat"})
        service.handle(request("ถาม ทดสอบ"))
        ask.assert_called_once_with("ทดสอบ", conversation_id="chat-1", history=[])
        self.assertEqual(self.memory.saved, [])

    @patch("app.services.ai_chat_service.ai_chat.ask")
    @patch("app.services.ai_chat_service.ai_chat.get_provider", return_value="local")
    def test_database_failure_falls_back_to_stateless_ai(self, _provider, ask):
        ask.return_value = {"answer": "ยังตอบได้", "provider": "local", "model": "test"}
        service = AIChatService(
            BrokenMemoryRepository(),
            enabled_resolver=lambda _: {"ai_chat", "conversation_memory"},
        )
        response = service.handle(request("ถาม ยังทำงานไหม"))
        self.assertTrue(response.success)
        ask.assert_called_once_with("ยังทำงานไหม", conversation_id="chat-1", history=[])


if __name__ == "__main__":
    unittest.main()
