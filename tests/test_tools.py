"""Integration tests for curated tools modules — register functions.

Each tools/ module exposes a register(mcp) function that adds tools to a FastMCP instance.
These tests verify each module registers the expected tools.
"""

import pytest
from mcp.server.fastmcp import FastMCP

from src.tools import register as register_all


# ═══════════════════════════════════════════════════════════════
# Per-module registration
# ═══════════════════════════════════════════════════════════════

class TestGenericRegister:
    """Test generic.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.generic import register
        mcp = FastMCP("test-generic")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "list_documents" in tools
        assert "get_document" in tools
        assert "submit_document" in tools
        assert "cancel_document" in tools
        assert len(tools) == 4


class TestAccountingRegister:
    """Test accounting.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.accounting import register
        mcp = FastMCP("test-accounting")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "get_account_balance" in tools
        assert "get_exchange_rate" in tools
        assert "get_fiscal_year" in tools
        assert "create_payment_entry" in tools
        assert "create_sales_return" in tools
        assert len(tools) == 5


class TestSellingRegister:
    """Test selling.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.selling import register
        mcp = FastMCP("test-selling")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "get_erpnext_url" in tools
        assert "convert_quotation_to_sales_order" in tools
        assert "convert_sales_order_to_invoice" in tools
        assert "convert_sales_order_to_delivery" in tools
        assert "convert_opportunity_to_quotation" in tools
        assert "convert_lead_to_opportunity" in tools
        assert "convert_lead_to_customer" in tools
        assert len(tools) == 7


class TestBuyingRegister:
    """Test buying.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.buying import register
        mcp = FastMCP("test-buying")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "convert_po_to_receipt" in tools
        assert "convert_po_to_invoice" in tools
        assert "convert_receipt_to_invoice" in tools
        assert "create_purchase_return" in tools
        assert "convert_material_request_to_po" in tools
        assert len(tools) == 5


class TestStockRegister:
    """Test stock.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.stock import register
        mcp = FastMCP("test-stock")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "get_item_details" in tools
        assert "get_stock_balance" in tools
        assert "get_batch_qty" in tools
        assert "create_stock_entry" in tools
        assert "convert_delivery_to_invoice" in tools
        assert "create_return_from_delivery" in tools
        assert "get_stock_ledger_entries" in tools
        assert len(tools) == 7


class TestHRRegister:
    """Test hr.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.hr import register
        mcp = FastMCP("test-hr")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "get_leave_balance" in tools
        assert "calculate_leave_days" in tools
        assert len(tools) == 2


class TestManufacturingRegister:
    """Test manufacturing.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.manufacturing import register
        mcp = FastMCP("test-manufacturing")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "get_bom_items" in tools
        assert "get_exploded_bom_items" in tools
        assert len(tools) == 2


class TestProjectsRegister:
    """Test projects.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.projects import register
        mcp = FastMCP("test-projects")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "convert_timesheet_to_invoice" in tools
        assert len(tools) == 1


class TestAssetsRegister:
    """Test assets.py register function."""

    def test_registers_expected_tools(self):
        from src.tools.assets import register
        mcp = FastMCP("test-assets")
        register(mcp)
        tools = mcp._tool_manager._tools
        assert "create_asset_invoice" in tools
        assert "scrap_asset" in tools
        assert "restore_asset" in tools
        assert "create_asset_movement" in tools
        assert len(tools) == 4


# ═══════════════════════════════════════════════════════════════
# Combined registration
# ═══════════════════════════════════════════════════════════════

class TestAllModulesRegister:
    """Test that importing and calling all register functions works without errors."""

    def test_all_modules_register_no_errors(self):
        mcp = FastMCP("test-all")
        register_all(mcp)
        tools = mcp._tool_manager._tools
        # 4 + 5 + 7 + 5 + 7 + 2 + 2 + 1 + 4 = 37
        assert len(tools) == 37

    def test_all_tools_have_descriptions(self):
        mcp = FastMCP("test-all-desc")
        register_all(mcp)
        for name, tool in mcp._tool_manager._tools.items():
            assert tool.description, f"Tool '{name}' missing description"
            assert len(tool.description) > 10, f"Tool '{name}' description too short"

    def test_no_duplicate_tool_names(self):
        mcp = FastMCP("test-all-dupes")
        register_all(mcp)
        names = list(mcp._tool_manager._tools.keys())
        assert len(names) == len(set(names)), "Duplicate tool names found"
