"""AI-ERP MCP Server — entry point.

This is the thin Layer 1 of the two-layer architecture:
- Defines MCP tools (what the agent can call)
- Forwards all calls to the AI-ERP Gateway (Layer 2)
- Returns structured responses with ai_context

The server has ZERO business logic — no auth, no approval engine,
no ERPNext client, no statutory validation. All of that lives in the gateway.

Usage:
    python -m src.server          # stdio transport (default)
    python -m src.server --sse    # SSE transport (for remote agents)
"""

import sys

from mcp.server.fastmcp import FastMCP

from .tools import documents, accounting, hr, approvals

# ── MCP Server ────────────────────────────────────────────────

mcp = FastMCP(
    "ai-erp",
    instructions=(
        "AI-ERP: AI-native ERP for Malaysian SMEs. "
        "Financial operations require human approval before execution. "
        "All monetary values are in MYR. "
        "SST 8% is applied automatically by ERPNext. "
        "Use list_intents to check pending approvals. "
        "Use approve_intent or reject_intent to act on them."
    ),
)

# ── Register tool groups ──────────────────────────────────────

documents.register(mcp)
accounting.register(mcp)
hr.register(mcp)
approvals.register(mcp)

# ── MCP Resources (read-only structured data) ─────────────────


@mcp.resource("erpnext://companies")
def list_companies() -> dict:
    """List all companies in ERPNext."""
    from .gateway import gateway
    return gateway.list_documents("Company", fields=["name", "country", "default_currency"])


@mcp.resource("erpnext://customers")
def list_customers() -> dict:
    """List all customers."""
    from .gateway import gateway
    return gateway.list_documents(
        "Customer",
        fields=["name", "customer_name", "territory", "customer_group"],
        limit=50,
    )


@mcp.resource("erpnext://suppliers")
def list_suppliers() -> dict:
    """List all suppliers."""
    from .gateway import gateway
    return gateway.list_documents(
        "Supplier",
        fields=["name", "supplier_name", "supplier_group"],
        limit=50,
    )


@mcp.resource("erpnext://items")
def list_items() -> dict:
    """List all items (products/services)."""
    from .gateway import gateway
    return gateway.list_documents(
        "Item",
        fields=["name", "item_name", "item_group", "standard_rate"],
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
        "Include the total overdue amount in MYR."
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
    """Prepare payroll for approval with statutory breakdown."""
    return (
        f"Prepare payroll for {company or '[company]'} "
        f"for {month or '[month]'} {year or '[year]'}:\n"
        "1. Get all active employees for the company\n"
        "2. Calculate gross salary for each employee\n"
        "3. Apply Malaysia statutory deductions:\n"
        "   - EPF: Employee 11%, Employer 13% (for salary > RM5,000)\n"
        "   - SOCSO: Based on salary tier\n"
        "   - PCB: Based on tax bracket\n"
        "   - EIS: 0.2% each (employer + employee)\n"
        "4. Show per-employee breakdown\n"
        "5. Show total employer cost\n"
        "6. Submit for approval"
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
