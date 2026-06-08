# erpnext-mcp-server

**Standalone MCP server for ERPNext.** Connects directly to any ERPNext instance — no gateway, no middleware, no business logic.

Tools are **auto-generated from DocType metadata** at startup. The server adapts to whatever DocTypes exist in your ERPNext.

```
AI Agent (Claude, ChatGPT, Hermes, Cursor, etc.)
    │
    ▼ MCP protocol (stdio / HTTP)
┌──────────────────────────┐
│  erpnext-mcp-server       │
│  discovery.py (auto-CRUD) │  ← generates tools from DocType metadata
│  tools/curated.py (smart) │  ← conversions, reports, workflows
└──────────┬───────────────┘
           │ REST API
┌──────────▼───────────────┐
│  ERPNext instance         │
└──────────────────────────┘
```

## Setup

```bash
git clone https://github.com/faizalmy/erpnext-mcp-server.git
cd erpnext-mcp-server
cp .env.example .env
# Edit .env — point at your ERPNext
uv venv && uv pip install -e ".[dev]"
```

## Run

```bash
# stdio transport (default — for local agents like Claude Desktop)
python -m src.server

# Streamable HTTP transport (for remote agents / gateways)
python -m src.server --http

# HTTP with custom host/port
python -m src.server --http --host 0.0.0.0 --port 3000

# SSE transport (legacy)
python -m src.server --sse

# Tests
pytest tests/ -v
```

## Configuration

`.env` file:

| Variable | Default | Description |
|---|---|---|
| `ERPNEXT_URL` | `http://localhost:8080` | Your ERPNext instance |
| `ERPNEXT_API_KEY` | | Token auth — generate in User > API Access |
| `ERPNEXT_API_SECRET` | | Token auth — paired with API key |
| `ERPNEXT_USR` | `Administrator` | Password auth (dev only) |
| `ERPNEXT_PWD` | `admin` | Password auth (dev only) |
| `ERPNEXT_DISCOVERY_INCLUDE` | (44 core DocTypes) | Comma-separated DocTypes to discover |
| `ERPNEXT_DISCOVERY_EXCLUDE` | | Comma-separated DocTypes to skip |
| `HTTP_HOST` | `127.0.0.1` | HTTP transport bind address |
| `HTTP_PORT` | `3000` | HTTP transport port |
| `MCP_API_KEY` | | API key for HTTP transport auth (empty = no auth) |

**Token auth** (production): set `ERPNEXT_API_KEY` + `ERPNEXT_API_SECRET`.

**Password auth** (dev): leave API key/secret empty. Client auto-logins via session cookie.

**Discovery filter**: override `ERPNEXT_DISCOVERY_INCLUDE` to discover specific DocTypes, or `ERPNEXT_DISCOVERY_EXCLUDE` to skip some.

## MCP Client Config

### stdio (Claude Desktop, Cursor, etc.)

```json
{
  "mcpServers": {
    "erpnext": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/erpnext-mcp-server"
    }
  }
}
```

### HTTP (remote agents, gateways)

Start the server:
```bash
python -m src.server --http --port 3000
```

Connect to `http://127.0.0.1:3000/mcp` using Streamable HTTP transport.

```json
{
  "mcpServers": {
    "erpnext": {
      "url": "http://127.0.0.1:3000/mcp"
    }
  }
}
```

## How Tools Are Generated

At startup, the server:

1. **Discovers DocTypes** — queries ERPNext for the 44 core business DocTypes (Customer, Sales Invoice, Employee, etc.)
2. **Fetches field metadata** — gets field definitions for each DocType via `frappe.client.get`
3. **Generates CRUD tools** — creates `list_*`, `get_*`, `create_*`, `update_*`, `delete_*` for each DocType with field-aware inputSchemas
4. **Registers curated tools** — high-level tools for conversions, reports, and workflows

## Tool Categories

### Auto-discovered CRUD (220 tools)

Each of the 44 DocTypes gets 5 tools:

| Tool | Action |
|---|---|
| `list_Customer` | List records with filters |
| `get_Customer` | Get single record by name |
| `create_Customer` | Create new record (field-aware schema) |
| `update_Customer` | Partial update |
| `delete_Customer` | Delete permanently |

### Curated tools

High-level operations that need business logic:

| Category | Tools |
|---|---|
| Generic | `submit_document`, `cancel_document` |
| Selling | `convert_quotation_to_sales_order`, `convert_sales_order_to_invoice`, `convert_sales_order_to_delivery`, `convert_opportunity_to_quotation`, `convert_lead_to_opportunity`, `convert_lead_to_customer` |
| Buying | `convert_po_to_receipt`, `convert_po_to_invoice`, `convert_receipt_to_invoice`, `convert_material_request_to_po` |
| Stock | `convert_delivery_to_invoice` |
| HR | `calculate_leave_days` |
| Projects | `convert_timesheet_to_invoice` |
| Assets | `scrap_asset`, `restore_asset` |

## Resources

- `erpnext://companies` — companies
- `erpnext://customers` — customers
- `erpnext://suppliers` — suppliers
- `erpnext://items` — items
- `erpnext://employees` — active employees

## Prompts

- `review_overdue_invoices` — overdue invoice analysis
- `monthly_financial_summary` — P&L + balance sheet
- `prepare_payroll` — payroll with statutory breakdown
- `purchase_order_workflow` — PO from stock levels
- `manufacturing_report` — work order status + materials

## Docker

```bash
# Build and run
docker compose up -d

# With custom ERPNext credentials
ERPNEXT_URL=http://host.docker.internal:8080 \
ERPNEXT_API_KEY=your_key \
ERPNEXT_API_SECRET=your_secret \
docker compose up -d
```

Docker Compose runs the server in HTTP mode on port 3000.

### Known Issues / Pitfalls

**DNS rebinding 421 in Docker (MCP SDK security)**

FastMCP defaults to `host="127.0.0.1"` which auto-enables DNS rebinding protection with only `localhost` in `allowed_hosts`. When running in Docker, requests from other containers use `Host: service-name:port` (e.g., `Host: mcp-server:3000`) which gets rejected with `421 Misdirected Request`.

Fix: pass `host=settings.http_host` to the `FastMCP()` constructor in `src/server.py`:
```python
mcp = FastMCP(
    "erpnext",
    host=settings.http_host,  # ← required for Docker
    ...
)
```

When `host="0.0.0.0"`, FastMCP skips the DNS rebinding check entirely. After changing, rebuild with `docker compose build --no-cache` (old layers cache the default).

**`frappe.desk.form.meta.get_meta` returns 403**

The discovery module fetches DocType metadata via `frappe.client.get(doctype="DocType", name=...)` instead. Do not use `frappe.desk.form.meta.get_meta` — it requires elevated permissions that API users don't have.

**Env prefix removed**

Config fields map directly to env vars: `ERPNEXT_URL`, `ERPNEXT_API_KEY`, `HTTP_HOST`, `HTTP_PORT`, `MCP_API_KEY`. There is no `ERPNEXT_` prefix on HTTP/MCP settings.

## Project Structure

```
src/
├── server.py              # FastMCP entry point (stdio / HTTP / SSE)
├── config.py              # Settings (env vars)
├── erpnext_client.py      # httpx client → ERPNext REST API
├── discovery.py           # Auto-discovers DocTypes, generates CRUD tools
└── tools/
    └── curated.py         # High-level tools (conversions, reports)
tests/
└── test_erpnext_client.py # Mocked HTTP tests
```

## License

MIT
