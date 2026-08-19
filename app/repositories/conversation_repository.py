"""Repository สำหรับประวัติคำสั่งถาม แยกตาม LINE chat_id"""
from collections.abc import Callable


class ConversationRepository:
    def __init__(self, connector: Callable | None = None) -> None:
        if connector is None:
            from app.db import connect as connector
        self._connect = connector

    def get_recent_messages(self, chat_id: str, limit: int = 20) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content
                    FROM (
                        SELECT m.id, m.role, m.content
                        FROM ai_messages m
                        JOIN ai_conversations c ON c.id = m.conversation_id
                        WHERE c.chat_id = %s
                        ORDER BY m.id DESC
                        LIMIT %s
                    ) recent
                    ORDER BY id
                    """,
                    (chat_id, limit),
                )
                return [
                    {"role": row["role"], "content": row["content"]}
                    for row in cur.fetchall()
                ]

    def append_exchange(
        self,
        chat_id: str,
        user_id: str | None,
        provider: str,
        question: str,
        answer: str,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bot_chats (chat_id, chat_type)
                    VALUES (%s, 'user')
                    ON CONFLICT (chat_id) DO NOTHING
                    """,
                    (chat_id,),
                )
                cur.execute(
                    """
                    INSERT INTO ai_conversations (chat_id, provider)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id) DO UPDATE SET provider = EXCLUDED.provider
                    RETURNING id
                    """,
                    (chat_id, provider),
                )
                conversation_id = cur.fetchone()["id"]
                cur.execute(
                    """
                    INSERT INTO ai_messages (conversation_id, user_id, role, content)
                    VALUES
                        (%s, %s, 'user', %s),
                        (%s, NULL, 'assistant', %s)
                    """,
                    (conversation_id, user_id, question, conversation_id, answer),
                )

    def count_messages(self, chat_id: str) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(m.id) AS count
                    FROM ai_conversations c
                    LEFT JOIN ai_messages m ON m.conversation_id = c.id
                    WHERE c.chat_id = %s
                    """,
                    (chat_id,),
                )
                row = cur.fetchone()
                return int(row["count"]) if row else 0

    def clear_history(self, chat_id: str) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM ai_conversations WHERE chat_id = %s RETURNING id",
                    (chat_id,),
                )
                return 1 if cur.fetchone() else 0
