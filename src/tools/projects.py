"""Projects MCP tools — timesheet invoicing."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def convert_timesheet_to_invoice(timesheet: str) -> dict:
        """Convert a Timesheet into a Sales Invoice.

        Bills the client for time worked. Creates an invoice with
        timesheet line items.

        Args:
            timesheet: Timesheet name/ID (e.g. 'TIM-00001')
        """
        return erpnext.make_sales_invoice_from_timesheet(source_name=timesheet)
