"""Assets MCP tools — invoicing, movements, and lifecycle management."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

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
