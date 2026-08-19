import types
import unittest

from app.core.service_loader import OptionalServiceLoader, ServiceSpec


class GoodService:
    name = "good"
    commands = ()

    def can_handle(self, request):
        return False

    def handle(self, request):
        raise NotImplementedError

    def health_check(self):
        return True


class OptionalServiceLoaderTests(unittest.TestCase):
    def test_missing_service_is_skipped_without_stopping_other_services(self):
        modules = {"good.module": types.SimpleNamespace(GoodService=GoodService)}

        def importer(name):
            if name not in modules:
                raise ModuleNotFoundError(name)
            return modules[name]

        loader = OptionalServiceLoader(
            specs=(
                ServiceSpec("missing", "missing.module", "MissingService"),
                ServiceSpec("good", "good.module", "GoodService"),
            ),
            importer=importer,
        )
        registry = loader.load()

        self.assertEqual(registry.names(), ("good",))
        self.assertIn("missing", registry.load_errors())

    def test_name_mismatch_is_reported_and_skipped(self):
        module = types.SimpleNamespace(GoodService=GoodService)
        loader = OptionalServiceLoader(
            specs=(ServiceSpec("wrong", "good.module", "GoodService"),),
            importer=lambda _: module,
        )
        registry = loader.load()
        self.assertEqual(registry.names(), ())
        self.assertIn("wrong", registry.load_errors())


if __name__ == "__main__":
    unittest.main()
