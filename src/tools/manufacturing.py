"""MCP tools for Manufacturing module.

Work Order, BOM (Bill of Materials), Production Plan, Job Card.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def list_work_orders(fields: list[str] | None = None, filters: list | None = None,
                         limit: int = 20) -> dict:
        """List work orders (production orders).

        Args:
            fields: Fields to return. Example: ["name", "production_item", "qty", "status"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Work Order", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_work_order(name: str) -> dict:
        """Get work order details.

        Args:
            name: Work Order name/ID
        """
        return erpnext.get_document("Work Order", name)

    @mcp.tool()
    def create_work_order(production_item: str, qty: float, bom_no: str,
                          company: str = "", fg_warehouse: str = "",
                          wip_warehouse: str = "") -> dict:
        """Create a work order for manufacturing.

        Args:
            production_item: Item to manufacture
            qty: Quantity to produce
            bom_no: Bill of Materials to use
            company: Company name (optional)
            fg_warehouse: Finished goods warehouse (optional)
            wip_warehouse: Work-in-progress warehouse (optional)
        """
        data = {
            "production_item": production_item,
            "qty": qty,
            "bom_no": bom_no,
        }
        if company:
            data["company"] = company
        if fg_warehouse:
            data["fg_warehouse"] = fg_warehouse
        if wip_warehouse:
            data["wip_warehouse"] = wip_warehouse
        return erpnext.create_document("Work Order", data)

    @mcp.tool()
    def make_stock_entry_from_work_order(work_order: str) -> dict:
        """Create a stock entry (material transfer/manufacture) from a work order.

        Args:
            work_order: Work Order name/ID
        """
        return erpnext.make_stock_entry_from_wo(work_order)

    @mcp.tool()
    def list_boms(fields: list[str] | None = None, filters: list | None = None,
                  limit: int = 20) -> dict:
        """List Bills of Materials.

        Args:
            fields: Fields to return. Example: ["name", "item", "quantity", "is_active"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("BOM", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_bom(name: str) -> dict:
        """Get BOM details including raw materials and operations.

        Args:
            name: BOM name/ID
        """
        return erpnext.get_document("BOM", name)

    @mcp.tool()
    def get_bom_items(bom: str, company: str = "", qty: float = 0) -> dict:
        """Get the list of raw materials in a BOM with quantities and rates.

        Args:
            bom: BOM name/ID
            company: Company context (optional)
            qty: Override quantity (optional, uses BOM qty if omitted)
        """
        return erpnext.get_bom_items(bom, company=company, qty=qty)

    @mcp.tool()
    def get_exploded_items(bom: str, qty: float = 0) -> dict:
        """Get exploded (multi-level) BOM items — includes sub-assembly components.

        Args:
            bom: BOM name/ID
            qty: Override quantity (optional)
        """
        return erpnext.get_exploded_items(bom, qty=qty)

    @mcp.tool()
    def list_production_plans(fields: list[str] | None = None, filters: list | None = None,
                              limit: int = 20) -> dict:
        """List production plans.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Production Plan", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_production_plan(name: str) -> dict:
        """Get production plan details.

        Args:
            name: Production Plan name/ID
        """
        return erpnext.get_document("Production Plan", name)

    @mcp.tool()
    def make_material_request_from_pp(production_plan: str) -> dict:
        """Generate material requests from a production plan.

        Args:
            production_plan: Production Plan name/ID
        """
        return erpnext.make_material_request_from_pp(production_plan)

    @mcp.tool()
    def make_work_order_from_pp(production_plan: str) -> dict:
        """Generate work orders from a production plan.

        Args:
            production_plan: Production Plan name/ID
        """
        return erpnext.make_work_order_from_pp(production_plan)

    @mcp.tool()
    def list_job_cards(fields: list[str] | None = None, filters: list | None = None,
                       limit: int = 20) -> dict:
        """List job cards (shop floor work instructions).

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Job Card", fields=fields, filters=filters, limit=limit)
