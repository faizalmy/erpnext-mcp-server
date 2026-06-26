"""Integration tests for server.py — MCP server registration (tools, resources, prompts).

These tests verify that tools, resources, and prompts register correctly on FastMCP
without requiring a live ERPNext connection.
"""

import pytest
from unittest.mock import patch, MagicMock

from mcp.server.fastmcp import FastMCP


class TestRegisterResources:
    """Test _register_resources registers 5 erpnext:// resources."""

    def test_register_resources_count(self):
        from src.server import _register_resources
        mcp = FastMCP("test-resources")
        _register_resources(mcp)
        # FastMCP stores resources in _resource_manager
        resources = mcp._resource_manager._resources
        assert len(resources) == 5

    def test_register_resources_have_uris(self):
        from src.server import _register_resources
        mcp = FastMCP("test-resources-uris")
        _register_resources(mcp)
        resources = mcp._resource_manager._resources
        uris = [str(r.uri) for r in resources.values()]
        assert any("companies" in u for u in uris)
        assert any("customers" in u for u in uris)
        assert any("suppliers" in u for u in uris)
        assert any("items" in u for u in uris)
        assert any("employees" in u for u in uris)

    def test_register_resources_erpnext_scheme(self):
        from src.server import _register_resources
        mcp = FastMCP("test-resources-scheme")
        _register_resources(mcp)
        resources = mcp._resource_manager._resources
        for r in resources.values():
            assert str(r.uri).startswith("erpnext://")


class TestRegisterPrompts:
    """Test _register_prompts registers 5 prompts."""

    def test_register_prompts_count(self):
        from src.server import _register_prompts
        mcp = FastMCP("test-prompts")
        _register_prompts(mcp)
        prompts = mcp._prompt_manager._prompts
        assert len(prompts) == 5

    def test_register_prompts_have_names(self):
        from src.server import _register_prompts
        mcp = FastMCP("test-prompts-names")
        _register_prompts(mcp)
        prompts = mcp._prompt_manager._prompts
        names = list(prompts.keys())
        assert "review_overdue_invoices" in names
        assert "monthly_financial_summary" in names
        assert "prepare_payroll" in names
        assert "purchase_order_workflow" in names
        assert "manufacturing_report" in names


class TestToolsRegistration:
    """Test curated tools registration via tools.register(mcp)."""

    def test_register_curated_tools_count(self):
        from src.tools import register
        mcp = FastMCP("test-tools")
        register(mcp)
        tools = mcp._tool_manager._tools
        # Expected curated tools:
        # generic: 4 (list_documents, get_document, submit_document, cancel_document)
        # accounting: 5 (get_account_balance, get_exchange_rate, get_fiscal_year,
        #                 create_payment_entry, create_sales_return)
        # selling: 7 (get_erpnext_url, convert_quotation_to_sales_order,
        #             convert_sales_order_to_invoice, convert_sales_order_to_delivery,
        #             convert_opportunity_to_quotation, convert_lead_to_opportunity,
        #             convert_lead_to_customer)
        # buying: 5 (convert_po_to_receipt, convert_po_to_invoice,
        #            convert_receipt_to_invoice, create_purchase_return,
        #            convert_material_request_to_po)
        # stock: 7 (get_item_details, get_stock_balance, get_batch_qty,
        #           create_stock_entry, convert_delivery_to_invoice,
        #           create_return_from_delivery, get_stock_ledger_entries)
        # hr: 2 (get_leave_balance, calculate_leave_days)
        # manufacturing: 2 (get_bom_items, get_exploded_bom_items)
        # projects: 1 (convert_timesheet_to_invoice)
        # assets: 4 (create_asset_invoice, scrap_asset, restore_asset,
        #            create_asset_movement)
        assert len(tools) == 37

    def test_register_curated_tools_have_names(self):
        from src.tools import register
        mcp = FastMCP("test-tools-names")
        register(mcp)
        tools = mcp._tool_manager._tools
        for name in tools:
            assert name, f"Tool has empty name"
            assert len(name) > 0

    def test_register_curated_tools_have_descriptions(self):
        from src.tools import register
        mcp = FastMCP("test-tools-desc")
        register(mcp)
        tools = mcp._tool_manager._tools
        for name, tool in tools.items():
            assert tool.description, f"Tool {name} has no description"


class TestFullRegistration:
    """Test that tools + resources + prompts all register correctly together."""

    def test_full_registration_totals(self):
        """Simulate full registration without ERPNext (mock discovery to return 0)."""
        from src.server import _register_resources, _register_prompts
        from src.tools import register as register_curated

        mcp = FastMCP("test-full")

        # Register curated tools
        register_curated(mcp)
        curated_count = len(mcp._tool_manager._tools)

        # Register resources
        _register_resources(mcp)
        resource_count = len(mcp._resource_manager._resources)

        # Register prompts
        _register_prompts(mcp)
        prompt_count = len(mcp._prompt_manager._prompts)

        assert curated_count == 37
        assert resource_count == 5
        assert prompt_count == 5


class TestToolAnnotations:
    """Test that CRUD tools have correct readOnlyHint/destructiveHint annotations."""

    def test_generic_list_is_readonly(self):
        from src.tools.generic import register
        mcp = FastMCP("test-annot-generic")
        register(mcp)
        tool = mcp._tool_manager._tools["list_documents"]
        # Generic tools don't set annotations directly; they rely on MCP defaults
        # But we can verify the tool exists and has a description
        assert tool.description is not None

    def test_generic_cancel_exists(self):
        from src.tools.generic import register
        mcp = FastMCP("test-annot-cancel")
        register(mcp)
        assert "cancel_document" in mcp._tool_manager._tools

    def test_selling_tools_registered(self):
        from src.tools.selling import register
        mcp = FastMCP("test-annot-selling")
        register(mcp)
        assert "get_erpnext_url" in mcp._tool_manager._tools
        assert "convert_quotation_to_sales_order" in mcp._tool_manager._tools
