"""Manufacturing MCP tools — BOM item listings."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

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
