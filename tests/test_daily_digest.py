import unittest

from app.daily_digest import send_daily_digest


class FakeRepository:
    def all_chats(self):
        return {
            "subscribed": {"subscribed_daily": True, "topics": ["PTT.BK", "พายุ"]},
            "disabled": {"subscribed_daily": False, "topics": []},
        }


class FakeNews:
    def __init__(self):
        self.queries = []

    def fetch_headlines(self, query=None, limit=5):
        self.queries.append((query, limit))
        return [query or "general"]

    def format_plain(self, title, items):
        return f"{title}: {items[0]}"


class FakeStock:
    def __init__(self):
        self.tickers = []

    def get_stock_price(self, ticker):
        self.tickers.append(ticker)
        return f"stock:{ticker}"


class DailyDigestTests(unittest.TestCase):
    def test_sends_only_subscribed_and_keeps_stock_separate(self):
        news = FakeNews()
        stock = FakeStock()
        messages = []

        sent = send_daily_digest(
            FakeRepository(), news, stock, lambda chat_id, text: messages.append((chat_id, text))
        )

        self.assertEqual(sent, 1)
        self.assertEqual(stock.tickers, ["PTT.BK"])
        self.assertIn(("พายุ", 3), news.queries)
        self.assertEqual(messages[0][0], "subscribed")

    def test_one_failed_push_does_not_stop_other_chats(self):
        class TwoChats:
            def all_chats(self):
                return {
                    "bad": {"subscribed_daily": True, "topics": []},
                    "good": {"subscribed_daily": True, "topics": []},
                }

        delivered = []

        def sender(chat_id, text):
            if chat_id == "bad":
                raise RuntimeError("LINE unavailable")
            delivered.append(chat_id)

        sent = send_daily_digest(TwoChats(), FakeNews(), FakeStock(), sender)
        self.assertEqual(sent, 1)
        self.assertEqual(delivered, ["good"])


if __name__ == "__main__":
    unittest.main()
