"""Curated MCP tools — high-level ERPNext operations.

These tools call ERPNext's whitelisted methods for complex operations
that go beyond simple CRUD: document workflows, conversions, reports.

Auto-discovery handles the generic CRUD tools. These are the "smart" ones.
"""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext

TOOL_COUNT = 36


def register(mcp: FastMCP):
    """Register curated tools on the MCP server."""

    # ═══════════════════════════════════════════════════════════
    # GENERIC — flexible entry points
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def list_documents(
        doctype: str,
        fields: list[str] | None = None,
        filters: list | None = None,
        limit: int = 20,
    ) -> dict:
        """List documents of any ERPNext DocType with full filter support.

        Use this for flexible queries when the auto-generated list_* tools
        are too restrictive. Supports ERPNext filter syntax.

        Args:
            doctype: DocType name (e.g. 'Customer', 'Sales Invoice')
            fields: Fields to return. Example: ["name", "customer_name"]
            filters: ERPNext filters. Example: [["Customer", "territory", "=", "Malaysia"]]
            limit: Max records (default 20)
        """
        return erpnext.list_documents(doctype, fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_document(doctype: str, name: str) -> dict:
        """Get any ERPNext document by DocType and name.

        Use this when you need a specific document and know its exact DocType.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice')
            name: Document name/ID (e.g. 'SINV-00001')
        """
        return erpnext.get_document(doctype, name)

    @mcp.tool()
    def submit_document(doctype: str, name: str) -> dict:
        """Submit (finalize) a draft document.

        ERPNext has draft → submitted workflow for many DocTypes
        (Sales Invoice, Purchase Order, Stock Entry, etc.).
        Once submitted, the document cannot be edited — only cancelled.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice')
            name: Document name/ID to submit
        """
        return erpnext.submit_document(doctype, name)

    @mcp.tool()
    def cancel_document(doctype: str, name: str) -> dict:
        """Cancel a submitted document.

        Reverses the effects of submission. The document returns to draft state.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice')
            name: Document name/ID to cancel
        """
        return erpnext.cancel_document(doctype, name)

    # ═══════════════════════════════════════════════════════════
    # ACCOUNTING
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def get_account_balance(account: str, date: str = "", company: str = "") -> dict:
        """Get the current balance of a GL account.

        Returns the balance amount for a given account as of a date.
        Useful for cash flow analysis, reconciliation, and reporting.

        Args:
            account: Account name (e.g. 'Cash - ARC')
            date: As-of date (YYYY-MM-DD, default: today)
            company: Company name (optional)
        """
        return erpnext.get_balance_on(account, date=date, company=company)

    @mcp.tool()
    def get_exchange_rate(from_currency: str, to_currency: str,
                          date: str = "") -> dict:
        """Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code (e.g. 'USD')
            to_currency: Target currency code (e.g. 'MYR')
            date: Date for the rate (YYYY-MM-DD, default: today)
        """
        return erpnext.get_exchange_rate(from_currency, to_currency, date=date)

    @mcp.tool()
    def get_fiscal_year(date: str = "", company: str = "") -> dict:
        """Get the fiscal year for a given date.

        Args:
            date: Date to check (YYYY-MM-DD, default: today)
            company: Company name (optional)
        """
        return erpnext.get_fiscal_year(date=date, company=company)

    @mcp.tool()
    def create_payment_entry(doctype: str, name: str) -> dict:
        """Generate a Payment Entry from an invoice or order.

        Creates a draft payment entry linked to the source document.
        Review and submit the payment entry to record the payment.

        Args:
            doctype: Source DocType (e.g. 'Sales Invoice', 'Purchase Invoice')
            name: Source document name/ID
        """
        return erpnext.get_payment_entry(dt=doctype, dn=name)

    @mcp.tool()
    def create_sales_return(sales_invoice: str) -> dict:
        """Create a sales return (credit note) from a sales invoice.

        Generates a return invoice that reverses the original.
        Used for refunds, returns, and corrections.

        Args:
            sales_invoice: The Sales Invoice name/ID to create a return from
        """
        return erpnext.make_sales_return(source_name=sales_invoice)

    # ═══════════════════════════════════════════════════════════
    # SELLING — document conversions
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def convert_quotation_to_sales_order(quotation: str) -> dict:
        """Convert an accepted Quotation into a Sales Order.

        Creates a new Sales Order with items from the quotation.
        The quotation must be in 'Submitted' status.

        Args:
            quotation: Quotation name/ID (e.g. 'QTN-00001')
        """
        return erpnext.make_sales_order_from_quotation(source_name=quotation)

    @mcp.tool()
    def convert_sales_order_to_invoice(sales_order: str) -> dict:
        """Convert a Sales Order into a Sales Invoice.

        Creates an invoice from the order for billing.
        The sales order must be submitted.

        Args:
            sales_order: Sales Order name/ID (e.g. 'SAL-ORD-00001')
        """
        return erpnext.make_sales_invoice_from_sales_order(source_name=sales_order)

    @mcp.tool()
    def convert_sales_order_to_delivery(sales_order: str) -> dict:
        """Convert a Sales Order into a Delivery Note.

        Creates a delivery note for shipping/fulfillment.
        Used when goods are ready to ship.

        Args:
            sales_order: Sales Order name/ID (e.g. 'SAL-ORD-00001')
        """
        return erpnext.make_delivery_note_from_sales_order(source_name=sales_order)

    @mcp.tool()
    def convert_opportunity_to_quotation(opportunity: str) -> dict:
        """Convert an Opportunity into a Quotation.

        Creates a quotation from a sales opportunity.
        Used in the CRM pipeline: Lead → Opportunity → Quotation.

        Args:
            opportunity: Opportunity name/ID (e.g. 'CRM-OPP-00001')
        """
        return erpnext.make_quotation_from_opportunity(source_name=opportunity)

    @mcp.tool()
    def convert_lead_to_opportunity(lead: str) -> dict:
        """Convert a Lead into an Opportunity.

        First step in the sales pipeline when a lead shows interest.

        Args:
            lead: Lead name/ID (e.g. 'CRM-LEAD-00001')
        """
        return erpnext.make_opportunity_from_lead(source_name=lead)

    @mcp.tool()
    def convert_lead_to_customer(lead: str) -> dict:
        """Convert a Lead directly into a Customer.

        Skips the opportunity stage — use when the lead is ready to buy.

        Args:
            lead: Lead name/ID (e.g. 'CRM-LEAD-00001')
        """
        return erpnext.make_customer_from_lead(source_name=lead)

    # ═══════════════════════════════════════════════════════════
    # BUYING — document conversions
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def convert_po_to_receipt(purchase_order: str) -> dict:
        """Convert a Purchase Order into a Purchase Receipt.

        Creates a receipt when goods arrive from the supplier.
        Used for recording incoming inventory.

        Args:
            purchase_order: Purchase Order name/ID (e.g. 'PUR-ORD-00001')
        """
        return erpnext.make_purchase_receipt_from_po(source_name=purchase_order)

    @mcp.tool()
    def convert_po_to_invoice(purchase_order: str) -> dict:
        """Convert a Purchase Order into a Purchase Invoice.

        Creates an invoice for payment to the supplier.

        Args:
            purchase_order: Purchase Order name/ID (e.g. 'PUR-ORD-00001')
        """
        return erpnext.make_purchase_invoice_from_po(source_name=purchase_order)

    @mcp.tool()
    def convert_receipt_to_invoice(purchase_receipt: str) -> dict:
        """Convert a Purchase Receipt into a Purchase Invoice.

        Creates an invoice from a received goods receipt.

        Args:
            purchase_receipt: Purchase Receipt name/ID (e.g. 'PUR-REC-00001')
        """
        return erpnext.make_purchase_invoice_from_pr(source_name=purchase_receipt)

    @mcp.tool()
    def create_purchase_return(purchase_receipt: str) -> dict:
        """Create a purchase return from a purchase receipt.

        Returns goods to the supplier. Creates a debit note.

        Args:
            purchase_receipt: Purchase Receipt name/ID to return from
        """
        return erpnext.make_purchase_return(source_name=purchase_receipt)

    @mcp.tool()
    def convert_material_request_to_po(material_request: str) -> dict:
        """Convert a Material Request into a Purchase Order.

        Used in the procurement workflow: stock check → Material Request → PO.

        Args:
            material_request: Material Request name/ID (e.g. 'MAT-REQ-00001')
        """
        return erpnext.make_purchase_order_from_mr(source_name=material_request)

    # ═══════════════════════════════════════════════════════════
    # STOCK
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def get_item_details(item_code: str, company: str = "",
                         warehouse: str = "") -> dict:
        """Get full item details including pricing, stock, and defaults.

        Returns item master data with pricing rules, tax templates,
        warehouse defaults, and current stock levels.

        Args:
            item_code: Item code (e.g. 'CONSULTING-HOURS')
            company: Company context (optional)
            warehouse: Warehouse context (optional)
        """
        return erpnext.get_item_details(item_code, company=company, warehouse=warehouse)

    @mcp.tool()
    def get_stock_balance(item_code: str, warehouse: str = "",
                          posting_date: str = "") -> dict:
        """Get current stock balance for an item.

        Returns the actual quantity in stock as of a date.

        Args:
            item_code: Item code (e.g. 'ITEM-001')
            warehouse: Warehouse name (optional, default: all warehouses)
            posting_date: As-of date (YYYY-MM-DD, default: today)
        """
        return erpnext.get_stock_balance(item_code, warehouse=warehouse,
                                         posting_date=posting_date)

    @mcp.tool()
    def get_batch_qty(batch_no: str, warehouse: str = "") -> dict:
        """Get quantity available in a specific batch.

        Args:
            batch_no: Batch number
            warehouse: Warehouse name (optional)
        """
        return erpnext.get_batch_qty(batch_no, warehouse=warehouse)

    @mcp.tool()
    def create_stock_entry(**kwargs) -> dict:
        """Create a Stock Entry for inventory movements.

        Used for material transfers, manufacturing, repacking, etc.

        Args:
            **kwargs: Stock Entry fields (stock_entry_type, items, etc.)
        """
        return erpnext.make_stock_entry(**kwargs)

    @mcp.tool()
    def convert_delivery_to_invoice(delivery_note: str) -> dict:
        """Convert a Delivery Note into a Sales Invoice.

        Creates an invoice after goods have been delivered.

        Args:
            delivery_note: Delivery Note name/ID (e.g. 'DEL-00001')
        """
        return erpnext.make_sales_invoice_from_dn(source_name=delivery_note)

    @mcp.tool()
    def create_return_from_delivery(delivery_note: str) -> dict:
        """Create a sales return from a Delivery Note.

        Used when delivered goods are returned by the customer.

        Args:
            delivery_note: Delivery Note name/ID to create a return from
        """
        return erpnext.make_sales_return_from_dn(source_name=delivery_note)

    @mcp.tool()
    def get_stock_ledger_entries(item_code: str, warehouse: str = "",
                                 from_date: str = "", to_date: str = "") -> dict:
        """Get stock movement history for an item.

        Returns all stock transactions (in/out) with dates, quantities,
        and valuation. Useful for stock audit and analysis.

        Args:
            item_code: Item code
            warehouse: Warehouse name (optional)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        """
        return erpnext.get_stock_ledger_entries(
            item_code, warehouse=warehouse,
            posting_date_from=from_date, posting_date_to=to_date,
        )

    # ═══════════════════════════════════════════════════════════
    # HR
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def get_leave_balance(employee: str, leave_type: str,
                          date: str = "") -> dict:
        """Get leave balance for an employee.

        Returns remaining leave days for a specific leave type.

        Args:
            employee: Employee ID (e.g. 'HR-EMP-00001')
            leave_type: Leave type (e.g. 'Annual Leave', 'Sick Leave')
            date: As-of date (YYYY-MM-DD, default: today)
        """
        return erpnext.get_leave_balance_on(employee, leave_type, date=date)

    @mcp.tool()
    def calculate_leave_days(employee: str, leave_type: str,
                             from_date: str, to_date: str) -> dict:
        """Calculate number of leave days between two dates.

        Accounts for holidays and weekends.

        Args:
            employee: Employee ID
            leave_type: Leave type (e.g. 'Annual Leave')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
        """
        return erpnext.get_leave_days(employee, leave_type, from_date, to_date)

    # ═══════════════════════════════════════════════════════════
    # MANUFACTURING
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def get_bom_items(bom: str, company: str = "", qty: float = 0) -> dict:
        """Get raw materials list from a Bill of Materials.

        Returns all items needed to manufacture the BOM's product.

        Args:
            bom: BOM name/ID (e.g. 'BOM-ITEM-001')
            company: Company context (optional)
            qty: Quantity to produce (default: BOM quantity)
        """
        return erpnext.get_bom_items(bom, company=company, qty=qty)

    @mcp.tool()
    def get_exploded_bom_items(bom: str, qty: float = 0) -> dict:
        """Get all raw materials from a BOM including sub-assembly items.

        Unlike get_bom_items, this recursively expands nested BOMs
        to show the complete raw material list.

        Args:
            bom: BOM name/ID
            qty: Quantity to produce (default: BOM quantity)
        """
        return erpnext.get_exploded_items(bom, qty=qty)

    # ═══════════════════════════════════════════════════════════
    # PROJECTS
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def convert_timesheet_to_invoice(timesheet: str) -> dict:
        """Convert a Timesheet into a Sales Invoice.

        Bills the client for time worked. Creates an invoice with
        timesheet line items.

        Args:
            timesheet: Timesheet name/ID (e.g. 'TIM-00001')
        """
        return erpnext.make_sales_invoice_from_timesheet(source_name=timesheet)

    # ═══════════════════════════════════════════════════════════
    # ASSETS
    # ═══════════════════════════════════════════════════════════

    @mcp.tool()
    def create_asset_invoice(asset: str) -> dict:
        """Create a Sales Invoice for an asset sale.

        Generates an invoice when selling a fixed asset.

        Args:
            asset: Asset name/ID (e.g. 'AST-00001')
        """
        return erpnext.make_asset_sales_invoice(source_name=asset)

    @mcp.tool()
    def scrap_asset(asset_name: str) -> dict:
        """Scrap (dispose of) a fixed asset.

        Marks the asset as scrapped and removes it from the books.

        Args:
            asset_name: Asset name/ID to scrap
        """
        return erpnext.scrap_asset(asset_name)

    @mcp.tool()
    def restore_asset(asset_name: str) -> dict:
        """Restore a scrapped asset back to active status.

        Reverses the scrap action.

        Args:
            asset_name: Asset name/ID to restore
        """
        return erpnext.restore_asset(asset_name)

    @mcp.tool()
    def create_asset_movement(asset: str) -> dict:
        """Create an asset movement record.

        Tracks when an asset is moved between locations or departments.

        Args:
            asset: Asset name/ID to move
        """
        return erpnext.make_asset_movement(source_name=asset)
