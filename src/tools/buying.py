"""Buying MCP tools — purchase document conversions and returns."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext


def register(mcp: FastMCP):

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
