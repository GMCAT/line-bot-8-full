import unittest

from app.core.contracts import ServiceRequest
from app.core.registry import ServiceRegistry
from app.services.help_service import HelpService
from app.services.unknown_command_service import UnknownCommandService


def request(text):
    return ServiceRequest("default", "chat-1", "user-1", text)


class HelpAndUnknownServiceTests(unittest.TestCase):
    def test_help_recognizes_all_aliases(self):
        service = HelpService(lambda _: {"help"})
        for command in ("ช่วยเหลือ", "help", "HELP", "เมนู", "คำสั่ง"):
            self.assertTrue(service.can_handle(request(command)))

    def test_help_shows_only_enabled_services(self):
        service = HelpService(lambda _: {"ai_chat", "settings", "help", "unknown"})
        response = service.handle(request("ช่วยเหลือ"))
        self.assertIn("ถาม <คำถาม>", response.message)
        self.assertIn("โหมด", response.message)
        self.assertNotIn("หุ้น <สัญลักษณ์>", response.message)
        self.assertNotIn("เพิ่มติดต่อ", response.message)

    def test_help_shows_memory_and_group_report_commands_when_enabled(self):
        service = HelpService(
            lambda _: {"conversation_memory", "group_reports", "help", "unknown"}
        )
        response = service.handle(request("ช่วยเหลือ"))
        self.assertIn("ความจำ", response.message)
        self.assertIn("ล้างความจำ", response.message)
        self.assertIn("สรุปแชท 24 ชั่วโมง", response.message)
        self.assertIn("รายงานแชท", response.message)
        self.assertIn("เปิดบันทึกแชท", response.message)
        self.assertIn("ล้างประวัติกลุ่ม", response.message)

    def test_help_hides_unavailable_memory_commands(self):
        service = HelpService(lambda _: {"ai_chat", "help", "unknown"})
        response = service.handle(request("ช่วยเหลือ"))
        self.assertNotIn("ล้างความจำ", response.message)
        self.assertNotIn("สรุปแชท", response.message)

    def test_unknown_never_searches_news(self):
        service = UnknownCommandService()
        response = service.handle(request("สวัสดีเฉย ๆ"))
        self.assertFalse(response.success)
        self.assertEqual(response.error_code, "UNKNOWN_COMMAND")
        self.assertIn("ช่วยเหลือ", response.message)

    def test_unknown_is_last_registry_handler(self):
        registry = ServiceRegistry()
        registry.register(HelpService(lambda _: {"help", "unknown"}))
        registry.register(UnknownCommandService())

        help_response = registry.dispatch(
            request("ช่วยเหลือ"),
            {"help", "unknown"},
            lambda _: "fallback",
        )
        unknown_response = registry.dispatch(
            request("ข้อความทั่วไป"),
            {"help", "unknown"},
            lambda _: "fallback",
        )

        self.assertEqual(help_response.service, "help")
        self.assertEqual(unknown_response.service, "unknown")
        self.assertNotEqual(unknown_response.message, "fallback")


if __name__ == "__main__":
    unittest.main()
