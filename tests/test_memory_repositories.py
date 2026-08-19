import unittest

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.group_message_repository import GroupMessageRepository


class FakeCursor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.current = []
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        self.executions.append((" ".join(query.split()), params))
        self.current = self.responses.pop(0) if self.responses else []

    def fetchone(self):
        return self.current[0] if self.current else None

    def fetchall(self):
        return self.current


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self._cursor


def connector_with(responses):
    cursor = FakeCursor(responses)
    return lambda: FakeConnection(cursor), cursor


class MemoryRepositoryTests(unittest.TestCase):
    def test_recent_messages_preserve_chronological_order_from_query(self):
        connector, _ = connector_with([[{
            "role": "user", "content": "ผมชื่อสมชาย"
        }, {
            "role": "assistant", "content": "ยินดีที่รู้จัก"
        }]])
        repository = ConversationRepository(connector)
        self.assertEqual(repository.get_recent_messages("c1", 20)[0]["content"], "ผมชื่อสมชาย")

    def test_append_exchange_inserts_user_and_assistant_together(self):
        connector, cursor = connector_with([[], [{"id": 7}], []])
        repository = ConversationRepository(connector)
        repository.append_exchange("c1", "u1", "local", "ชื่ออะไร", "สมชาย")
        self.assertEqual(len(cursor.executions), 3)
        self.assertIn("INSERT INTO ai_messages", cursor.executions[-1][0])
        self.assertEqual(cursor.executions[-1][1], (7, "u1", "ชื่ออะไร", 7, "สมชาย"))

    def test_group_message_is_written_only_when_insert_returns_id(self):
        connector, _ = connector_with([[{"id": 1}], []])
        repository = GroupMessageRepository(connector)
        self.assertTrue(repository.record_if_enabled("g1", "u1", "ข้อความ", "m1"))

        connector, _ = connector_with([[]])
        repository = GroupMessageRepository(connector)
        self.assertFalse(repository.record_if_enabled("g1", "u1", "ข้อความ", "m1"))


if __name__ == "__main__":
    unittest.main()
