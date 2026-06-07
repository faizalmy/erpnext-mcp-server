"""MCP tools for Stock/Inventory module.

Item, Stock Entry, Delivery Note, Stock Balance, Batch, Serial No, Warehouse.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def list_items(fields: list[str] | None = None, filters: list | None = None,
                   limit: int = 20) -> dict:
        """List items (products and services).

        Args:
            fields: Fields to return. Example: ["name", "item_name", "item_group", "standard_rate"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Item", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_item(name: str) -> dict:
        """Get item details.

        Args:
            name: Item code/name
        """
        return erpnext.get_document("Item", name)

    @mcp.tool()
    def create_item(item_code: str, item_name: str, item_group: str = "All Item Groups",
                    stock_uom: str = "Nos", standard_rate: float = 0,
                    is_stock_item: int = 1) -> dict:
        """Create a new item.

        Args:
            item_code: Unique item code
            item_name: Item display name
            item_group: Item group (default: All Item Groups)
            stock_uom: Stock unit of measure (default: Nos)
            standard_rate: Standard selling rate (default: 0)
            is_stock_item: 1 for stock item, 0 for service
        """
        data = {
            "item_code": item_code,
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": stock_uom,
            "standard_rate": standard_rate,
            "is_stock_item": is_stock_item,
        }
        return erpnext.create_document("Item", data)

    @mcp.tool()
    def get_item_details(item_code: str, company: str = "", warehouse: str = "") -> dict:
        """Get full item details including stock levels, pricing, and defaults.

        Args:
            item_code: Item code
            company: Company context (optional)
            warehouse: Warehouse context (optional)
        """
        return erpnext.get_item_details(item_code, company=company, warehouse=warehouse)

    @mcp.tool()
    def get_stock_balance(item_code: str, warehouse: str = "",
                          posting_date: str = "") -> dict:
        """Get current stock balance for an item.

        Args:
            item_code: Item code
            warehouse: Warehouse (optional, all warehouses if omitted)
            posting_date: Date to check (optional, today if omitted)
        """
        return erpnext.get_stock_balance(item_code, warehouse=warehouse, posting_date=posting_date)

    @mcp.tool()
    def list_stock_entries(fields: list[str] | None = None, filters: list | None = None,
                           limit: int = 20) -> dict:
        """List stock entries (stock movements).

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Stock Entry", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_stock_entry(name: str) -> dict:
        """Get stock entry details.

        Args:
            name: Stock Entry name/ID
        """
        return erpnext.get_document("Stock Entry", name)

    @mcp.tool()
    def make_stock_entry(item_code: str, qty: float, from_warehouse: str = "",
                         to_warehouse: str = "", purpose: str = "Material Transfer") -> dict:
        """Create a stock entry for material transfer or issue.

        Args:
            item_code: Item to move
            qty: Quantity to move
            from_warehouse: Source warehouse (optional for Material Receipt)
            to_warehouse: Destination warehouse (optional for Material Issue)
            purpose: 'Material Transfer', 'Material Issue', 'Material Receipt', 'Manufacture'
        """
        return erpnext.make_stock_entry(
            item_code=item_code, qty=qty,
            from_warehouse=from_warehouse, to_warehouse=to_warehouse,
            purpose=purpose,
        )

    @mcp.tool()
    def list_delivery_notes(fields: list[str] | None = None, filters: list | None = None,
                            limit: int = 20) -> dict:
        """List delivery notes.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Delivery Note", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_delivery_note(name: str) -> dict:
        """Get delivery note details.

        Args:
            name: Delivery Note name/ID
        """
        return erpnext.get_document("Delivery Note", name)

    @mcp.tool()
    def make_sales_invoice_from_dn(delivery_note: str) -> dict:
        """Create a sales invoice from a delivery note.

        Args:
            delivery_note: Delivery Note name/ID
        """
        return erpnext.make_sales_invoice_from_dn(delivery_note)

    @mcp.tool()
    def make_sales_return_from_dn(delivery_note: str) -> dict:
        """Create a sales return from a delivery note.

        Args:
            delivery_note: Delivery Note name/ID
        """
        return erpnext.make_sales_return_from_dn(delivery_note)

    @mcp.tool()
    def list_warehouses(fields: list[str] | None = None, filters: list | None = None,
                        limit: int = 50) -> dict:
        """List warehouses.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Warehouse", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_batch_qty(batch_no: str, warehouse: str = "") -> dict:
        """Get quantity available in a specific batch.

        Args:
            batch_no: Batch number
            warehouse: Filter by warehouse (optional)
        """
        return erpnext.get_batch_qty(batch_no, warehouse=warehouse)

    @mcp.tool()
    def list_batches(fields: list[str] | None = None, filters: list | None = None,
                     limit: int = 20) -> dict:
        """List batches.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Batch", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def list_serial_nos(fields: list[str] | None = None, filters: list | None = None,
                        limit: int = 20) -> dict:
        """List serial numbers.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Serial No", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_stock_ledger_entries(item_code: str, warehouse: str = "",
                                 posting_date_from: str = "",
                                 posting_date_to: str = "") -> dict:
        """Get stock ledger entries (movement history) for an item.

        Args:
            item_code: Item code
            warehouse: Filter by warehouse (optional)
            posting_date_from: Start date (YYYY-MM-DD, optional)
            posting_date_to: End date (YYYY-MM-DD, optional)
        """
        return erpnext.get_stock_ledger_entries(
            item_code, warehouse=warehouse,
            posting_date_from=posting_date_from, posting_date_to=posting_date_to,
        )
