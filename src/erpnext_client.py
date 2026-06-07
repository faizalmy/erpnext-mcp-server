"""Direct ERPNext REST API client.

This module is the ONLY place that talks to ERPNext.
All tool modules call erpnext.* functions — they never touch httpx directly.

Supports two auth modes:
1. Token auth (api_key:api_secret) — production
2. Password auth (usr/pwd session cookie) — development
"""

import json
import httpx

from .config import settings


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
            headers=settings.auth_header,
            timeout=settings.timeout,
            follow_redirects=True,
        )
        self._logged_in = False

    def close(self):
        self._client.close()

    def _login(self):
        """Password-based login (dev only). Creates session cookie."""
        if self._logged_in:
            return
        r = self._client.post(
            f"{settings.erpnext_url}/api/method/login",
            json={"usr": settings.erpnext_usr, "pwd": settings.erpnext_pwd},
        )
        self._logged_in = r.json().get("message") == "Logged In"

    # ═══════════════════════════════════════════════════════════
    # RESOURCE API (CRUD on any DocType)
    # Docs: https://docs.frappe.io/framework/user/en/api/rest
    # ═══════════════════════════════════════════════════════════

    def list_documents(self, doctype: str, fields: list[str] | None = None,
                       filters: list | None = None, limit: int = 20,
                       offset: int = 0, order_by: str = "") -> dict:
        """List documents of a DocType.

        GET /api/resource/{doctype}?fields=[...]&filters=[...]&limit_page_length=N
        """
        params: dict = {"limit_page_length": limit, "limit_start": offset}
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)
        if order_by:
            params["order_by"] = order_by
        r = self._client.get(f"{settings.api_base}/{doctype}", params=params)
        r.raise_for_status()
        data = r.json()
        return {"data": data.get("data", []), "count": len(data.get("data", []))}

    def get_document(self, doctype: str, name: str) -> dict:
        """Get a single document by name.

        GET /api/resource/{doctype}/{name}
        """
        r = self._client.get(f"{settings.api_base}/{doctype}/{name}")
        r.raise_for_status()
        return r.json().get("data", {})

    def create_document(self, doctype: str, data: dict) -> dict:
        """Create a new document.

        POST /api/resource/{doctype}
        """
        r = self._client.post(f"{settings.api_base}/{doctype}", json=data)
        r.raise_for_status()
        return r.json().get("data", {})

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        """Update an existing document (partial update).

        PUT /api/resource/{doctype}/{name}
        """
        r = self._client.put(f"{settings.api_base}/{doctype}/{name}", json=data)
        r.raise_for_status()
        return r.json().get("data", {})

    def delete_document(self, doctype: str, name: str) -> dict:
        """Delete a document.

        DELETE /api/resource/{doctype}/{name}
        """
        r = self._client.delete(f"{settings.api_base}/{doctype}/{name}")
        r.raise_for_status()
        return {"message": "ok"}

    def submit_document(self, doctype: str, name: str) -> dict:
        """Submit a draft document (finalize it).

        Uses the Frappe method API: /api/method/frappe.client.submit
        """
        r = self._client.post(
            f"{settings.method_base}/frappe.client.submit",
            json={"doctype": doctype, "name": name},
        )
        r.raise_for_status()
        return r.json().get("message", {})

    def cancel_document(self, doctype: str, name: str) -> dict:
        """Cancel a submitted document.

        Uses the Frappe method API: /api/method/frappe.client.cancel
        """
        r = self._client.post(
            f"{settings.method_base}/frappe.client.cancel",
            json={"doctype": doctype, "name": name},
        )
        r.raise_for_status()
        return r.json().get("message", {})

    # ═══════════════════════════════════════════════════════════
    # METHOD API (whitelisted Python functions)
    # Docs: https://docs.frappe.io/framework/user/en/guides/integration/rest_api
    # ═══════════════════════════════════════════════════════════

    def call_method(self, method: str, **kwargs) -> dict:
        """Call any whitelisted ERPNext/Frappe method.

        GET/POST /api/method/{dotted.path}

        Args:
            method: Dotted path (e.g. 'erpnext.stock.utils.get_stock_balance')
            kwargs: Method parameters
        """
        if kwargs:
            r = self._client.post(f"{settings.method_base}/{method}", json=kwargs)
        else:
            r = self._client.get(f"{settings.method_base}/{method}")
        r.raise_for_status()
        return r.json().get("message", r.json())

    # ═══════════════════════════════════════════════════════════
    # CONVENIENCE METHODS (common ERPNext workflows)
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


# Singleton
erpnext = ERPNextClient()
