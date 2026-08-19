import unittest

from app.repositories.bot_state_repository import BotStateRepository


class FakeCursor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.current = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
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


def repository_with(responses):
    cursor = FakeCursor(responses)
    return BotStateRepository(lambda: FakeConnection(cursor))


class BotStateRepositoryTests(unittest.TestCase):
    def test_duplicate_topic_returns_false(self):
        self.assertFalse(repository_with([[], []]).add_topic("chat-1", "พายุ"))

    def test_new_topic_returns_true(self):
        self.assertTrue(repository_with([[], [{"id": 1}]]).add_topic("chat-1", "พายุ"))

    def test_all_chats_groups_topics(self):
        rows = [
            {"chat_id": "c1", "chat_type": "group", "subscribed_daily": True, "topic": "พายุ"},
            {"chat_id": "c1", "chat_type": "group", "subscribed_daily": True, "topic": "น้ำท่วม"},
            {"chat_id": "c2", "chat_type": "user", "subscribed_daily": False, "topic": None},
        ]
        chats = repository_with([rows]).all_chats()
        self.assertEqual(chats["c1"]["topics"], ["พายุ", "น้ำท่วม"])
        self.assertEqual(chats["c2"]["topics"], [])

    def test_missing_setting_uses_default(self):
        repository = repository_with([[]])
        self.assertEqual(repository.get_setting("ai_provider", "local"), "local")


if __name__ == "__main__":
    unittest.main()
