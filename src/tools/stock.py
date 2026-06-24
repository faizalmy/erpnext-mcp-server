"""Stock MCP tools — inventory movements, balances, and delivery conversions."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

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
