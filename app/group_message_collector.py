"""บันทึกข้อความทั่วไปในกลุ่มเฉพาะเมื่อแอดมินเปิดการบันทึกแล้ว"""


def capture_group_message(
    chat_id: str,
    user_id: str | None,
    content: str,
    line_message_id: str | None = None,
    repository=None,
) -> bool:
    if repository is None:
        from app.repositories.group_message_repository import GroupMessageRepository
        repository = GroupMessageRepository()
    return repository.record_if_enabled(chat_id, user_id, content, line_message_id)
