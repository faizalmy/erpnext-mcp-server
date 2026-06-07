"""Thin HTTP client for the AI-ERP Gateway.

This module is the ONLY place that talks to the gateway.
All tool modules call gateway.* functions — they never touch httpx directly.

Design: synchronous httpx.Client because FastMCP tool functions are sync
and the gateway is on localhost (sub-millisecond latency).
"""

import httpx

from .config import settings


class GatewayClient:
    """Thin HTTP adapter for the AI-ERP Gateway REST API.

    No business logic here. Just:
    - Build URLs
    - Set headers (auth)
    - Forward request
    - Return JSON
    """

    def __init__(self):
        self._client = httpx.Client(
            base_url=settings.api_base,
            headers=settings.headers,
            timeout=30,
        )

    def close(self):
        self._client.close()

    # ── Generic CRUD ──────────────────────────────────────────

    def list_documents(self, doctype: str, fields: list[str] | None = None,
                       filters: list | None = None, limit: int = 20,
                       offset: int = 0) -> dict:
        """List documents of a DocType."""
        import json
        params: dict = {"limit_page_length": limit, "limit_start": offset}
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)
        r = self._client.get(f"/documents/{doctype}", params=params)
        r.raise_for_status()
        return r.json()

    def get_document(self, doctype: str, name: str) -> dict:
        """Get a single document by name."""
        r = self._client.get(f"/documents/{doctype}/{name}")
        r.raise_for_status()
        return r.json()

    def create_document(self, doctype: str, data: dict) -> dict:
        """Create a document (goes through approval)."""
        r = self._client.post(f"/documents/{doctype}", json=data)
        r.raise_for_status()
        return r.json()

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        """Update a document (goes through approval)."""
        r = self._client.put(f"/documents/{doctype}/{name}", json=data)
        r.raise_for_status()
        return r.json()

    def submit_document(self, doctype: str, name: str) -> dict:
        """Submit a draft document (goes through approval)."""
        r = self._client.post(f"/documents/{doctype}/{name}/submit")
        r.raise_for_status()
        return r.json()

    # ── Accounting ────────────────────────────────────────────

    def create_invoice(self, customer: str, items: list[dict],
                       due_date: str = "", company: str = "") -> dict:
        """Create a sales invoice (goes through approval)."""
        body = {"customer": customer, "items": items}
        if due_date:
            body["due_date"] = due_date
        if company:
            body["company"] = company
        r = self._client.post("/accounting/invoices", json=body)
        r.raise_for_status()
        return r.json()

    def record_payment(self, party: str, amount: float,
                       payment_type: str = "Receive",
                       reference: str = "") -> dict:
        """Record a payment (goes through approval)."""
        body = {
            "party": party,
            "amount": amount,
            "payment_type": payment_type,
        }
        if reference:
            body["reference"] = reference
        r = self._client.post("/accounting/payments", json=body)
        r.raise_for_status()
        return r.json()

    def get_trial_balance(self, company: str = "",
                          from_date: str = "", to_date: str = "") -> dict:
        """Get trial balance report (read-only)."""
        params = {}
        if company:
            params["company"] = company
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        r = self._client.get("/accounting/trial-balance", params=params)
        r.raise_for_status()
        return r.json()

    def get_profit_and_loss(self, company: str = "",
                            from_date: str = "", to_date: str = "") -> dict:
        """Get P&L statement (read-only)."""
        params = {}
        if company:
            params["company"] = company
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        r = self._client.get("/accounting/profit-and-loss", params=params)
        r.raise_for_status()
        return r.json()

    def get_balance_sheet(self, company: str = "",
                          from_date: str = "", to_date: str = "") -> dict:
        """Get balance sheet (read-only)."""
        params = {}
        if company:
            params["company"] = company
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        r = self._client.get("/accounting/balance-sheet", params=params)
        r.raise_for_status()
        return r.json()

    # ── HR ────────────────────────────────────────────────────

    def create_employee(self, data: dict) -> dict:
        """Create an employee (goes through approval)."""
        r = self._client.post("/hr/employees", json=data)
        r.raise_for_status()
        return r.json()

    def run_payroll(self, company: str, month: str, year: int) -> dict:
        """Run payroll for a given month (goes through approval)."""
        r = self._client.post("/hr/payroll/run", json={
            "company": company, "month": month, "year": year
        })
        r.raise_for_status()
        return r.json()

    def get_leave_balance(self, employee: str) -> dict:
        """Get leave balance for an employee (read-only)."""
        r = self._client.get(f"/hr/leave/{employee}")
        r.raise_for_status()
        return r.json()

    def submit_expense(self, employee: str, expenses: list[dict]) -> dict:
        """Submit an expense claim (goes through approval)."""
        r = self._client.post("/hr/expenses", json={
            "employee": employee, "expenses": expenses
        })
        r.raise_for_status()
        return r.json()

    # ── Approvals ─────────────────────────────────────────────

    def list_intents(self, status: str = "") -> dict:
        """List intents, optionally filtered by status."""
        params = {"status": status} if status else {}
        r = self._client.get("/intents", params=params)
        r.raise_for_status()
        return r.json()

    def approve_intent(self, intent_id: str,
                       reviewed_by: str = "human:faizal") -> dict:
        """Approve a pending intent."""
        r = self._client.post(f"/intents/{intent_id}/approve", json={
            "reviewed_by": reviewed_by
        })
        r.raise_for_status()
        return r.json()

    def reject_intent(self, intent_id: str, reason: str = "",
                      reviewed_by: str = "human:faizal") -> dict:
        """Reject a pending intent."""
        r = self._client.post(f"/intents/{intent_id}/reject", json={
            "reviewed_by": reviewed_by, "reason": reason
        })
        r.raise_for_status()
        return r.json()

    # ── Audit ─────────────────────────────────────────────────

    def get_audit_log(self, limit: int = 50) -> dict:
        """Get the audit trail."""
        r = self._client.get("/audit", params={"limit": limit})
        r.raise_for_status()
        return r.json()


# Singleton — one client, reused across all tool calls
gateway = GatewayClient()
