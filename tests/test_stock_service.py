import unittest
from unittest.mock import patch

from app.core.contracts import ServiceRequest
from app.services.stock_service import StockService


class StockServiceTests(unittest.TestCase):
    @patch("app.services.stock_service.stock.get_stock_price", return_value="ราคา")
    def test_stock_service_uses_stock_module(self, get_stock_price):
        request = ServiceRequest("default", "chat", "user", "หุ้น ptt.bk")
        response = StockService().handle(request)
        self.assertEqual(response.message, "ราคา")
        get_stock_price.assert_called_once_with("PTT.BK")


if __name__ == "__main__":
    unittest.main()
