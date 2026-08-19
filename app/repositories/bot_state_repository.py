"""เก็บ chat, subscription, topic และ setting ใน PostgreSQL/Neon ฐานหลัก"""
from collections.abc import Callable


class BotStateRepository:
    def __init__(self, connector: Callable | None = None) -> None:
        if connector is None:
            from app.db import connect as connector
        self._connect = connector

    @staticmethod
    def _ensure_chat(cur, chat_id: str, chat_type: str = "user") -> None:
        cur.execute(
            """
            INSERT INTO bot_chats (chat_id, chat_type)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) DO NOTHING
            """,
            (chat_id, chat_type),
        )

    def register_chat(self, chat_id: str, chat_type: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bot_chats (chat_id, chat_type)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id) DO UPDATE SET chat_type = EXCLUDED.chat_type
                    """,
                    (chat_id, chat_type),
                )

    def set_daily_subscription(self, chat_id: str, enabled: bool) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bot_chats (chat_id, chat_type, subscribed_daily)
                    VALUES (%s, 'user', %s)
                    ON CONFLICT (chat_id) DO UPDATE
                    SET subscribed_daily = EXCLUDED.subscribed_daily
                    """,
                    (chat_id, enabled),
                )

    def add_topic(self, chat_id: str, topic: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                self._ensure_chat(cur, chat_id)
                cur.execute(
                    """
                    INSERT INTO bot_topics (chat_id, topic)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id, topic) DO NOTHING
                    RETURNING id
                    """,
                    (chat_id, topic),
                )
                return cur.fetchone() is not None

    def remove_topic(self, chat_id: str, topic: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM bot_topics WHERE chat_id = %s AND topic = %s RETURNING id",
                    (chat_id, topic),
                )
                return cur.fetchone() is not None

    def list_topics(self, chat_id: str) -> list[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT topic FROM bot_topics WHERE chat_id = %s ORDER BY created_at, id",
                    (chat_id,),
                )
                return [row["topic"] for row in cur.fetchall()]

    def all_chats(self) -> dict[str, dict]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.chat_id, c.chat_type, c.subscribed_daily, t.topic
                    FROM bot_chats c
                    LEFT JOIN bot_topics t ON t.chat_id = c.chat_id
                    ORDER BY c.chat_id, t.created_at, t.id
                    """
                )
                chats: dict[str, dict] = {}
                for row in cur.fetchall():
                    chat = chats.setdefault(
                        row["chat_id"],
                        {
                            "type": row["chat_type"],
                            "subscribed_daily": row["subscribed_daily"],
                            "topics": [],
                        },
                    )
                    if row["topic"] is not None:
                        chat["topics"].append(row["topic"])
                return chats

    def remove_chat(self, chat_id: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM bot_chats WHERE chat_id = %s", (chat_id,))

    def get_setting(self, key: str, default=None):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM bot_settings WHERE key = %s", (key,))
                row = cur.fetchone()
                return row["value"] if row else default

    def set_setting(self, key: str, value) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bot_settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """,
                    (key, str(value)),
                )
