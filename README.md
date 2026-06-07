# erpnext-mcp-server

**Standalone MCP server for ERPNext.** Connects directly to any ERPNext instance — no gateway, no middleware, no business logic.

Open source. Any developer can point it at their ERPNext and get AI agent access instantly.

```
AI Agent (Claude, ChatGPT, Hermes, Cursor, etc.)
    │
    ▼ MCP protocol (stdio)
┌──────────────────────────┐
│  erpnext-mcp-server       │  ← tool definitions + direct ERPNext API calls
│  ~115 tools, zero logic   │     no auth layer, no approval engine
└──────────┬───────────────┘
           │ REST API
┌──────────▼───────────────┐
│  ERPNext instance         │  ← the actual ERP
└──────────────────────────┘
```

## Quick Start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Configure (point at your ERPNext)
cp .env.example .env
# Edit .env — set ERPNEXT_URL and auth credentials

# 3. Run (stdio transport, for MCP clients)
python -m src.server

# 4. Run tests
pytest tests/ -v
```

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `ERPNEXT_URL` | `http://localhost:8080` | ERPNext instance URL |
| `ERPNEXT_API_KEY` | (empty) | API key (token auth) |
| `ERPNEXT_API_SECRET` | (empty) | API secret (token auth) |
| `ERPNEXT_USR` | `Administrator` | Username (password auth, dev only) |
| `ERPNEXT_PWD` | `admin` | Password (password auth, dev only) |

**Auth modes:**
- **Token auth** (production): Set `ERPNEXT_API_KEY` and `ERPNEXT_API_SECRET`. Generate in ERPNext: User > API Access > Generate Keys.
- **Password auth** (development): Leave API key/secret empty. Uses session cookies.

## Tools (118 total)

| Module | Tools | Covers |
|---|---|---|
| Documents | 5 | Generic CRUD on ANY DocType |
| Accounting | 5 | Invoices, payments, P&L, trial balance, balance sheet |
| Selling | 17 | Customer, Sales Order, Quotation, Lead, Opportunity, CRM |
| Buying | 13 | Supplier, PO, Purchase Receipt, Material Request, returns |
| Stock | 17 | Item, Stock Entry, Delivery Note, Stock Balance, Batch, Serial No |
| HR | 25 | Employee, Leave, Attendance, Expense, Payroll, Salary, Loan |
| Manufacturing | 13 | Work Order, BOM, Production Plan, Job Card |
| Projects | 9 | Project, Task, Timesheet |
| Assets | 10 | Asset, Category, Maintenance, Repair, Scrap, Restore |

## MCP Resources

- `erpnext://companies` — List companies
- `erpnext://customers` — List customers
- `erpnext://suppliers` — List suppliers
- `erpnext://items` — List items
- `erpnext://employees` — List active employees

## MCP Prompts

- `review_overdue_invoices` — Analyze overdue invoices and suggest actions
- `monthly_financial_summary` — Monthly P&L + balance sheet summary
- `prepare_payroll` — Prepare payroll with statutory breakdown
- `purchase_order_workflow` — End-to-end PO from stock levels
- `manufacturing_report` — Work order status and material availability

## How It Works

This server has **zero business logic**. It:

1. Defines MCP tools (name, description, inputSchema)
2. Calls ERPNext's REST API directly
3. Returns ERPNext's response

All business logic (approvals, validation, compliance) lives in ERPNext itself. This server is purely a protocol adapter.

## ERPNext API Coverage

The server uses two ERPNext API types:

**Resource API** (generic CRUD):
```
GET    /api/resource/{DocType}           # List
POST   /api/resource/{DocType}           # Create
GET    /api/resource/{DocType}/{name}    # Read
PUT    /api/resource/{DocType}/{name}    # Update
DELETE /api/resource/{DocType}/{name}    # Delete
```

**Method API** (whitelisted functions):
```
GET/POST /api/method/{dotted.path}       # Call any whitelisted function
```

## Project Structure

```
erpnext-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP server entry point (FastMCP)
│   ├── config.py              # Settings (ERPNext URL, auth)
│   ├── erpnext_client.py      # Direct ERPNext REST API client
│   └── tools/
│       ├── documents.py       # Generic DocType CRUD
│       ├── accounting.py      # Invoices, payments, reports
│       ├── selling.py         # Customer, SO, Quotation, Lead, Opportunity
│       ├── buying.py          # Supplier, PO, PR, Material Request
│       ├── stock.py           # Item, Stock Entry, DN, Balance, Batch
│       ├── hr.py              # Employee, Leave, Attendance, Payroll
│       ├── manufacturing.py   # Work Order, BOM, Production Plan
│       ├── projects.py        # Project, Task, Timesheet
│       └── assets.py          # Asset, Maintenance, Repair
├── tests/
│   └── test_erpnext_client.py # Client tests (mocked HTTP)
├── pyproject.toml
├── .env.example
└── README.md
```

## License

MIT
