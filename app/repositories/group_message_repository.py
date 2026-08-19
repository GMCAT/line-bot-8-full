"""Repository สำหรับการยินยอมบันทึกและข้อความในกลุ่ม LINE"""
from collections.abc import Callable
from datetime import datetime


class GroupMessageRepository:
    def __init__(self, connector: Callable | None = None) -> None:
        if connector is None:
            from app.db import connect as connector
        self._connect = connector

    def set_recording(
        self,
        chat_id: str,
        enabled: bool,
        user_id: str | None,
        chat_type: str = "group",
    ) -> None:
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
                cur.execute(
                    """
                    INSERT INTO group_recording_settings (chat_id, enabled, enabled_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (chat_id) DO UPDATE
                    SET enabled = EXCLUDED.enabled, enabled_by = EXCLUDED.enabled_by
                    """,
                    (chat_id, enabled, user_id),
                )

    def is_recording_enabled(self, chat_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT enabled FROM group_recording_settings WHERE chat_id = %s",
                    (chat_id,),
                )
                row = cur.fetchone()
                return bool(row and row["enabled"])

    def record_if_enabled(
        self,
        chat_id: str,
        user_id: str | None,
        content: str,
        line_message_id: str | None = None,
    ) -> bool:
        if not content.strip():
            return False
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO group_messages (chat_id, user_id, content, line_message_id)
                    SELECT %s, %s, %s, %s
                    FROM group_recording_settings
                    WHERE chat_id = %s AND enabled = true
                    ON CONFLICT (line_message_id) DO NOTHING
                    RETURNING id
                    """,
                    (chat_id, user_id, content, line_message_id, chat_id),
                )
                inserted = cur.fetchone() is not None
                if inserted:
                    cur.execute(
                        """
                        DELETE FROM group_messages gm
                        USING group_recording_settings s
                        WHERE gm.chat_id = s.chat_id
                          AND gm.chat_id = %s
                          AND gm.created_at < CURRENT_TIMESTAMP - (s.retention_days * INTERVAL '1 day')
                        """,
                        (chat_id,),
                    )
                return inserted

    def get_messages_since(
        self,
        chat_id: str,
        since: datetime,
        limit: int = 500,
    ) -> list[dict]:
        limit = max(1, min(int(limit), 2000))
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, content, created_at
                    FROM (
                        SELECT id, user_id, content, created_at
                        FROM group_messages
                        WHERE chat_id = %s AND created_at >= %s
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                    ) recent
                    ORDER BY created_at, id
                    """,
                    (chat_id, since, limit),
                )
                return list(cur.fetchall())

    def clear_messages(self, chat_id: str) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM group_messages WHERE chat_id = %s RETURNING id",
                    (chat_id,),
                )
                return len(cur.fetchall())
