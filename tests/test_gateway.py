"""Tests for the AI-ERP MCP server.

Tests the gateway client (the only code with logic in this MCP server).
MCP tools are pure forwarding — no logic to test independently.
"""

import pytest
import respx
from httpx import Response

from src.config import settings


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def mock_gateway():
    """Mock all gateway HTTP endpoints.

    Recreates the gateway singleton so it uses the mocked httpx client.
    """
    with respx.mock(assert_all_called=False) as respx_mock:
        base = settings.api_base

        # Documents
        respx_mock.get(f"{base}/documents/Customer").mock(
            return_value=Response(200, json={
                "data": [{"name": "CUST-001", "customer_name": "Acme Sdn Bhd"}],
                "count": 1,
                "ai_context": {"summary": "1 customer found"},
            })
        )
        respx_mock.get(f"{base}/documents/Customer/CUST-001").mock(
            return_value=Response(200, json={
                "data": {"name": "CUST-001", "customer_name": "Acme Sdn Bhd"},
                "ai_context": {"summary": "Customer Acme Sdn Bhd"},
            })
        )
        respx_mock.post(f"{base}/documents/Item").mock(
            return_value=Response(200, json={
                "intent_id": "intent-123",
                "status": "pending",
                "preview": "Create Item: Widget",
                "ai_context": {"summary": "Intent created. Awaiting approval."},
            })
        )

        # Accounting
        respx_mock.post(f"{base}/accounting/invoices").mock(
            return_value=Response(200, json={
                "intent_id": "intent-456",
                "status": "pending",
                "preview": "Invoice for Acme: RM10,000 + SST 8% = RM10,800",
                "ai_context": {"summary": "Intent to create invoice. Awaiting approval."},
            })
        )
        respx_mock.get(f"{base}/accounting/profit-and-loss").mock(
            return_value=Response(200, json={
                "data": {"total_revenue": 100000, "total_expenses": 60000, "net_profit": 40000},
                "ai_context": {"summary": "Net profit RM40,000 this period."},
            })
        )

        # Approvals
        respx_mock.get(f"{base}/intents").mock(
            return_value=Response(200, json={
                "data": [{"id": "intent-456", "status": "pending"}],
                "count": 1,
            })
        )
        respx_mock.post(f"{base}/intents/intent-456/approve").mock(
            return_value=Response(200, json={
                "status": "executed",
                "invoice": {"name": "INV-2026-001", "grand_total": 10800},
                "ai_context": {"summary": "Invoice INV-2026-001 created. Total: RM10,800"},
            })
        )
        respx_mock.post(f"{base}/intents/intent-456/reject").mock(
            return_value=Response(200, json={
                "status": "rejected",
                "intent_id": "intent-456",
            })
        )

        # Audit
        respx_mock.get(f"{base}/audit").mock(
            return_value=Response(200, json={
                "data": [
                    {"action": "intent.created", "performed_by": "agent:hermes"},
                    {"action": "intent.executed", "performed_by": "human:faizal"},
                ],
                "count": 2,
            })
        )

        # Recreate the gateway singleton so it uses the mocked transport
        from src import gateway as gw_module
        old_client = gw_module.gateway
        gw_module.gateway = gw_module.GatewayClient()

        yield respx_mock

        # Restore original
        gw_module.gateway = old_client


# ── Gateway Client Tests ──────────────────────────────────────


class TestGatewayClient:
    """Test that the gateway client forwards calls correctly."""

    def test_list_documents(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.list_documents("Customer")
        assert result["count"] == 1
        assert result["data"][0]["customer_name"] == "Acme Sdn Bhd"

    def test_get_document(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.get_document("Customer", "CUST-001")
        assert result["data"]["name"] == "CUST-001"

    def test_create_document(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.create_document("Item", {"item_name": "Widget"})
        assert result["status"] == "pending"
        assert "intent_id" in result

    def test_create_invoice(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.create_sales_invoice(
            customer="Acme Sdn Bhd",
            items=[{"item_code": "CONSULTING", "qty": 1, "rate": 10000}],
        )
        assert result["status"] == "pending"
        assert "RM10,800" in result["preview"]

    def test_list_intents(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.list_intents(status="pending")
        assert result["count"] == 1

    def test_approve_intent(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.approve_intent("intent-456")
        assert result["status"] == "executed"
        assert result["invoice"]["name"] == "INV-2026-001"

    def test_reject_intent(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.reject_intent("intent-456", reason="Too expensive")
        assert result["status"] == "rejected"

    def test_get_profit_and_loss(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.get_profit_and_loss()
        assert result["data"]["net_profit"] == 40000

    def test_get_audit_log(self, mock_gateway):
        from src.gateway import gateway
        result = gateway.get_audit_log()
        assert result["count"] == 2


# ── Config Tests ──────────────────────────────────────────────


class TestConfig:
    """Test configuration loading."""

    def test_api_base(self):
        from src.config import Settings
        s = Settings(gateway_url="http://localhost:8000", gateway_version="v1")
        assert s.api_base == "http://localhost:8000/api/v1"

    def test_headers_with_key(self):
        from src.config import Settings
        s = Settings(gateway_api_key="test-key-123")
        assert s.headers["Authorization"] == "Bearer test-key-123"

    def test_headers_without_key(self):
        from src.config import Settings
        s = Settings(gateway_api_key="")
        assert "Authorization" not in s.headers
