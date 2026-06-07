"""MCP tools for Buying module.

Supplier, Purchase Order, Purchase Receipt, Material Request, Supplier Quotation.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def list_suppliers(fields: list[str] | None = None, filters: list | None = None,
                       limit: int = 20) -> dict:
        """List suppliers.

        Args:
            fields: Fields to return. Example: ["name", "supplier_name", "supplier_group"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Supplier", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_supplier(name: str) -> dict:
        """Get supplier details.

        Args:
            name: Supplier name/ID
        """
        return erpnext.get_document("Supplier", name)

    @mcp.tool()
    def create_supplier(supplier_name: str, supplier_group: str = "All Supplier Groups",
                        supplier_type: str = "Company", tax_id: str = "") -> dict:
        """Create a new supplier.

        Args:
            supplier_name: Company or individual name
            supplier_group: Supplier group
            supplier_type: 'Company' or 'Individual'
            tax_id: Tax registration number (optional)
        """
        data = {
            "supplier_name": supplier_name,
            "supplier_group": supplier_group,
            "supplier_type": supplier_type,
        }
        if tax_id:
            data["tax_id"] = tax_id
        return erpnext.create_document("Supplier", data)

    @mcp.tool()
    def list_purchase_orders(fields: list[str] | None = None, filters: list | None = None,
                             limit: int = 20) -> dict:
        """List purchase orders.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Purchase Order", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_purchase_order(name: str) -> dict:
        """Get purchase order details.

        Args:
            name: Purchase Order name/ID
        """
        return erpnext.get_document("Purchase Order", name)

    @mcp.tool()
    def make_purchase_receipt_from_po(purchase_order: str) -> dict:
        """Create a purchase receipt (goods received) from a PO.

        Args:
            purchase_order: Purchase Order name/ID
        """
        return erpnext.make_purchase_receipt_from_po(purchase_order)

    @mcp.tool()
    def make_purchase_invoice_from_po(purchase_order: str) -> dict:
        """Create a purchase invoice from a PO.

        Args:
            purchase_order: Purchase Order name/ID
        """
        return erpnext.make_purchase_invoice_from_po(purchase_order)

    @mcp.tool()
    def list_purchase_receipts(fields: list[str] | None = None, filters: list | None = None,
                               limit: int = 20) -> dict:
        """List purchase receipts.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Purchase Receipt", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def make_purchase_invoice_from_pr(purchase_receipt: str) -> dict:
        """Create a purchase invoice from a purchase receipt.

        Args:
            purchase_receipt: Purchase Receipt name/ID
        """
        return erpnext.make_purchase_invoice_from_pr(purchase_receipt)

    @mcp.tool()
    def make_purchase_return(purchase_receipt: str) -> dict:
        """Create a purchase return from a purchase receipt.

        Args:
            purchase_receipt: Purchase Receipt name/ID
        """
        return erpnext.make_purchase_return(purchase_receipt)

    @mcp.tool()
    def list_material_requests(fields: list[str] | None = None, filters: list | None = None,
                               limit: int = 20) -> dict:
        """List material requests.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Material Request", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def make_purchase_order_from_mr(material_request: str) -> dict:
        """Create a purchase order from a material request.

        Args:
            material_request: Material Request name/ID
        """
        return erpnext.make_purchase_order_from_mr(material_request)

    @mcp.tool()
    def make_supplier_quotation_from_mr(material_request: str) -> dict:
        """Create a supplier quotation from a material request.

        Args:
            material_request: Material Request name/ID
        """
        return erpnext.make_supplier_quotation_from_mr(material_request)
