"""Accounting MCP tools — balances, payments, returns, exchange rates."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

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
