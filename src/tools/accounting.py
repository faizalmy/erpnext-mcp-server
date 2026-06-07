"""MCP tools for accounting operations.

Invoices, payments, and financial reports.
All write operations go through the approval engine.
Read operations (reports) return data with ai_context enrichment.
"""

from mcp.server.fastmcp import FastMCP

from ..gateway import gateway


def register(mcp: FastMCP):
    """Register accounting tools on the MCP server."""

    @mcp.tool()
    def create_invoice(
        customer: str,
        items: list[dict],
        due_date: str = "",
        company: str = "",
    ) -> dict:
        """Create a sales invoice for a customer (goes through approval).

        SST 8% is calculated automatically by ERPNext.
        The approval preview shows the exact total before execution.

        Args:
            customer: Customer name (must exist in ERPNext)
            items: Line items. Each item needs:
                - item_code (str): Item code or name
                - qty (int): Quantity
                - rate (float): Unit price in MYR
            due_date: Optional due date (YYYY-MM-DD format)
            company: Optional company name (defaults to primary company)

        Returns:
            Intent with preview showing subtotal, SST, and total.
        """
        return gateway.create_invoice(
            customer=customer,
            items=items,
            due_date=due_date,
            company=company,
        )

    @mcp.tool()
    def record_payment(
        party: str,
        amount: float,
        payment_type: str = "Receive",
        reference: str = "",
    ) -> dict:
        """Record a payment (goes through approval).

        Args:
            party: Customer or Supplier name
            amount: Payment amount in MYR
            payment_type: 'Receive' (money in) or 'Pay' (money out)
            reference: Optional reference (invoice number, cheque number, etc.)

        Returns:
            Intent with preview for approval.
        """
        return gateway.record_payment(
            party=party,
            amount=amount,
            payment_type=payment_type,
            reference=reference,
        )

    @mcp.tool()
    def get_trial_balance(
        company: str = "",
        from_date: str = "",
        to_date: str = "",
    ) -> dict:
        """Get the trial balance report (read-only, no approval needed).

        Shows all account balances — debits and credits must match.

        Args:
            company: Filter by company (optional)
            from_date: Start date (YYYY-MM-DD, optional)
            to_date: End date (YYYY-MM-DD, optional)

        Returns:
            Trial balance data with ai_context (totals, warnings).
        """
        return gateway.get_trial_balance(
            company=company, from_date=from_date, to_date=to_date
        )

    @mcp.tool()
    def get_profit_and_loss(
        company: str = "",
        from_date: str = "",
        to_date: str = "",
    ) -> dict:
        """Get the Profit & Loss statement (read-only).

        Shows revenue, expenses, and net profit for a period.

        Args:
            company: Filter by company (optional)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            P&L data with ai_context (summary, trends, warnings).
        """
        return gateway.get_profit_and_loss(
            company=company, from_date=from_date, to_date=to_date
        )

    @mcp.tool()
    def get_balance_sheet(
        company: str = "",
        from_date: str = "",
        to_date: str = "",
    ) -> dict:
        """Get the Balance Sheet (read-only).

        Shows assets, liabilities, and equity at a point in time.

        Args:
            company: Filter by company (optional)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Balance sheet data with ai_context.
        """
        return gateway.get_balance_sheet(
            company=company, from_date=from_date, to_date=to_date
        )
