# AI-ERP MCP Server

**Layer 1 of the AI-ERP two-layer architecture.**

This is the thin MCP protocol adapter that AI agents connect to.
It defines tools, forwards calls to the [AI-ERP Gateway](../gateway/), and returns structured responses.

```
AI Agent (Hermes, Claude, ChatGPT)
    │
    ▼ MCP protocol (stdio)
┌──────────────────────┐
│   MCP Server (this)   │  ← tool definitions, HTTP forwarding
│   ~200 lines          │     no business logic
└──────────┬───────────┘
           │ HTTP
┌──────────▼───────────┐
│   AI-ERP Gateway      │  ← auth, approval, ERPNext, audit
│   (separate service)  │     all business logic lives here
└──────────┬───────────┘
           │ REST API
┌──────────▼───────────┐
│   ERPNext             │  ← deterministic accounting engine
└──────────────────────┘
```

## Quick Start

```bash
# 1. Install
cd mcp-server
pip install -e ".[dev]"

# 2. Configure
cp .env.example .env
# Edit .env — set GATEWAY_URL and GATEWAY_API_KEY

# 3. Run (stdio transport, for MCP clients)
python -m src.server

# 4. Run tests
pytest tests/ -v
```

## Tools

| Category | Tool | Description | Approval? |
|---|---|---|---|
| **Documents** | `list_documents` | List any ERPNext DocType | No |
| | `get_document` | Get single document | No |
| | `create_document` | Create document | Yes |
| | `update_document` | Update document | Yes |
| | `submit_document` | Submit (finalize) document | Yes |
| **Accounting** | `create_invoice` | Sales invoice with SST | Yes |
| | `record_payment` | Record payment | Yes |
| | `get_trial_balance` | Trial balance report | No |
| | `get_profit_and_loss` | P&L statement | No |
| | `get_balance_sheet` | Balance sheet | No |
| **HR** | `create_employee` | Employee record | Yes |
| | `run_payroll` | Run monthly payroll (MY statutory) | Yes |
| | `get_leave_balance` | Employee leave balance | No |
| | `submit_expense` | Expense claim | Yes |
| **Approvals** | `list_intents` | List approval requests | No |
| | `approve_intent` | Approve pending intent | No |
| | `reject_intent` | Reject pending intent | No |
| | `get_audit_log` | Audit trail | No |

## MCP Resources

- `erpnext://companies` — List companies
- `erpnext://customers` — List customers
- `erpnext://suppliers` — List suppliers
- `erpnext://items` — List items

## MCP Prompts

- `review_overdue_invoices` — Analyze overdue invoices
- `monthly_financial_summary` — Monthly P&L + balance sheet summary
- `prepare_payroll` — Prepare payroll with Malaysia statutory breakdown

## Architecture

**This server has ZERO business logic.** It:

1. Defines MCP tools (name, description, inputSchema)
2. Forwards tool calls to the gateway via HTTP
3. Returns the gateway's response (which includes `ai_context`)

All the real work happens in the gateway:
- Authentication (API keys, JWT)
- Approval workflows (intent queue)
- ERPNext integration (persistent httpx client)
- Malaysia statutory validation (EPF/SOCSO/PCB)
- Audit trail
- Event bus

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `GATEWAY_URL` | `http://127.0.0.1:8000` | Gateway base URL |
| `GATEWAY_API_KEY` | (empty) | API key for agent auth |
| `GATEWAY_VERSION` | `v1` | API version prefix |

## Project Structure

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server entry point (FastMCP)
│   ├── config.py          # Settings (env vars, gateway URL)
│   ├── gateway.py         # Thin HTTP client for gateway API
│   └── tools/
│       ├── __init__.py
│       ├── documents.py   # Generic DocType CRUD tools
│       ├── accounting.py  # Invoice, payment, reports
│       ├── hr.py          # Employee, payroll, leave, expenses
│       └── approvals.py   # Intent queue management
├── tests/
│   └── test_gateway.py    # Gateway client tests (mocked HTTP)
├── pyproject.toml
├── .env.example
└── README.md
```

## License

MIT
