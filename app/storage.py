"""Compatibility API สำหรับสถานะบอท ซึ่งจัดเก็บใน Neon/PostgreSQL ฐานหลัก"""
from app.repositories.bot_state_repository import BotStateRepository


_repository = BotStateRepository()

register_chat = _repository.register_chat
set_daily_subscription = _repository.set_daily_subscription
add_topic = _repository.add_topic
remove_topic = _repository.remove_topic
list_topics = _repository.list_topics
all_chats = _repository.all_chats
remove_chat = _repository.remove_chat
get_setting = _repository.get_setting
set_setting = _repository.set_setting
