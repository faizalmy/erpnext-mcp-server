"""MCP tools for Accounting module.

Sales Invoice, Purchase Invoice, Payment Entry, and financial reports.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def create_sales_invoice(customer: str, items: list[dict],
                             due_date: str = "", company: str = "") -> dict:
        """Create a sales invoice.

        Args:
            customer: Customer name (must exist in ERPNext)
            items: Line items. Each item needs:
                - item_code (str): Item code or name
                - qty (int): Quantity
                - rate (float): Unit price
            due_date: Optional due date (YYYY-MM-DD)
            company: Optional company name

        Returns:
            Created invoice from ERPNext.
        """
        data = {"customer": customer, "items": items}
        if due_date:
            data["due_date"] = due_date
        if company:
            data["company"] = company
        return erpnext.create_document("Sales Invoice", data)

    @mcp.tool()
    def create_purchase_invoice(supplier: str, items: list[dict],
                                due_date: str = "", company: str = "") -> dict:
        """Create a purchase invoice.

        Args:
            supplier: Supplier name (must exist in ERPNext)
            items: Line items. Each item needs:
                - item_code (str): Item code
                - qty (int): Quantity
                - rate (float): Unit price
            due_date: Optional due date (YYYY-MM-DD)
            company: Optional company name

        Returns:
            Created invoice from ERPNext.
        """
        data = {"supplier": supplier, "items": items}
        if due_date:
            data["due_date"] = due_date
        if company:
            data["company"] = company
        return erpnext.create_document("Purchase Invoice", data)

    @mcp.tool()
    def record_payment(party: str, amount: float,
                       payment_type: str = "Receive",
                       party_type: str = "Customer",
                       reference: str = "") -> dict:
        """Record a payment entry.

        Args:
            party: Customer or Supplier name
            amount: Payment amount
            payment_type: 'Receive' (money in) or 'Pay' (money out)
            party_type: 'Customer' or 'Supplier'
            reference: Optional reference (invoice number, cheque number)

        Returns:
            Created payment entry from ERPNext.
        """
        data = {
            "party": party,
            "paid_amount": amount,
            "payment_type": payment_type,
            "party_type": party_type,
        }
        if reference:
            data["reference_no"] = reference
        return erpnext.create_document("Payment Entry", data)

    @mcp.tool()
    def get_trial_balance(company: str = "", from_date: str = "",
                          to_date: str = "") -> dict:
        """Get the trial balance report (read-only).

        Shows all account balances -- debits and credits must match.

        Args:
            company: Filter by company (optional)
            from_date: Start date (YYYY-MM-DD, optional)
            to_date: End date (YYYY-MM-DD, optional)

        Returns:
            Trial balance data from ERPNext.
        """
        return erpnext.call_method(
            "erpnext.accounts.utils.get_balance_on",
            account="Trial Balance", date=to_date, company=company,
        )

    @mcp.tool()
    def get_profit_and_loss(company: str = "", from_date: str = "",
                            to_date: str = "") -> dict:
        """Get the Profit & Loss statement (read-only).

        Shows revenue, expenses, and net profit for a period.

        Args:
            company: Filter by company (optional)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            P&L data from ERPNext.
        """
        return erpnext.call_method(
            "erpnext.accounts.report.profit_and_loss_statement.profit_and_loss_statement.execute",
            filters={
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
            },
        )

    @mcp.tool()
    def get_balance_sheet(company: str = "", from_date: str = "",
                          to_date: str = "") -> dict:
        """Get the Balance Sheet (read-only).

        Shows assets, liabilities, and equity at a point in time.

        Args:
            company: Filter by company (optional)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Balance sheet data from ERPNext.
        """
        return erpnext.call_method(
            "erpnext.accounts.report.balance_sheet.balance_sheet.execute",
            filters={
                "company": company,
                "from_date": from_date,
                "to_date": to_date,
            },
        )

    @mcp.tool()
    def list_sales_invoices(fields: list[str] | None = None,
                            filters: list | None = None,
                            limit: int = 20) -> dict:
        """List sales invoices.

        Args:
            fields: Fields to return. Example: ["name", "customer", "grand_total", "status"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Sales Invoice", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_sales_invoice(name: str) -> dict:
        """Get a sales invoice by name.

        Args:
            name: Sales Invoice name/ID (e.g. 'SINV-2026-00001')
        """
        return erpnext.get_document("Sales Invoice", name)

    @mcp.tool()
    def list_purchase_invoices(fields: list[str] | None = None,
                               filters: list | None = None,
                               limit: int = 20) -> dict:
        """List purchase invoices.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Purchase Invoice", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def list_payment_entries(fields: list[str] | None = None,
                             filters: list | None = None,
                             limit: int = 20) -> dict:
        """List payment entries.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Payment Entry", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_exchange_rate(from_currency: str, to_currency: str,
                          date: str = "") -> dict:
        """Get exchange rate between two currencies.

        Args:
            from_currency: Source currency (e.g. 'USD')
            to_currency: Target currency (e.g. 'MYR')
            date: Date for rate (YYYY-MM-DD, optional)
        """
        return erpnext.get_exchange_rate(from_currency, to_currency, date=date)

    @mcp.tool()
    def list_journal_entries(fields: list[str] | None = None,
                             filters: list | None = None,
                             limit: int = 20) -> dict:
        """List journal entries.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Journal Entry", fields=fields, filters=filters, limit=limit)
