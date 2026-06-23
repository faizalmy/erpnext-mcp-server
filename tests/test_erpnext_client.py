"""Tests for the erpnext-mcp-server.

Tests the ERPNext client (the only code with logic in this MCP server).
MCP tools are pure forwarding — no logic to test independently.
"""

import pytest
import respx
from httpx import Response

from src.erpnext_client import set_request_context


@pytest.fixture
def mock_erpnext():
    """Mock ERPNext REST API endpoints.

    Recreates the erpnext client singleton so it uses the mocked transport.
    """
    with respx.mock(assert_all_called=False) as respx_mock:
        base = "http://test-erp:8080"

        # Mock login (for password auth auto-login)
        respx_mock.post(f"{base}/api/method/login").mock(
            return_value=Response(200, json={"message": "Logged In"})
        )

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

        # ── Frappe client methods (submit/cancel) ──
        respx_mock.post(f"{base}/api/method/frappe.client.submit").mock(
            return_value=Response(200, json={
                "message": {"name": "SINV-001", "docstatus": 1}
            })
        )
        respx_mock.post(f"{base}/api/method/frappe.client.cancel").mock(
            return_value=Response(200, json={
                "message": {"name": "SINV-001", "docstatus": 2}
            })
        )

        # ── Accounting methods ──
        respx_mock.post(f"{base}/api/method/erpnext.accounts.utils.get_balance_on").mock(
            return_value=Response(200, json={"message": 150000.00})
        )
        respx_mock.post(f"{base}/api/method/erpnext.accounts.utils.get_exchange_rate").mock(
            return_value=Response(200, json={"message": 4.72})
        )
        respx_mock.post(f"{base}/api/method/erpnext.accounts.utils.get_fiscal_year").mock(
            return_value=Response(200, json={
                "message": ["2026-2027", "2026-04-01", "2027-03-31"]
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return").mock(
            return_value=Response(200, json={
                "message": {"name": "SRET-001", "return_against": "SINV-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry").mock(
            return_value=Response(200, json={
                "message": {"name": "PE-001", "payment_type": "Receive", "paid_amount": 10800}
            })
        )

        # ── Selling methods ──
        respx_mock.post(f"{base}/api/method/erpnext.selling.doctype.quotation.quotation.make_sales_order").mock(
            return_value=Response(200, json={"message": {"name": "SO-001"}})
        )
        respx_mock.post(f"{base}/api/method/erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice").mock(
            return_value=Response(200, json={
                "message": {"name": "SINV-002", "sales_order": "SO-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.selling.doctype.sales_order.sales_order.make_delivery_note").mock(
            return_value=Response(200, json={
                "message": {"name": "DEL-001", "sales_order": "SO-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.crm.doctype.opportunity.opportunity.make_quotation").mock(
            return_value=Response(200, json={
                "message": {"name": "QTN-001", "opportunity": "OPP-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.crm.doctype.lead.lead.make_opportunity").mock(
            return_value=Response(200, json={
                "message": {"name": "OPP-001", "lead_name": "LEAD-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.crm.doctype.lead.lead.make_customer").mock(
            return_value=Response(200, json={
                "message": {"name": "CUST-002", "lead_name": "LEAD-001"}
            })
        )

        # ── Buying methods ──
        respx_mock.post(f"{base}/api/method/erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt").mock(
            return_value=Response(200, json={
                "message": {"name": "PRE-001", "purchase_order": "PO-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice").mock(
            return_value=Response(200, json={
                "message": {"name": "PINV-001", "purchase_order": "PO-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.buying.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice").mock(
            return_value=Response(200, json={
                "message": {"name": "PINV-002", "purchase_receipt": "PRE-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.buying.doctype.purchase_receipt.purchase_receipt.make_purchase_return").mock(
            return_value=Response(200, json={
                "message": {"name": "PRET-001", "return_against": "PRE-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.buying.doctype.material_request.material_request.make_purchase_order").mock(
            return_value=Response(200, json={
                "message": {"name": "PO-001", "material_request": "MR-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.buying.doctype.material_request.material_request.make_supplier_quotation").mock(
            return_value=Response(200, json={
                "message": {"name": "SQ-001", "material_request": "MR-001"}
            })
        )

        # ── Stock methods ──
        respx_mock.post(f"{base}/api/method/erpnext.stock.utils.get_stock_balance").mock(
            return_value=Response(200, json={"message": 100.0})
        )
        respx_mock.post(f"{base}/api/method/erpnext.stock.doctype.item.item.get_item_details").mock(
            return_value=Response(200, json={
                "message": {
                    "item_code": "ITEM-001",
                    "item_name": "Widget",
                    "stock_uom": "Nos",
                    "actual_qty": 50,
                }
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.stock.doctype.batch.batch.get_batch_qty").mock(
            return_value=Response(200, json={"message": 25.0})
        )
        respx_mock.post(f"{base}/api/method/erpnext.stock.doctype.stock_entry.stock_entry.make_stock_entry").mock(
            return_value=Response(200, json={
                "message": {"name": "STE-001", "stock_entry_type": "Material Transfer"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice").mock(
            return_value=Response(200, json={
                "message": {"name": "SINV-003", "delivery_note": "DEL-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return").mock(
            return_value=Response(200, json={
                "message": {"name": "SRET-002", "return_against": "DEL-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.stock.stock_ledger.get_stock_ledger_entries").mock(
            return_value=Response(200, json={
                "message": [
                    {"item_code": "ITEM-001", "actual_qty": 10, "posting_date": "2026-06-01"},
                    {"item_code": "ITEM-001", "actual_qty": -5, "posting_date": "2026-06-05"},
                ]
            })
        )

        # ── HR methods ──
        respx_mock.post(f"{base}/api/method/erpnext.hr.doctype.leave_application.leave_application.get_leave_balance_on").mock(
            return_value=Response(200, json={"message": 12.0})
        )
        respx_mock.post(f"{base}/api/method/erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days").mock(
            return_value=Response(200, json={"message": 3.0})
        )

        # ── Manufacturing methods ──
        respx_mock.post(f"{base}/api/method/erpnext.manufacturing.doctype.bom.bom.get_bom_items").mock(
            return_value=Response(200, json={
                "message": [
                    {"item_code": "RAW-001", "qty": 2, "rate": 100},
                    {"item_code": "RAW-002", "qty": 1, "rate": 250},
                ]
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.manufacturing.doctype.bom.bom.get_exploded_items").mock(
            return_value=Response(200, json={
                "message": [
                    {"item_code": "RAW-001", "qty": 4, "rate": 100},
                    {"item_code": "RAW-002", "qty": 1, "rate": 250},
                    {"item_code": "SUB-001", "qty": 2, "rate": 50},
                ]
            })
        )

        # ── Projects methods ──
        respx_mock.post(f"{base}/api/method/erpnext.projects.doctype.timesheet.timesheet.make_sales_invoice").mock(
            return_value=Response(200, json={
                "message": {"name": "SINV-004", "timesheet": "TS-001"}
            })
        )

        # ── Assets methods ──
        respx_mock.post(f"{base}/api/method/erpnext.assets.doctype.asset.asset.scrap_asset").mock(
            return_value=Response(200, json={
                "message": {"name": "AST-001", "status": "Scrapped"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.assets.doctype.asset.asset.restore_asset").mock(
            return_value=Response(200, json={
                "message": {"name": "AST-001", "status": "Submitted"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.assets.doctype.asset.asset.make_sales_invoice").mock(
            return_value=Response(200, json={
                "message": {"name": "SINV-005", "asset": "AST-001"}
            })
        )
        respx_mock.post(f"{base}/api/method/erpnext.assets.doctype.asset.asset.make_asset_movement").mock(
            return_value=Response(200, json={
                "message": {"name": "ASSTM-001", "asset": "AST-001"}
            })
        )

        # Recreate the client singleton
        from src import erpnext_client as ec_module
        old_client = ec_module.erpnext
        ec_module.erpnext = ec_module.ERPNextClient()
        set_request_context(url="http://test-erp:8080", api_key="test-api-key", api_secret="test-api-secret")

        yield respx_mock

        ec_module.erpnext = old_client


# ═══════════════════════════════════════════════════════════
# CRUD (Resource API)
# ═══════════════════════════════════════════════════════════

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

    def test_submit_document(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.submit_document("Sales Invoice", "SINV-001")
        assert result["name"] == "SINV-001"
        assert result["docstatus"] == 1

    def test_cancel_document(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.cancel_document("Sales Invoice", "SINV-001")
        assert result["name"] == "SINV-001"
        assert result["docstatus"] == 2


# ═══════════════════════════════════════════════════════════
# Method API (call_method gateway)
# ═══════════════════════════════════════════════════════════

class TestCallMethod:
    """Test the core call_method gateway + error handling."""

    def test_call_method_get(self, mock_erpnext):
        """GET when no kwargs (stock_balance uses POST because it has kwargs)."""
        from src.erpnext_client import erpnext
        result = erpnext.get_stock_balance("ITEM-001")
        assert result == 100.0

    def test_call_method_post(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_order_from_quotation("QTN-001")
        assert result["name"] == "SO-001"

    def test_call_method_http_error(self, mock_erpnext):
        """call_method should raise on HTTP errors."""
        from src.erpnext_client import erpnext
        import httpx
        # Override the mock to return 500
        mock_erpnext.post(f"{'http://test-erp:8080'}/api/method/erpnext.stock.utils.get_stock_balance").mock(
            return_value=Response(500, json={"exc": "Internal Server Error"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            erpnext.get_stock_balance("ITEM-999")

    def test_call_method_no_message_key(self, mock_erpnext):
        """When response has no 'message' key, call_method returns full JSON."""
        from src.erpnext_client import erpnext
        mock_erpnext.post(f"{'http://test-erp:8080'}/api/method/erpnext.accounts.utils.get_exchange_rate").mock(
            return_value=Response(200, json={"result": 4.72})
        )
        result = erpnext.get_exchange_rate("USD", "MYR")
        # Falls through to r.json() since no 'message' key
        assert result["result"] == 4.72


# ═══════════════════════════════════════════════════════════
# Accounting convenience methods
# ═══════════════════════════════════════════════════════════

class TestAccounting:
    """Test accounting convenience methods."""

    def test_get_balance_on(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_balance_on("Debtors - ACT")
        assert result == 150000.00

    def test_get_balance_on_with_date_and_company(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_balance_on("Debtors - ACT", date="2026-06-08", company="Test Co")
        assert result == 150000.00

    def test_get_exchange_rate(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_exchange_rate("USD", "MYR")
        assert result == 4.72

    def test_get_exchange_rate_with_date(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_exchange_rate("USD", "MYR", date="2026-06-08")
        assert result == 4.72

    def test_get_fiscal_year(self, mock_erpnext):
        from src.erpnext_client import erpnext
        # When called with no args, call_method uses GET (not POST)
        mock_erpnext.get(f"{'http://test-erp:8080'}/api/method/erpnext.accounts.utils.get_fiscal_year").mock(
            return_value=Response(200, json={
                "message": ["2026-2027", "2026-04-01", "2027-03-31"]
            })
        )
        result = erpnext.get_fiscal_year()
        assert result[0] == "2026-2027"

    def test_get_fiscal_year_with_date(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_fiscal_year(date="2026-06-08")
        assert result[0] == "2026-2027"

    def test_make_sales_return(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_return("SINV-001")
        assert result["name"] == "SRET-001"
        assert result["return_against"] == "SINV-001"

    def test_get_payment_entry(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_payment_entry("Sales Invoice", "SINV-001")
        assert result["name"] == "PE-001"
        assert result["paid_amount"] == 10800


# ═══════════════════════════════════════════════════════════
# Selling convenience methods
# ═══════════════════════════════════════════════════════════

class TestSelling:
    """Test selling workflow convenience methods."""

    def test_make_sales_order_from_quotation(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_order_from_quotation("QTN-001")
        assert result["name"] == "SO-001"

    def test_make_sales_invoice_from_sales_order(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_invoice_from_sales_order("SO-001")
        assert result["name"] == "SINV-002"
        assert result["sales_order"] == "SO-001"

    def test_make_delivery_note_from_sales_order(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_delivery_note_from_sales_order("SO-001")
        assert result["name"] == "DEL-001"
        assert result["sales_order"] == "SO-001"

    def test_make_quotation_from_opportunity(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_quotation_from_opportunity("OPP-001")
        assert result["name"] == "QTN-001"
        assert result["opportunity"] == "OPP-001"

    def test_make_opportunity_from_lead(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_opportunity_from_lead("LEAD-001")
        assert result["name"] == "OPP-001"

    def test_make_customer_from_lead(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_customer_from_lead("LEAD-001")
        assert result["name"] == "CUST-002"


# ═══════════════════════════════════════════════════════════
# Buying convenience methods
# ═══════════════════════════════════════════════════════════

class TestBuying:
    """Test buying workflow convenience methods."""

    def test_make_purchase_receipt_from_po(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_purchase_receipt_from_po("PO-001")
        assert result["name"] == "PRE-001"

    def test_make_purchase_invoice_from_po(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_purchase_invoice_from_po("PO-001")
        assert result["name"] == "PINV-001"

    def test_make_purchase_invoice_from_pr(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_purchase_invoice_from_pr("PRE-001")
        assert result["name"] == "PINV-002"

    def test_make_purchase_return(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_purchase_return("PRE-001")
        assert result["name"] == "PRET-001"

    def test_make_purchase_order_from_mr(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_purchase_order_from_mr("MR-001")
        assert result["name"] == "PO-001"

    def test_make_supplier_quotation_from_mr(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_supplier_quotation_from_mr("MR-001")
        assert result["name"] == "SQ-001"


# ═══════════════════════════════════════════════════════════
# Stock convenience methods
# ═══════════════════════════════════════════════════════════

class TestStock:
    """Test stock convenience methods."""

    def test_get_stock_balance(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_stock_balance("ITEM-001")
        assert result == 100.0

    def test_get_stock_balance_with_warehouse(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_stock_balance("ITEM-001", warehouse="WH-001")
        assert result == 100.0

    def test_get_item_details(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_item_details("ITEM-001")
        assert result["item_code"] == "ITEM-001"
        assert result["stock_uom"] == "Nos"
        assert result["actual_qty"] == 50

    def test_get_item_details_with_company_and_warehouse(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_item_details("ITEM-001", company="Test Co", warehouse="WH-001")
        assert result["item_code"] == "ITEM-001"

    def test_get_batch_qty(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_batch_qty("BATCH-001")
        assert result == 25.0

    def test_get_batch_qty_with_warehouse(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_batch_qty("BATCH-001", warehouse="WH-001")
        assert result == 25.0

    def test_make_stock_entry(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_stock_entry(
            stock_entry_type="Material Transfer",
            items=[{"item_code": "ITEM-001", "qty": 5}],
        )
        assert result["name"] == "STE-001"
        assert result["stock_entry_type"] == "Material Transfer"

    def test_make_sales_invoice_from_dn(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_invoice_from_dn("DEL-001")
        assert result["name"] == "SINV-003"

    def test_make_sales_return_from_dn(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_return_from_dn("DEL-001")
        assert result["name"] == "SRET-002"

    def test_get_stock_ledger_entries(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_stock_ledger_entries("ITEM-001")
        assert len(result) == 2
        assert result[0]["actual_qty"] == 10
        assert result[1]["actual_qty"] == -5

    def test_get_stock_ledger_entries_with_filters(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_stock_ledger_entries(
            "ITEM-001", warehouse="WH-001",
            posting_date_from="2026-06-01", posting_date_to="2026-06-30",
        )
        assert len(result) == 2


# ═══════════════════════════════════════════════════════════
# HR convenience methods
# ═══════════════════════════════════════════════════════════

class TestHR:
    """Test HR convenience methods."""

    def test_get_leave_balance_on(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_leave_balance_on("EMP-001", "Annual Leave")
        assert result == 12.0

    def test_get_leave_balance_on_with_date(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_leave_balance_on("EMP-001", "Annual Leave", date="2026-06-08")
        assert result == 12.0

    def test_get_leave_days(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_leave_days("EMP-001", "Annual Leave", "2026-06-10", "2026-06-12")
        assert result == 3.0


# ═══════════════════════════════════════════════════════════
# Manufacturing convenience methods
# ═══════════════════════════════════════════════════════════

class TestManufacturing:
    """Test manufacturing convenience methods."""

    def test_get_bom_items(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_bom_items("BOM-001")
        assert len(result) == 2
        assert result[0]["item_code"] == "RAW-001"
        assert result[1]["rate"] == 250

    def test_get_bom_items_with_company_and_qty(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_bom_items("BOM-001", company="Test Co", qty=10)
        assert len(result) == 2

    def test_get_exploded_items(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_exploded_items("BOM-001")
        assert len(result) == 3
        assert result[2]["item_code"] == "SUB-001"

    def test_get_exploded_items_with_qty(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.get_exploded_items("BOM-001", qty=10)
        assert len(result) == 3


# ═══════════════════════════════════════════════════════════
# Projects convenience methods
# ═══════════════════════════════════════════════════════════

class TestProjects:
    """Test projects convenience methods."""

    def test_make_sales_invoice_from_timesheet(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_sales_invoice_from_timesheet("TS-001")
        assert result["name"] == "SINV-004"
        assert result["timesheet"] == "TS-001"


# ═══════════════════════════════════════════════════════════
# Assets convenience methods
# ═══════════════════════════════════════════════════════════

class TestAssets:
    """Test assets convenience methods."""

    def test_scrap_asset(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.scrap_asset("AST-001")
        assert result["name"] == "AST-001"
        assert result["status"] == "Scrapped"

    def test_restore_asset(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.restore_asset("AST-001")
        assert result["name"] == "AST-001"
        assert result["status"] == "Submitted"

    def test_make_asset_sales_invoice(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_asset_sales_invoice("AST-001")
        assert result["name"] == "SINV-005"
        assert result["asset"] == "AST-001"

    def test_make_asset_movement(self, mock_erpnext):
        from src.erpnext_client import erpnext
        result = erpnext.make_asset_movement("AST-001")
        assert result["name"] == "ASSTM-001"
        assert result["asset"] == "AST-001"


# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# Configuration tests — REMOVED (api_base/method_base/auth_header
# no longer exist; connection config is per-request via contextvars)
# ═══════════════════════════════════════════════════════════
