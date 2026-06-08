"""erpnext-mcp-server — MCP server for ERPNext.

Standalone MCP server that connects directly to any ERPNext instance.
No gateway, no business logic — just tool definitions and ERPNext API calls.

Tools come from two sources:
1. Auto-discovery: CRUD tools generated from DocType metadata at startup
2. Curated: High-level operations (conversions, reports, workflows)

Usage:
    python -m src.server              # stdio transport (default, for local agents)
    python -m src.server --http       # Streamable HTTP at http://127.0.0.1:8000/mcp
    python -m src.server --sse        # SSE transport at http://127.0.0.1:8000/sse
    python -m src.server --http --port 3000 --host 0.0.0.0
    python -m src.server --http --refresh  # force re-fetch DocType metadata
"""

import json
import logging
import sys
import time

from mcp.server.fastmcp import FastMCP

from .config import settings
from .discovery import discovery
from .tools import curated

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_start_time = time.time()

# ── MCP Server ────────────────────────────────────────────────

mcp = FastMCP(
    "erpnext",
    host=settings.http_host,
    instructions=(
        "ERPNext MCP Server: AI-native interface to ERPNext. "
        "Tools are auto-generated from your ERPNext DocTypes at startup. "
        "Use list_* tools to browse data, get_* to read, "
        "create_*/update_*/delete_* for mutations. "
        "Curated tools handle complex workflows (conversions, reports). "
        "All monetary values are in the company's default currency."
    ),
)

# ── CLI args (parsed once at import) ─────────────────────────


def _parse_args() -> dict:
    """Parse CLI args into transport config."""
    args = sys.argv[1:]
    transport = "stdio"
    host = settings.http_host
    port = settings.http_port
    refresh = "--refresh" in args

    if "--http" in args:
        transport = "streamable-http"
    elif "--sse" in args:
        transport = "sse"

    for i, arg in enumerate(args):
        if arg == "--host" and i + 1 < len(args):
            host = args[i + 1]
        elif arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    return {"transport": transport, "host": host, "port": port, "refresh": refresh}


config = _parse_args()


# ── Register tools ────────────────────────────────────────────

# 1. Auto-discovered CRUD tools from DocType metadata (cached)
log.info("Discovering DocTypes from ERPNext...")
crud_count = discovery.register_tools(
    mcp,
    include=settings.discovery_include_list,
    exclude=settings.discovery_exclude_list,
    force_refresh=config["refresh"],
)
log.info("Auto-discovered %d CRUD tools", crud_count)

# 2. Curated tools (conversions, reports, workflows)
curated.register(mcp)
log.info("Registered curated tools")

_total_tools = crud_count + curated.TOOL_COUNT


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
    transport = config["transport"]

    if transport == "streamable-http":
        import uvicorn
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        mcp_api_key = settings.mcp_api_key

        # Get FastMCP's ASGI app
        mcp_app = mcp.streamable_http_app()

        async def health(request: Request) -> JSONResponse:
            """Health check endpoint for Docker/load balancers."""
            return JSONResponse({
                "status": "ok",
                "server": "erpnext-mcp-server",
                "tools": _total_tools,
                "uptime_seconds": round(time.time() - _start_time, 1),
            })

        async def dispatch(scope, receive, send):
            """Route: /health → health handler, everything else → FastMCP (with auth)."""
            path = scope.get("path", "/")

            # Health check — no auth required
            if path == "/health" and scope["type"] == "http":
                response = JSONResponse({
                    "status": "ok",
                    "server": "erpnext-mcp-server",
                    "tools": _total_tools,
                    "uptime_seconds": round(time.time() - _start_time, 1),
                })
                return await response(scope, receive, send)

            # Auth check for MCP endpoints
            if scope["type"] == "http" and mcp_api_key:
                headers = dict(scope.get("headers", []))
                auth = headers.get(b"authorization", b"").decode()
                if not auth.startswith("Bearer ") or auth[7:] != mcp_api_key:
                    response = JSONResponse(
                        {"error": "Unauthorized", "detail": "Invalid or missing Bearer token"},
                        status_code=401,
                    )
                    return await response(scope, receive, send)

            # Delegate to FastMCP
            return await mcp_app(scope, receive, send)

        app = dispatch

        if mcp_api_key:
            log.info("Auth enabled (ERPNEXT_MCP_API_KEY is set)")
        log.info(
            "Starting HTTP at http://%s:%d (health: /health, mcp: /mcp)",
            config["host"], config["port"],
        )
        uvicorn.run(app, host=config["host"], port=config["port"],
                    log_level="info")
    elif transport == "sse":
        mcp.settings.host = config["host"]
        mcp.settings.port = config["port"]
        log.info("Starting SSE at http://%s:%d/sse", config["host"], config["port"])
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
