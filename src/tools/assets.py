"""MCP tools for Assets module.

Asset, Asset Category, Asset Movement, Asset Maintenance, Asset Repair.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def list_assets(fields: list[str] | None = None, filters: list | None = None,
                    limit: int = 20) -> dict:
        """List fixed assets.

        Args:
            fields: Fields to return. Example: ["name", "asset_name", "status", "gross_purchase_amount"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Asset", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_asset(name: str) -> dict:
        """Get asset details including depreciation schedule.

        Args:
            name: Asset name/ID
        """
        return erpnext.get_document("Asset", name)

    @mcp.tool()
    def create_asset(asset_name: str, asset_category: str, item_code: str,
                     company: str = "", gross_purchase_amount: float = 0,
                     purchase_date: str = "") -> dict:
        """Create a new fixed asset.

        Args:
            asset_name: Asset display name
            asset_category: Asset category (must exist)
            item_code: Linked item code
            company: Company name (optional)
            gross_purchase_amount: Purchase cost in MYR
            purchase_date: Purchase date YYYY-MM-DD (optional)
        """
        data = {
            "asset_name": asset_name,
            "asset_category": asset_category,
            "item_code": item_code,
        }
        if company:
            data["company"] = company
        if gross_purchase_amount:
            data["gross_purchase_amount"] = gross_purchase_amount
        if purchase_date:
            data["purchase_date"] = purchase_date
        return erpnext.create_document("Asset", data)

    @mcp.tool()
    def make_sales_invoice_from_asset(asset: str) -> dict:
        """Create a sales invoice for disposing/selling an asset.

        Args:
            asset: Asset name/ID
        """
        return erpnext.make_asset_sales_invoice(asset)

    @mcp.tool()
    def scrap_asset(asset_name: str) -> dict:
        """Scrap an asset (mark as scrapped, no sale proceeds).

        Args:
            asset_name: Asset name/ID
        """
        return erpnext.scrap_asset(asset_name)

    @mcp.tool()
    def restore_asset(asset_name: str) -> dict:
        """Restore a scrapped asset back to active.

        Args:
            asset_name: Asset name/ID
        """
        return erpnext.restore_asset(asset_name)

    @mcp.tool()
    def make_asset_movement(asset: str) -> dict:
        """Create an asset movement/transfer.

        Args:
            asset: Asset name/ID
        """
        return erpnext.make_asset_movement(asset)

    @mcp.tool()
    def list_asset_categories(fields: list[str] | None = None, limit: int = 50) -> dict:
        """List asset categories.

        Args:
            fields: Fields to return
            limit: Max results
        """
        return erpnext.list_documents("Asset Category", fields=fields, limit=limit)

    @mcp.tool()
    def list_asset_maintenance(fields: list[str] | None = None, filters: list | None = None,
                               limit: int = 20) -> dict:
        """List asset maintenance schedules.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Asset Maintenance", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def list_asset_repairs(fields: list[str] | None = None, filters: list | None = None,
                           limit: int = 20) -> dict:
        """List asset repairs.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Asset Repair", fields=fields, filters=filters, limit=limit)
