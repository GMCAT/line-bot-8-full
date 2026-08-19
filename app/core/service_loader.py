from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from app.core.registry import ServiceRegistry


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    module: str
    class_name: str


DEFAULT_SERVICE_SPECS = (
    ServiceSpec("news", "app.services.news_service", "NewsService"),
    ServiceSpec("stocks", "app.services.stock_service", "StockService"),
    ServiceSpec("ai_chat", "app.services.ai_chat_service", "AIChatService"),
    ServiceSpec(
        "conversation_memory",
        "app.services.conversation_memory_service",
        "ConversationMemoryService",
    ),
    ServiceSpec("group_reports", "app.services.group_report_service", "GroupReportService"),
    ServiceSpec("contacts", "app.services.contact_service", "ContactService"),
    ServiceSpec("subscriptions", "app.services.subscription_service", "SubscriptionService"),
    ServiceSpec("admin", "app.services.admin_service", "AdminService"),
    ServiceSpec("settings", "app.services.settings_service", "SettingsService"),
    ServiceSpec("help", "app.services.help_service", "HelpService"),
    # ต้องอยู่สุดท้าย เพราะ UnknownCommandService รับทุกข้อความ
    ServiceSpec("unknown", "app.services.unknown_command_service", "UnknownCommandService"),
)


class OptionalServiceLoader:
    """โหลด Service แยกรายตัว; ตัวใด import/สร้างไม่สำเร็จจะถูกข้าม"""

    def __init__(
        self,
        specs: tuple[ServiceSpec, ...] = DEFAULT_SERVICE_SPECS,
        importer: Callable[[str], ModuleType] = importlib.import_module,
    ) -> None:
        self.specs = specs
        self.importer = importer

    def load(self) -> ServiceRegistry:
        registry = ServiceRegistry()
        for spec in self.specs:
            try:
                module = self.importer(spec.module)
                service_class = getattr(module, spec.class_name)
                service = service_class()
                if service.name != spec.name:
                    raise ValueError(
                        f"ชื่อ Service ไม่ตรง: spec={spec.name}, class={service.name}"
                    )
                registry.register(service)
            except Exception as exc:
                logger.exception("ข้าม service %s เพราะโหลดไม่สำเร็จ", spec.name)
                registry.record_load_error(spec.name, exc)
        return registry
