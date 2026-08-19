import unittest

from app.core.contracts import ServiceRequest
from app.services.conversation_memory_service import ConversationMemoryService


class FakeRepository:
    def __init__(self, count=0, removed=0):
        self.count = count
        self.removed = removed
        self.cleared = []

    def count_messages(self, chat_id):
        return self.count

    def clear_history(self, chat_id):
        self.cleared.append(chat_id)
        return self.removed


def request(text):
    return ServiceRequest("default", "chat-1", "user-1", text)


class ConversationMemoryServiceTests(unittest.TestCase):
    def test_memory_count(self):
        response = ConversationMemoryService(FakeRepository(count=6)).handle(request("ความจำ"))
        self.assertIn("6 ข้อความ", response.message)

    def test_clear_memory(self):
        repository = FakeRepository(removed=1)
        response = ConversationMemoryService(repository).handle(request("ล้างความจำ"))
        self.assertIn("ล้างประวัติ", response.message)
        self.assertEqual(repository.cleared, ["chat-1"])

    def test_recognizes_only_exact_commands(self):
        service = ConversationMemoryService(FakeRepository())
        self.assertTrue(service.can_handle(request("ความจำ")))
        self.assertFalse(service.can_handle(request("ถาม ความจำคืออะไร")))


if __name__ == "__main__":
    unittest.main()
