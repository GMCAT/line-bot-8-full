import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.contracts import ServiceRequest
from app.services.group_report_service import GroupReportService, _period_start


NOW = datetime(2026, 8, 18, 17, 0, tzinfo=ZoneInfo("Asia/Bangkok"))


class FakeRepository:
    def __init__(self, enabled=True, messages=None):
        self.enabled = enabled
        self.messages = messages or []
        self.settings = []
        self.cleared = 0

    def set_recording(self, chat_id, enabled, user_id, chat_type):
        self.enabled = enabled
        self.settings.append((chat_id, enabled, user_id, chat_type))

    def is_recording_enabled(self, chat_id):
        return self.enabled

    def get_messages_since(self, chat_id, since, limit=500):
        return self.messages

    def clear_messages(self, chat_id):
        return self.cleared


class FakeAI:
    def __init__(self):
        self.calls = []

    def ask(self, prompt, conversation_id=None, history=None):
        self.calls.append((prompt, conversation_id, history))
        return {"answer": "สรุปทดสอบ", "provider": "local", "model": "test"}


def request(text, user_id="admin", chat_type="group"):
    return ServiceRequest(
        "default", "group-1", user_id, text, metadata={"chat_type": chat_type}
    )


class GroupReportServiceTests(unittest.TestCase):
    def test_open_recording_requires_admin_and_announces_collection(self):
        repository = FakeRepository(enabled=False)
        service = GroupReportService(repository, authorizer=lambda user: user == "admin")
        denied = service.handle(request("เปิดบันทึกแชท", user_id="member"))
        self.assertEqual(denied.error_code, "FORBIDDEN")
        allowed = service.handle(request("เปิดบันทึกแชท"))
        self.assertIn("เปิดบันทึก", allowed.message)
        self.assertIn("ข้อความตัวอักษร", allowed.message)

    def test_report_is_group_only(self):
        service = GroupReportService(FakeRepository())
        response = service.handle(request("สรุปแชท", chat_type="user"))
        self.assertEqual(response.error_code, "GROUP_ONLY")

    def test_disabled_recording_returns_instruction(self):
        service = GroupReportService(FakeRepository(enabled=False))
        response = service.handle(request("สรุปแชท"))
        self.assertEqual(response.error_code, "RECORDING_DISABLED")

    def test_summary_uses_messages_without_writing_ai_memory(self):
        messages = [{
            "user_id": "U123",
            "content": "ตกลงให้สมชายทดสอบระบบ",
            "created_at": NOW,
        }]
        ai = FakeAI()
        service = GroupReportService(
            FakeRepository(messages=messages), ai_provider=ai, clock=lambda: NOW
        )
        response = service.handle(request("สรุปแชท 24 ชั่วโมง"))
        self.assertTrue(response.success)
        self.assertIn("สรุปทดสอบ", response.message)
        self.assertIn("ตกลงให้สมชาย", ai.calls[0][0])
        self.assertEqual(ai.calls[0][1:], (None, []))

    def test_period_parser_caps_days(self):
        since, label = _period_start("สรุปแชท 90 วัน", NOW)
        self.assertEqual(label, "30 วันล่าสุด")
        self.assertEqual((NOW - since).days, 30)


if __name__ == "__main__":
    unittest.main()
