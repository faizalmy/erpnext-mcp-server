"""Direct ERPNext REST API client.

This module is the ONLY place that talks to ERPNext.
All tool modules call erpnext.* functions — they never touch httpx directly.

Supports two auth modes:
1. Token auth (api_key:api_secret) — production
2. Password auth (usr/pwd session cookie) — development

Multi-tenant: supports per-request credential overrides via contextvars.
When _ctx_api_key/_ctx_api_secret are set (from HTTP headers), a per-request
httpx client is used instead of the shared singleton.
"""

import contextvars
import json
import httpx

from .config import settings

# Per-request context overrides (set by HTTP dispatch from headers)
_ctx_erpnext_url: contextvars.ContextVar[str | None] = contextvars.ContextVar("erpnext_url", default=None)
_ctx_api_key: contextvars.ContextVar[str | None] = contextvars.ContextVar("erpnext_api_key", default=None)
_ctx_api_secret: contextvars.ContextVar[str | None] = contextvars.ContextVar("erpnext_api_secret", default=None)


def set_request_context(url: str | None = None, api_key: str | None = None, api_secret: str | None = None) -> None:
    """Set per-request ERPNext context (URL + credentials, called from HTTP dispatch)."""
    if url is not None:
        _ctx_erpnext_url.set(url)
    if api_key is not None:
        _ctx_api_key.set(api_key)
    if api_secret is not None:
        _ctx_api_secret.set(api_secret)


def set_request_credentials(api_key: str | None, api_secret: str | None) -> None:
    """Alias for backward compat — delegates to set_request_context."""
    set_request_context(api_key=api_key, api_secret=api_secret)


def get_request_url() -> str | None:
    """Get the per-request ERPNext URL (used by discovery for cache keying)."""
    return _ctx_erpnext_url.get()


def _get_auth_header() -> dict[str, str]:
    """Get auth header from per-request context (empty if not set)."""
    api_key = _ctx_api_key.get()
    api_secret = _ctx_api_secret.get()
    if api_key and api_secret:
        return {"Authorization": f"token {api_key}:{api_secret}"}
    return {}


