"""erpnext-mcp-server — MCP server for ERPNext.

Standalone MCP server that connects directly to any ERPNext instance.
No gateway, no business logic — just tool definitions and ERPNext API calls.

Usage:
    python -m src.server          # stdio transport (default)
    python -m src.server --sse    # SSE transport (for remote agents)
"""

import sys

from mcp.server.fastmcp import FastMCP

from .tools import (
    documents, accounting, selling, buying, stock,
    hr, manufacturing, projects, assets,
)

# ── MCP Server ────────────────────────────────────────────────

mcp = FastMCP(
    "erpnext",
    instructions=(
        "ERPNext MCP Server: AI-native interface to ERPNext. "
        "All monetary values are in the company's default currency. "
        "Use list_documents for generic DocType queries. "
        "Use specialized tools (create_sales_invoice, etc.) for domain operations."
    ),
)

# ── Register tool groups ──────────────────────────────────────

documents.register(mcp)
accounting.register(mcp)
selling.register(mcp)
buying.register(mcp)
stock.register(mcp)
hr.register(mcp)
manufacturing.register(mcp)
projects.register(mcp)
assets.register(mcp)

# ── MCP Resources (read-only structured data) ─────────────────


@mcp.resource("erpnext://companies")
def list_companies() -> dict:
    """List all companies in ERPNext."""
    from .erpnext_client import erpnext
    return erpnext.list_documents("Company", fields=["name", "country", "default_currency"])


@mcp.resource("erpnext://customers")
def list_customers() -> dict:
    """List all customers."""
    from .erpnext_client import erpnext
    return erpnext.list_documents(
        "Customer",
        fields=["name", "customer_name", "territory", "customer_group"],
        limit=50,
    )


@mcp.resource("erpnext://suppliers")
def list_suppliers() -> dict:
    """List all suppliers."""
    from .erpnext_client import erpnext
    return erpnext.list_documents(
        "Supplier",
        fields=["name", "supplier_name", "supplier_group"],
        limit=50,
    )


@mcp.resource("erpnext://items")
def list_items() -> dict:
    """List all items (products/services)."""
    from .erpnext_client import erpnext
    return erpnext.list_documents(
        "Item",
        fields=["name", "item_name", "item_group", "standard_rate"],
        limit=50,
    )


@mcp.resource("erpnext://employees")
def list_employees() -> dict:
    """List all active employees."""
    from .erpnext_client import erpnext
    return erpnext.list_documents(
        "Employee",
        fields=["name", "employee_name", "department", "designation", "status"],
        filters=[["Employee", "status", "=", "Active"]],
        limit=50,
    )


# ── MCP Prompts (pre-built workflows) ────────────────────────


@mcp.prompt()
def review_overdue_invoices() -> str:
    """Analyze overdue invoices and suggest follow-up actions."""
    return (
        "List all overdue Sales Invoices in ERPNext. "
        "For each invoice, calculate how many days overdue it is. "
        "Group by customer and suggest follow-up actions: "
        "send reminder, escalate, write off, or initiate legal. "
        "Include the total overdue amount."
    )


@mcp.prompt()
def monthly_financial_summary() -> str:
    """Generate a monthly financial summary."""
    return (
        "Generate a financial summary for this month:\n"
        "1. Get the Profit & Loss statement\n"
        "2. Get the Balance Sheet\n"
        "3. List all outstanding invoices (unpaid)\n"
        "4. Summarize: revenue, expenses, net profit, cash position\n"
        "5. Highlight any concerns (overdue invoices, unusual expenses)\n"
        "6. Suggest 2-3 actions to improve cash flow"
    )


@mcp.prompt()
def prepare_payroll(company: str = "", month: str = "", year: str = "") -> str:
    """Prepare payroll with statutory breakdown."""
    return (
        f"Prepare payroll for {company or '[company]'} "
        f"for {month or '[month]'} {year or '[year]'}:\n"
        "1. Get all active employees for the company\n"
        "2. Calculate gross salary for each employee\n"
        "3. Apply statutory deductions (EPF, SOCSO, PCB, EIS)\n"
        "4. Show per-employee breakdown\n"
        "5. Show total employer cost"
    )


@mcp.prompt()
def purchase_order_workflow(supplier: str = "") -> str:
    """End-to-end purchase order workflow."""
    return (
        f"Create a purchase order for {supplier or '[supplier]'}:\n"
        "1. Check current stock levels for items below reorder level\n"
        "2. List recent purchase prices for these items\n"
        "3. Create a Material Request for items needed\n"
        "4. Convert Material Request to Purchase Order"
    )


@mcp.prompt()
def manufacturing_report() -> str:
    """Manufacturing status report."""
    return (
        "Generate a manufacturing status report:\n"
        "1. List all open Work Orders\n"
        "2. For each: show progress, raw material availability, and status\n"
        "3. List overdue Work Orders (past planned start date)\n"
        "4. Show raw material stock levels vs BOM requirements\n"
        "5. Suggest prioritization and any material requests needed"
    )


# ── Entry point ───────────────────────────────────────────────


def main():
    """Run the MCP server."""
    transport = "stdio"
    if "--sse" in sys.argv:
        transport = "sse"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
