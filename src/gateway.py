"""Thin HTTP client for the AI-ERP Gateway.

This module is the ONLY place that talks to the gateway.
All tool modules call gateway.* functions — they never touch httpx directly.

Design: synchronous httpx.Client because FastMCP tool functions are sync
and the gateway is on localhost (sub-millisecond latency).
"""

import json
import httpx

from .config import settings


class GatewayClient:
    """Thin HTTP adapter for the AI-ERP Gateway REST API.

    Two types of calls:
    1. Resource API — generic CRUD on any DocType
    2. Method API — whitelisted Python functions (business logic)
    """

    def __init__(self):
        self._client = httpx.Client(
            base_url=settings.api_base,
            headers=settings.headers,
            timeout=30,
        )

    def close(self):
        self._client.close()

    # ═══════════════════════════════════════════════════════════
    # GENERIC RESOURCE API (CRUD on any DocType)
    # ═══════════════════════════════════════════════════════════

    def list_documents(self, doctype: str, fields: list[str] | None = None,
                       filters: list | None = None, limit: int = 20,
                       offset: int = 0, order_by: str = "") -> dict:
        params: dict = {"limit_page_length": limit, "limit_start": offset}
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)
        if order_by:
            params["order_by"] = order_by
        r = self._client.get(f"/documents/{doctype}", params=params)
        r.raise_for_status()
        return r.json()

    def get_document(self, doctype: str, name: str) -> dict:
        r = self._client.get(f"/documents/{doctype}/{name}")
        r.raise_for_status()
        return r.json()

    def create_document(self, doctype: str, data: dict) -> dict:
        r = self._client.post(f"/documents/{doctype}", json=data)
        r.raise_for_status()
        return r.json()

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        r = self._client.put(f"/documents/{doctype}/{name}", json=data)
        r.raise_for_status()
        return r.json()

    def delete_document(self, doctype: str, name: str) -> dict:
        r = self._client.delete(f"/documents/{doctype}/{name}")
        r.raise_for_status()
        return r.json()

    def submit_document(self, doctype: str, name: str) -> dict:
        r = self._client.post(f"/documents/{doctype}/{name}/submit")
        r.raise_for_status()
        return r.json()

    def cancel_document(self, doctype: str, name: str) -> dict:
        r = self._client.post(f"/documents/{doctype}/{name}/cancel")
        r.raise_for_status()
        return r.json()

    # ═══════════════════════════════════════════════════════════
    # GENERIC METHOD CALLER (whitelisted Python functions)
    # ═══════════════════════════════════════════════════════════

    from typing import Any

    def call_method(self, method: str, **kwargs: Any) -> dict:
        """Call any whitelisted ERPNext method.

        Args:
            method: Dotted path (e.g. 'erpnext.selling.doctype.customer.customer.create_quotation')
            kwargs: Method parameters
        """
        r = self._client.post(f"/methods/{method}", json=kwargs)
        r.raise_for_status()
        return r.json()

    # ═══════════════════════════════════════════════════════════
    # ACCOUNTING
    # ═══════════════════════════════════════════════════════════

    def create_sales_invoice(self, customer: str, items: list[dict],
                             due_date: str = "", company: str = "") -> dict:
        body = {"customer": customer, "items": items}
        if due_date:
            body["due_date"] = due_date
        if company:
            body["company"] = company
        r = self._client.post("/accounting/invoices", json=body)
        r.raise_for_status()
        return r.json()

    def create_purchase_invoice(self, supplier: str, items: list[dict],
                                due_date: str = "", company: str = "") -> dict:
        body = {"supplier": supplier, "items": items}
        if due_date:
            body["due_date"] = due_date
        if company:
            body["company"] = company
        r = self._client.post("/accounting/purchase-invoices", json=body)
        r.raise_for_status()
        return r.json()

    def record_payment(self, party: str, amount: float,
                       payment_type: str = "Receive",
                       reference: str = "", party_type: str = "Customer") -> dict:
        body = {"party": party, "amount": amount, "payment_type": payment_type, "party_type": party_type}
        if reference:
            body["reference"] = reference
        r = self._client.post("/accounting/payments", json=body)
        r.raise_for_status()
        return r.json()

    def get_trial_balance(self, company: str = "", from_date: str = "", to_date: str = "") -> dict:
        params = {k: v for k, v in {"company": company, "from_date": from_date, "to_date": to_date}.items() if v}
        r = self._client.get("/accounting/trial-balance", params=params)
        r.raise_for_status()
        return r.json()

    def get_profit_and_loss(self, company: str = "", from_date: str = "", to_date: str = "") -> dict:
        params = {k: v for k, v in {"company": company, "from_date": from_date, "to_date": to_date}.items() if v}
        r = self._client.get("/accounting/profit-and-loss", params=params)
        r.raise_for_status()
        return r.json()

    def get_balance_sheet(self, company: str = "", from_date: str = "", to_date: str = "") -> dict:
        params = {k: v for k, v in {"company": company, "from_date": from_date, "to_date": to_date}.items() if v}
        r = self._client.get("/accounting/balance-sheet", params=params)
        r.raise_for_status()
        return r.json()

    def make_sales_return(self, against_sales_invoice: str) -> dict:
        return self.call_method(
            "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
            source_name=against_sales_invoice,
        )

    def get_payment_entry(self, dt: str, dn: str) -> dict:
        return self.call_method(
            "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
            dt=dt, dn=dn,
        )

    def get_reference_details(self, reference_doctype: str, reference_name: str, party_account: str) -> dict:
        return self.call_method(
            "erpnext.accounts.doctype.payment_entry.payment_entry.get_reference_details",
            reference_doctype=reference_doctype, reference_name=reference_name, party_account=party_account,
        )

    # ═══════════════════════════════════════════════════════════
    # SELLING
    # ═══════════════════════════════════════════════════════════

    def make_quotation_from_opportunity(self, opportunity_name: str) -> dict:
        return self.call_method(
            "erpnext.crm.doctype.opportunity.opportunity.make_quotation",
            source_name=opportunity_name,
        )

    def make_sales_order_from_quotation(self, quotation_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.quotation.quotation.make_sales_order",
            source_name=quotation_name,
        )

    def make_sales_invoice_from_sales_order(self, sales_order_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
            source_name=sales_order_name,
        )

    def make_delivery_note_from_sales_order(self, sales_order_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
            source_name=sales_order_name,
        )

    def make_quotation_from_customer(self, customer_name: str) -> dict:
        return self.call_method(
            "erpnext.selling.doctype.customer.customer.create_quotation",
            customer_name=customer_name,
        )

    def make_opportunity_from_lead(self, lead_name: str) -> dict:
        return self.call_method(
            "erpnext.crm.doctype.lead.lead.make_opportunity",
            source_name=lead_name,
        )

    def make_customer_from_lead(self, lead_name: str) -> dict:
        return self.call_method(
            "erpnext.crm.doctype.lead.lead.make_customer",
            source_name=lead_name,
        )

    # ═══════════════════════════════════════════════════════════
    # BUYING
    # ═══════════════════════════════════════════════════════════

    def make_purchase_receipt_from_po(self, purchase_order_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
            source_name=purchase_order_name,
        )

    def make_purchase_invoice_from_po(self, purchase_order_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice",
            source_name=purchase_order_name,
        )

    def make_purchase_invoice_from_pr(self, purchase_receipt_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
            source_name=purchase_receipt_name,
        )

    def make_purchase_return(self, purchase_receipt_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.purchase_receipt.purchase_receipt.make_purchase_return",
            source_name=purchase_receipt_name,
        )

    def make_purchase_order_from_mr(self, material_request_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.material_request.material_request.make_purchase_order",
            source_name=material_request_name,
        )

    def make_supplier_quotation_from_mr(self, material_request_name: str) -> dict:
        return self.call_method(
            "erpnext.buying.doctype.material_request.material_request.make_supplier_quotation",
            source_name=material_request_name,
        )

    # ═══════════════════════════════════════════════════════════
    # STOCK
    # ═══════════════════════════════════════════════════════════

    def make_stock_entry(self, work_order: str = "", item_code: str = "",
                         qty: float = 0, from_warehouse: str = "",
                         to_warehouse: str = "", purpose: str = "") -> dict:
        kwargs = {}
        if work_order:
            kwargs["work_order"] = work_order
        if item_code:
            kwargs["item_code"] = item_code
        if qty:
            kwargs["qty"] = qty
        if from_warehouse:
            kwargs["from_warehouse"] = from_warehouse
        if to_warehouse:
            kwargs["to_warehouse"] = to_warehouse
        if purpose:
            kwargs["purpose"] = purpose
        return self.call_method(
            "erpnext.stock.doctype.stock_entry.stock_entry.make_stock_entry",
            **kwargs,
        )

    def get_item_details(self, item_code: str, company: str = "",
                         warehouse: str = "") -> dict:
        kwargs = {"item_code": item_code}
        if company:
            kwargs["company"] = company
        if warehouse:
            kwargs["warehouse"] = warehouse
        return self.call_method(
            "erpnext.stock.doctype.item.item.get_item_details",
            **kwargs,
        )

    def make_sales_invoice_from_dn(self, delivery_note_name: str) -> dict:
        return self.call_method(
            "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
            source_name=delivery_note_name,
        )

    def make_sales_return_from_dn(self, delivery_note_name: str) -> dict:
        return self.call_method(
            "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return",
            source_name=delivery_note_name,
        )

    def get_stock_balance(self, item_code: str, warehouse: str = "",
                          posting_date: str = "", posting_time: str = "") -> dict:
        kwargs = {"item_code": item_code}
        if warehouse:
            kwargs["warehouse"] = warehouse
        if posting_date:
            kwargs["posting_date"] = posting_date
        if posting_time:
            kwargs["posting_time"] = posting_time
        return self.call_method(
            "erpnext.stock.utils.get_stock_balance",
            **kwargs,
        )

    def get_batch_qty(self, batch_no: str, warehouse: str = "") -> dict:
        kwargs = {"batch_no": batch_no}
        if warehouse:
            kwargs["warehouse"] = warehouse
        return self.call_method(
            "erpnext.stock.doctype.batch.batch.get_batch_qty",
            **kwargs,
        )

    def get_stock_ledger_entries(self, item_code: str, warehouse: str = "",
                                 posting_date_from: str = "",
                                 posting_date_to: str = "") -> dict:
        kwargs = {"item_code": item_code}
        if warehouse:
            kwargs["warehouse"] = warehouse
        if posting_date_from:
            kwargs["posting_date_from"] = posting_date_from
        if posting_date_to:
            kwargs["posting_date_to"] = posting_date_to
        return self.call_method(
            "erpnext.stock.stock_ledger.get_stock_ledger_entries",
            **kwargs,
        )

    # ═══════════════════════════════════════════════════════════
    # HR & PAYROLL
    # ═══════════════════════════════════════════════════════════

    def create_employee(self, data: dict) -> dict:
        r = self._client.post("/hr/employees", json=data)
        r.raise_for_status()
        return r.json()

    def run_payroll(self, company: str, month: str, year: int) -> dict:
        r = self._client.post("/hr/payroll/run", json={"company": company, "month": month, "year": year})
        r.raise_for_status()
        return r.json()

    def get_leave_balance(self, employee: str) -> dict:
        r = self._client.get(f"/hr/leave/{employee}")
        r.raise_for_status()
        return r.json()

    def submit_expense(self, employee: str, expenses: list[dict]) -> dict:
        r = self._client.post("/hr/expenses", json={"employee": employee, "expenses": expenses})
        r.raise_for_status()
        return r.json()

    def get_leave_balance_on(self, employee: str, leave_type: str,
                             date: str = "") -> dict:
        kwargs = {"employee": employee, "leave_type": leave_type, "date": date}
        return self.call_method(
            "erpnext.hr.doctype.leave_application.leave_application.get_leave_balance_on",
            **{k: v for k, v in kwargs.items() if v},
        )

    def get_leave_days(self, employee: str, leave_type: str,
                       from_date: str, to_date: str,
                       half_day: int = 0, half_day_date: str = "") -> dict:
        kwargs = {
            "employee": employee, "leave_type": leave_type,
            "from_date": from_date, "to_date": to_date,
        }
        if half_day:
            kwargs["half_day"] = half_day
        if half_day_date:
            kwargs["half_day_date"] = half_day_date
        return self.call_method(
            "erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days",
            **kwargs,
        )

    def make_expense_bank_entry(self, expense_claim_name: str) -> dict:
        return self.call_method(
            "erpnext.hr.doctype.expense_claim.expense_claim.make_bank_entry",
            source_name=expense_claim_name,
        )

    def create_salary_slips(self, payroll_entry_name: str) -> dict:
        return self.call_method(
            "erpnext.hr.doctype.payroll_entry.payroll_entry.create_salary_slips",
            payroll_entry=payroll_entry_name,
        )

    def submit_salary_slips(self, payroll_entry_name: str) -> dict:
        return self.call_method(
            "erpnext.hr.doctype.payroll_entry.payroll_entry.submit_salary_slips",
            payroll_entry=payroll_entry_name,
        )

    def make_payroll_bank_entry(self, payroll_entry_name: str) -> dict:
        return self.call_method(
            "erpnext.hr.doctype.payroll_entry.payroll_entry.make_bank_entry",
            payroll_entry=payroll_entry_name,
        )

    # ═══════════════════════════════════════════════════════════
    # MANUFACTURING
    # ═══════════════════════════════════════════════════════════

    def make_stock_entry_from_wo(self, work_order_name: str) -> dict:
        return self.call_method(
            "erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry",
            source_name=work_order_name,
        )

    def make_job_card_from_wo(self, work_order_name: str) -> dict:
        return self.call_method(
            "erpnext.manufacturing.doctype.work_order.work_order.make_job_card",
            source_name=work_order_name,
        )

    def get_bom_items(self, bom: str, company: str = "", qty: float = 0) -> dict:
        kwargs = {"bom": bom}
        if company:
            kwargs["company"] = company
        if qty:
            kwargs["qty"] = qty
        return self.call_method(
            "erpnext.manufacturing.doctype.bom.bom.get_bom_items",
            **kwargs,
        )

    def get_bom_item_rate(self, bom: str, item_code: str) -> dict:
        return self.call_method(
            "erpnext.manufacturing.doctype.bom.bom.get_bom_item_rate",
            bom=bom, item_code=item_code,
        )

    def get_exploded_items(self, bom: str, qty: float = 0) -> dict:
        kwargs = {"bom": bom}
        if qty:
            kwargs["qty"] = qty
        return self.call_method(
            "erpnext.manufacturing.doctype.bom.bom.get_exploded_items",
            **kwargs,
        )

    def get_material_request_items(self, production_plan_name: str) -> dict:
        return self.call_method(
            "erpnext.manufacturing.doctype.production_plan.production_plan.get_items_for_material_requests",
            production_plan=production_plan_name,
        )

    def make_material_request_from_pp(self, production_plan_name: str) -> dict:
        return self.call_method(
            "erpnext.manufacturing.doctype.production_plan.production_plan.make_material_request",
            production_plan=production_plan_name,
        )

    def make_work_order_from_pp(self, production_plan_name: str) -> dict:
        return self.call_method(
            "erpnext.manufacturing.doctype.production_plan.production_plan.make_work_order",
            production_plan=production_plan_name,
        )

    # ═══════════════════════════════════════════════════════════
    # PROJECTS
    # ═══════════════════════════════════════════════════════════

    def make_sales_invoice_from_timesheet(self, timesheet_name: str) -> dict:
        return self.call_method(
            "erpnext.projects.doctype.timesheet.timesheet.make_sales_invoice",
            source_name=timesheet_name,
        )

    def make_salary_slip_from_timesheet(self, timesheet_name: str) -> dict:
        return self.call_method(
            "erpnext.projects.doctype.timesheet.timesheet.make_salary_slip",
            source_name=timesheet_name,
        )

    def get_project_users(self, project_name: str) -> dict:
        return self.call_method(
            "erpnext.projects.doctype.project.project.get_users",
            project=project_name,
        )

    def get_task_children(self, task_name: str) -> dict:
        return self.call_method(
            "erpnext.projects.doctype.task.task.get_children",
            task=task_name,
        )

    # ═══════════════════════════════════════════════════════════
    # ASSETS
    # ═══════════════════════════════════════════════════════════

    def make_asset_sales_invoice(self, asset_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.make_sales_invoice",
            source_name=asset_name,
        )

    def make_asset_purchase_invoice(self, asset_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.make_purchase_invoice",
            source_name=asset_name,
        )

    def make_asset_movement(self, asset_name: str) -> dict:
        return self.call_method(
            "erpnext.assets.doctype.asset.asset.make_asset_movement",
            source_name=asset_name,
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

    # ═══════════════════════════════════════════════════════════
    # APPROVALS & AUDIT
    # ═══════════════════════════════════════════════════════════

    def list_intents(self, status: str = "") -> dict:
        params = {"status": status} if status else {}
        r = self._client.get("/intents", params=params)
        r.raise_for_status()
        return r.json()

    def approve_intent(self, intent_id: str, reviewed_by: str = "human:faizal") -> dict:
        r = self._client.post(f"/intents/{intent_id}/approve", json={"reviewed_by": reviewed_by})
        r.raise_for_status()
        return r.json()

    def reject_intent(self, intent_id: str, reason: str = "",
                      reviewed_by: str = "human:faizal") -> dict:
        r = self._client.post(f"/intents/{intent_id}/reject", json={
            "reviewed_by": reviewed_by, "reason": reason
        })
        r.raise_for_status()
        return r.json()

    def get_audit_log(self, limit: int = 50) -> dict:
        r = self._client.get("/audit", params={"limit": limit})
        r.raise_for_status()
        return r.json()


# Singleton — one client, reused across all tool calls
gateway = GatewayClient()
