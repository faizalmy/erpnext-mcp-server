# erpnext-mcp-server

**Standalone MCP server for ERPNext.** Connects directly to any ERPNext instance — no gateway, no middleware, no business logic.

```
AI Agent (Claude, ChatGPT, Hermes, Cursor, etc.)
    │
    ▼ MCP protocol (stdio)
┌──────────────────────────┐
│  erpnext-mcp-server       │  ← 121 tools, zero logic
└──────────┬───────────────┘
           │ REST API
┌──────────▼───────────────┐
│  ERPNext instance         │
└──────────────────────────┘
```

## Setup

```bash
git clone https://github.com/your-org/erpnext-mcp-server.git
cd erpnext-mcp-server
cp .env.example .env
# Edit .env — point at your ERPNext
uv venv && uv pip install -e ".[dev]"
```

## Run

```bash
# MCP server (stdio transport)
python -m src.server

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

**Token auth** (production): set `ERPNEXT_API_KEY` + `ERPNEXT_API_SECRET`.

**Password auth** (dev): leave API key/secret empty. Client auto-logins via session cookie.

## MCP Client Config

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

## Tools (121)

| Module | Tools | What |
|---|---|---|
| Documents | 5 | Generic CRUD on any DocType |
| Accounting | 12 | Invoices, payments, journals, P&L, balance sheet, trial balance |
| Selling | 17 | Customer, SO, quotation, lead, opportunity, CRM |
| Buying | 13 | Supplier, PO, receipt, material request, returns |
| Stock | 17 | Item, stock entry, DN, balance, batch, serial, warehouse |
| HR | 25 | Employee, leave, attendance, expense, payroll, salary, loan |
| Manufacturing | 13 | Work order, BOM, production plan, job card |
| Projects | 9 | Project, task, timesheet |
| Assets | 10 | Asset, category, maintenance, repair, scrap |

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

## Project Structure

```
src/
├── server.py              # FastMCP entry point
├── config.py              # Settings (env vars)
├── erpnext_client.py      # httpx client → ERPNext REST API
└── tools/
    ├── documents.py       # Generic CRUD
    ├── accounting.py      # Invoices, payments, reports
    ├── selling.py         # Sales cycle
    ├── buying.py          # Purchase cycle
    ├── stock.py           # Inventory
    ├── hr.py              # HR & payroll
    ├── manufacturing.py   # Production
    ├── projects.py        # Projects & timesheets
    └── assets.py          # Fixed assets
tests/
└── test_erpnext_client.py # Mocked HTTP tests
```

## How It Works

Zero business logic. The server:

1. Defines MCP tools (name, description, inputSchema)
2. Calls ERPNext REST API (Resource API + Method API)
3. Returns the response

All business logic lives in ERPNext. This is a protocol adapter.

## License

MIT
