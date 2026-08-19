import unittest

from app.group_message_collector import capture_group_message


class FakeRepository:
    def __init__(self):
        self.calls = []

    def record_if_enabled(self, chat_id, user_id, content, message_id):
        self.calls.append((chat_id, user_id, content, message_id))
        return True


class GroupMessageCollectorTests(unittest.TestCase):
    def test_forwards_message_to_opt_in_repository(self):
        repository = FakeRepository()
        recorded = capture_group_message("g1", "u1", "ข้อความ", "m1", repository)
        self.assertTrue(recorded)
        self.assertEqual(repository.calls, [("g1", "u1", "ข้อความ", "m1")])


if __name__ == "__main__":
    unittest.main()