class ERPNextClient:
    """Thin HTTP adapter for ERPNext REST API.

    No business logic here. Just:
    - Build URLs (Frappe resource API + method API)
    - Set headers (auth)
    - Forward request
    - Return JSON

    Reference: https://docs.frappe.io/framework/user/en/api/rest
    """

    def __init__(self):
        self._client = httpx.Client(
            timeout=settings.timeout,
            follow_redirects=True,
        )

    def close(self):
        self._client.close()

    def _request(self, method: str, url_path: str, **kwargs) -> httpx.Response:
        """Make a request using contextvar URL + relative path."""
        base_url = _ctx_erpnext_url.get()
        if not base_url:
            raise RuntimeError(
                "No ERPNext URL set for this request — tenant not configured. "
                "Call set_request_context(url=...) before making requests."
            )
        full_url = f"{base_url}{url_path}"
        auth_header = _get_auth_header()
        headers = kwargs.pop("headers", {})
        headers.update(auth_header)
        kwargs["headers"] = headers
        return self._client.request(method, full_url, **kwargs)

    # ═══════════════════════════════════════════════════════════
    # RESOURCE API (CRUD on any DocType)
    # Docs: https://docs.frappe.io/framework/user/en/api/rest
    # ═══════════════════════════════════════════════════════════

    def list_documents(self, doctype: str, fields: list[str] | None = None,
                       filters: list | None = None, limit: int = 20,
                       offset: int = 0, order_by: str = "") -> dict:
        """List documents of a DocType."""
        params: dict = {"limit_page_length": limit, "limit_start": offset}
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)
        if order_by:
            params["order_by"] = order_by
        r = self._request("GET", f"/api/resource/{doctype}", params=params)
        r.raise_for_status()
        data = r.json()
        return {"data": data.get("data", []), "count": len(data.get("data", []))}

    def get_document(self, doctype: str, name: str) -> dict:
        """Get a single document by name."""
        r = self._request("GET", f"/api/resource/{doctype}/{name}")
        r.raise_for_status()
        return r.json().get("data", {})

    def create_document(self, doctype: str, data: dict) -> dict:
        """Create a new document."""
        r = self._request("POST", f"/api/resource/{doctype}", json=data)
        r.raise_for_status()
        return r.json().get("data", {})

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        """Update an existing document (partial update)."""
        r = self._request("PUT", f"/api/resource/{doctype}/{name}", json=data)
        r.raise_for_status()
        return r.json().get("data", {})

    def delete_document(self, doctype: str, name: str) -> dict:
        """Delete a submitted document."""
        r = self._request("DELETE", f"/api/resource/{doctype}/{name}")
        r.raise_for_status()
        return {"message": "ok"}

    def submit_document(self, doctype: str, name: str) -> dict:
        """Submit a draft document (finalize it)."""
        r = self._request(
            "POST",
            "/api/method/frappe.client.submit",
            json={"doctype": doctype, "name": name},
        )
        r.raise_for_status()
        return r.json().get("message", {})

    def cancel_document(self, doctype: str, name: str) -> dict:
        """Cancel a submitted document."""
        r = self._request(
            "POST",
            "/api/method/frappe.client.cancel",
            json={"doctype": doctype, "name": name},
        )
        r.raise_for_status()
        return r.json().get("message", {})

    # ═══════════════════════════════════════════════════════════
    # METHOD API (whitelisted Python functions)
    # ═══════════════════════════════════════════════════════════

    def call_method(self, method: str, **kwargs) -> dict:
        """Call any whitelisted ERPNext/Frappe method."""
        if kwargs:
            r = self._request("POST", f"/api/method/{method}", json=kwargs)
        else:
            r = self._request("GET", f"/api/method/{method}")
        r.raise_for_status()
        return r.json().get("message", r.json())

    # ═══════════════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════════════

    # ── Accounting ────────────────────────────────────────

    def get_balance_on(self, account: str, date: str = "", company: str = "") -> dict:
        kwargs = {"account": account}
        if date:
            kwargs["date"] = date
        if company:
            kwargs["company"] = company
        return self.call_method("erpnext.accounts.utils.get_balance_on", **kwargs)

    def get_exchange_rate(self, from_currency: str, to_currency: str, date: str = "") -> dict:
        kwargs = {"from_currency": from_currency, "to_currency": to_currency}
        if date:
            kwargs["date"] = date
        return self.call_method("erpnext.accounts.utils.get_exchange_rate", **kwargs)

    def get_fiscal_year(self, date: str = "", company: str = "") -> dict:
        kwargs = {}
        if date:
            kwargs["date"] = date
        if company:
            kwargs["company"] = company
        return self.call_method("erpnext.accounts.utils.get_fiscal_year", **kwargs)

    def make_sales_return(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
            source_name=source_name,
        )

    def get_payment_entry(self, dt: str, dn: str) -> dict:
        return self.call_method(
            "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
            dt=dt, dn=dn,
        )

    # ── Selling ───────────────────────────────────────────

    def make_sales_order_from_quotation(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.quotation.quotation.make_sales_order",
            source_name=source_name,
        )

    def make_sales_invoice_from_sales_order(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
            source_name=source_name,
        )

    def make_delivery_note_from_sales_order(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
            source_name=source_name,
        )

    def make_quotation_from_opportunity(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.crm.doctype.opportunity.opportunity.make_quotation",
            source_name=source_name,
        )

    def make_opportunity_from_lead(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.crm.doctype.lead.lead.make_opportunity",
            source_name=source_name,
        )

    def make_customer_from_lead(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.crm.doctype.lead.lead.make_customer",
            source_name=source_name,
        )

    # ── Buying ────────────────────────────────────────────

    def make_purchase_receipt_from_po(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
            source_name=source_name,
        )

    def make_purchase_invoice_from_po(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice",
            source_name=source_name,
        )

    def make_purchase_invoice_from_pr(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
            source_name=source_name,
        )

    def make_purchase_return(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_receipt.purchase_receipt.make_purchase_return",
            source_name=source_name,
        )

    def make_purchase_order_from_mr(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.material_request.material_request.make_purchase_order",
            source_name=source_name,
        )

    def make_supplier_quotation_from_mr(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.material_request.material_request.make_supplier_quotation",
            source_name=source_name,
        )

    # ── Stock ─────────────────────────────────────────────

    def get_item_details(self, item_code: str, company: str = "",
                         warehouse: str = "") -> dict:
        kwargs: dict = {"item_code": item_code}
        if company:
            kwargs["company"] = company
        if warehouse:
            kwargs["warehouse"] = warehouse
        return self.call_method(
            "erpnext.stock.doctype.item.item.get_item_details", **kwargs,
        )

    def get_stock_balance(self, item_code: str, warehouse: str = "",
                          posting_date: str = "") -> dict:
        kwargs: dict = {"item_code": item_code}
        if warehouse:
            kwargs["warehouse"] = warehouse
        if posting_date:
            kwargs["posting_date"] = posting_date
        return self.call_method("erpnext.stock.utils.get_stock_balance", **kwargs)

    def get_batch_qty(self, batch_no: str, warehouse: str = "") -> dict:
        kwargs: dict = {"batch_no": batch_no}
        if warehouse:
            kwargs["warehouse"] = warehouse
        return self.call_method(
            "erpnext.stock.doctype.batch.batch.get_batch_qty", **kwargs,
        )

    def make_stock_entry(self, **kwargs) -> dict:
        return self.call_method(
            "erpnext.stock.doctype.stock_entry.stock_entry.make_stock_entry", **kwargs,
        )

    def make_sales_invoice_from_dn(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
            source_name=source_name,
        )

    def make_sales_return_from_dn(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return",
            source_name=source_name,
        )

    def get_stock_ledger_entries(self, item_code: str, warehouse: str = "",
                                 posting_date_from: str = "",
                                 posting_date_to: str = "") -> dict:
        kwargs: dict = {"item_code": item_code}
        if warehouse:
            kwargs["warehouse"] = warehouse
        if posting_date_from:
            kwargs["posting_date_from"] = posting_date_from
        if posting_date_to:
            kwargs["posting_date_to"] = posting_date_to
        return self.call_method(
            "erpnext.stock.stock_ledger.get_stock_ledger_entries", **kwargs,
        )

    # ── HR ────────────────────────────────────────────────

    def get_leave_balance_on(self, employee: str, leave_type: str,
                             date: str = "") -> dict:
        kwargs: dict = {"employee": employee, "leave_type": leave_type}
        if date:
            kwargs["date"] = date
        return self.call_method(
            "erpnext.hr.doctype.leave_application.leave_application.get_leave_balance_on",
            **kwargs,
        )

    def get_leave_days(self, employee: str, leave_type: str,
                       from_date: str, to_date: str) -> dict:
        return self.call_method(
            "erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days",
            employee=employee, leave_type=leave_type,
            from_date=from_date, to_date=to_date,
        )

    # ── Manufacturing ─────────────────────────────────────

    def get_bom_items(self, bom: str, company: str = "", qty: float = 0) -> dict:
        kwargs: dict = {"bom": bom}
        if company:
            kwargs["company"] = company
        if qty:
            kwargs["qty"] = qty
        return self.call_method(
            "erpnext.manufacturing.doctype.bom.bom.get_bom_items", **kwargs,
        )

    def get_exploded_items(self, bom: str, qty: float = 0) -> dict:
        kwargs: dict = {"bom": bom}
        if qty:
            kwargs["qty"] = qty
        return self.call_method(
            "erpnext.manufacturing.doctype.bom.bom.get_exploded_items", **kwargs,
        )

    # ── Projects ──────────────────────────────────────────

    def make_sales_invoice_from_timesheet(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.projects.doctype.timesheet.timesheet.make_sales_invoice",
            source_name=source_name,
        )

    # ── Assets ────────────────────────────────────────────

    def make_asset_sales_invoice(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.make_sales_invoice",
            source_name=source_name,
        )

    def scrap_asset(self, asset_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.scrap_asset",
            asset_name=asset_name,
        )

    def restore_asset(self, asset_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.restore_asset",
            asset_name=asset_name,
        )

    def make_asset_movement(self, source_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.make_asset_movement",
            source_name=source_name,
        )


# Singleton — stateless httpx wrapper, per-request context is in contextvars
erpnext = ERPNextClient()
