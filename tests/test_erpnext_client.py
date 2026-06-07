"""Tests for the erpnext-mcp-server.

Tests the ERPNext client (the only code with logic in this MCP server).
MCP tools are pure forwarding — no logic to test independently.
"""

import pytest
import respx
from httpx import Response

from src.config import settings


@pytest.fixture
def mock_erpnext():
    """Mock ERPNext REST API endpoints.

    Recreates the erpnext client singleton so it uses the mocked transport.
    """
    with respx.mock(assert_all_called=False) as respx_mock:
        base = settings.erpnext_url

        # Documents
        respx_mock.get(f"{base}/api/resource/Customer").mock(
            return_value=Response(200, json={
                "data": [{"name": "CUST-001", "customer_name": "Acme Sdn Bhd"}],
            })
        )
        respx_mock.get(f"{base}/api/resource/Customer/CUST-001").mock(
            return_value=Response(200, json={
                "data": {"name": "CUST-001", "customer_name": "Acme Sdn Bhd"},
            })
        )
        respx_mock.post(f"{base}/api/resource/Item").mock(
            return_value=Response(200, json={
                "data": {"name": "ITEM-001", "item_name": "Widget"},
            })
        )
        respx_mock.put(f"{base}/api/resource/Customer/CUST-001").mock(
            return_value=Response(200, json={
                "data": {"name": "CUST-001", "customer_name": "Acme Corp Sdn Bhd"},
            })
        )
        respx_mock.delete(f"{base}/api/resource/Customer/CUST-001").mock(
            return_value=Response(200, json={"message": "ok"})
        )

        # Sales Invoice
        respx_mock.post(f"{base}/api/resource/Sales Invoice").mock(
            return_value=Response(200, json={
                "data": {"name": "SINV-001", "grand_total": 10800, "customer": "Acme Sdn Bhd"},
            })
        )

        # Method calls
        respx_mock.post(f"{base}/api/method/erpnext.stock.utils.get_stock_balance").mock(
            return_value=Response(200, json={"message": 100.0})
        )
        respx_mock.post(f"{base}/api/method/erpnext.selling.doctype.quotation.quotation.make_sales_order").mock(
            return_value=Response(200, json={"message": {"name": "SO-001"}})
        )

        # Recreate the client singleton
        from src import erpnext_client as ec_module
        old_client = ec_module.erpnext
        ec_module.erpnext = ec_module.ERPNextClient()

        yield respx_mock

        ec_module.erpnext = old_client


class TestERPNextClient:
    """Test that the ERPNext client forwards calls correctly."""

    def test_list_documents(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.list_documents("Customer")
        assert result["count"] == 1
        assert result["data"][0]["customer_name"] == "Acme Sdn Bhd"

    def test_get_document(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_document("Customer", "CUST-001")
        assert result["name"] == "CUST-001"

    def test_create_document(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.create_document("Item", {"item_name": "Widget"})
        assert result["name"] == "ITEM-001"

    def test_update_document(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.update_document("Customer", "CUST-001", {"customer_name": "Acme Corp Sdn Bhd"})
        assert result["customer_name"] == "Acme Corp Sdn Bhd"

    def test_delete_document(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.delete_document("Customer", "CUST-001")
        assert result["message"] == "ok"

    def test_create_sales_invoice(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.create_document("Sales Invoice", {
            "customer": "Acme Sdn Bhd",
            "items": [{"item_code": "CONSULTING", "qty": 1, "rate": 10000}],
        })
        assert result["name"] == "SINV-001"
        assert result["grand_total"] == 10800

    def test_call_method_get(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_stock_balance("ITEM-001")
        assert result == 100.0

    def test_call_method_post(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_order_from_quotation("QTN-001")
        assert result["name"] == "SO-001"


class TestConfig:
    """Test configuration loading."""

    def test_api_base(self):
        from src.config import Settings
        s = Settings(erpnext_url="http://localhost:8080")
        assert s.api_base == "http://localhost:8080/api/resource"

    def test_method_base(self):
        from src.config import Settings
        s = Settings(erpnext_url="http://localhost:8080")
        assert s.method_base == "http://localhost:8080/api/method"

    def test_auth_header_token(self):
        from src.config import Settings
        s = Settings(erpnext_api_key="key123", erpnext_api_secret="secret456")
        assert s.auth_header["Authorization"] == "token key123:secret456"

    def test_auth_header_no_token(self):
        from src.config import Settings
        s = Settings(erpnext_api_key="", erpnext_api_secret="")
        assert "Authorization" not in s.auth_header
