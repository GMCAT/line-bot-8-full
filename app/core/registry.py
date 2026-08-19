from __future__ import annotations

import logging
from collections.abc import Callable

from app.core.contracts import BotService, ServiceRequest, ServiceResponse

logger = logging.getLogger(__name__)


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[str, BotService] = {}
        self._load_errors: dict[str, str] = {}

    def register(self, service: BotService) -> None:
        if service.name in self._services:
            raise ValueError(f"service ซ้ำ: {service.name}")
        self._services[service.name] = service

    def names(self) -> tuple[str, ...]:
        return tuple(self._services)

    def record_load_error(self, name: str, exc: Exception) -> None:
        self._load_errors[name] = f"{type(exc).__name__}: {exc}"

    def load_errors(self) -> dict[str, str]:
        return dict(self._load_errors)

    def dispatch(
        self,
        request: ServiceRequest,
        enabled_services: set[str],
        fallback: Callable[[ServiceRequest], str | list[str]],
    ) -> ServiceResponse:
        for name, service in self._services.items():
            if not service.can_handle(request):
                continue
            if name not in enabled_services:
                return ServiceResponse(
                    success=False,
                    service=name,
                    message=f"บอทนี้ไม่ได้เปิดใช้งานระบบ {name} ครับ",
                    error_code="SERVICE_DISABLED",
                )
            try:
                return service.handle(request)
            except Exception as exc:
                logger.exception("service %s failed", name)
                return ServiceResponse(
                    success=False,
                    service=name,
                    message=f"ระบบ {name} ไม่พร้อมใช้งานชั่วคราวครับ ระบบอื่นยังใช้งานได้ตามปกติ",
                    retryable=True,
                    error_code=type(exc).__name__,
                )

        return ServiceResponse(True, "fallback", fallback(request))
