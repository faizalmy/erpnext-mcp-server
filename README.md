# erpnext-mcp-server

**Standalone MCP server for ERPNext.** No gateway, no middleware — connects directly to any ERPNext instance. Tools are auto-generated from DocType metadata at startup and served as 290+ MCP tools over stdio or HTTP.

```
AI Agent ──MCP──▶ erpnext-mcp-server ──REST──▶ ERPNext
 (Claude,            │                           (any instance)
  Cursor,     ┌──────┴──────┐
  Hermes)     │  290+ tools  │
              │  CRUD + workflows
              └─────────────┘
```

## Quick Start

```bash
git clone https://github.com/faizalmy/erpnext-mcp-server.git
cd erpnext-mcp-server
cp .env.example .env
# Edit .env — set ERPNEXT_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET
uv venv && uv pip install -e ".[dev]"
python -m src.server           # stdio (default)
```

## Run

```bash
python -m src.server              # stdio (local agents)
python -m src.server --http       # Streamable HTTP at :8000/mcp
python -m src.server --http --host 0.0.0.0 --port 3000
python -m src.server --http --refresh   # force re-fetch DocType metadata
python -m src.server --sse        # SSE transport (legacy)
```

## Configuration

`.env` file (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `ERPNEXT_URL` | `http://localhost:8080` | ERPNext instance URL |
| `ERPNEXT_API_KEY` | | Token auth — generate in User > API Access |
| `ERPNEXT_API_SECRET` | | Token auth — paired with API key |
| `ERPNEXT_USR` | `Administrator` | Password auth (dev only) |
| `ERPNEXT_PWD` | `admin` | Password auth (dev only) |
| `ERPNEXT_DISCOVERY_INCLUDE` | (51 core DocTypes) | Comma-separated DocTypes to discover |
| `ERPNEXT_DISCOVERY_EXCLUDE` | | Comma-separated DocTypes to skip |
| `ERPNEXT_DISCOVERY_MODULES` | | Module filter (e.g. `Selling,Buying,Stock`) |
| `HTTP_HOST` | `127.0.0.1` | HTTP transport bind address |
| `HTTP_PORT` | `3000` | HTTP transport port |
| `MCP_API_KEY` | | API key for HTTP transport auth (empty = no auth) |
| `CONCISE_DESCRIPTIONS` | `false` | Short tool descriptions (saves ~60% schema tokens) |
| `MAX_RESPONSE_CHARS` | `0` | Truncate large responses (0 = no limit) |

**Token auth** (production): set `ERPNEXT_API_KEY` + `ERPNEXT_API_SECRET`.

**Password auth** (dev): leave API key/secret empty. Client auto-logins via session cookie.

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

### Multi-Tenant (HTTP headers)

Pass per-request ERPNext credentials via HTTP headers:

- `X-ERPNext-URL` — override ERPNext instance
- `X-ERPNext-API-Key` — override API key
- `X-ERPNext-API-Secret` — override API secret

## How Tools Are Generated

At startup:

1. **Discover DocTypes** — queries ERPNext for the 51 core business DocTypes
2. **Fetch field metadata** — gets field definitions via `frappe.client.get`
3. **Generate CRUD tools** — creates `list_*`, `get_*`, `create_*`, `update_*`, `delete_*` per DocType
4. **Register curated tools** — high-level operations (conversions, reports, workflows)

Results are cached to `.cache/doctypes.json` (24h TTL). Use `--refresh` or `ERPNEXT_CACHE_TTL=0` to bypass.

## Tool Categories

### Auto-Discovered CRUD (255 tools)

Each DocType gets 5 tools: `list_*`, `get_*`, `create_*`, `update_*`, `delete_*`.

### Curated Tools (37 tools)

| Module | Tools |
|---|---|
| Generic | `list_documents`, `get_document`, `submit_document`, `cancel_document` |
| Accounting | `get_account_balance`, `get_exchange_rate`, `get_fiscal_year`, `create_payment_entry`, `create_sales_return` |
| Selling | `get_erpnext_url`, `convert_quotation_to_sales_order`, `convert_sales_order_to_invoice`, `convert_sales_order_to_delivery`, `convert_opportunity_to_quotation`, `convert_lead_to_opportunity`, `convert_lead_to_customer` |
| Buying | `convert_po_to_receipt`, `convert_po_to_invoice`, `convert_receipt_to_invoice`, `create_purchase_return`, `convert_material_request_to_po` |
| Stock | `get_item_details`, `get_stock_balance`, `get_batch_qty`, `create_stock_entry`, `convert_delivery_to_invoice`, `create_return_from_delivery`, `get_stock_ledger_entries` |
| HR | `get_leave_balance`, `calculate_leave_days` |
| Manufacturing | `get_bom_items`, `get_exploded_bom_items` |
| Projects | `convert_timesheet_to_invoice` |
| Assets | `create_asset_invoice`, `scrap_asset`, `restore_asset`, `create_asset_movement` |

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
docker compose up -d
```

Docker Compose runs HTTP mode on port 8090. Configure ERPNext credentials via `.env`.

## Project Structure

```
src/
├── server.py              # FastMCP entry point (stdio / HTTP / SSE)
├── config.py              # Settings (env vars)
├── erpnext_client.py      # httpx client → ERPNext REST API
├── discovery.py           # Auto-discovers DocTypes, generates CRUD tools
└── tools/
    ├── generic.py         # Document ops (submit, cancel)
    ├── accounting.py      # Balances, payments, returns, exchange rates
    ├── selling.py         # Sales pipeline conversions
    ├── buying.py          # Purchase document conversions
    ├── stock.py           # Inventory, stock entries, deliveries
    ├── hr.py              # Leave balance and calculations
    ├── manufacturing.py   # BOM item listings
    ├── projects.py        # Timesheet invoicing
    └── assets.py          # Asset lifecycle (invoice, scrap, restore, move)
tests/
├── test_config.py
├── test_discovery.py
├── test_erpnext_client.py
├── test_server.py
├── test_stdio.py
└── test_tools.py
```

## Tests

```bash
pytest tests/ -v
```

## License

MIT
