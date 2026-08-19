from app.core.registry import ServiceRegistry
from app.core.service_loader import OptionalServiceLoader


def build_registry(loader: OptionalServiceLoader | None = None) -> ServiceRegistry:
    return (loader or OptionalServiceLoader()).load()
