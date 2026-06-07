"""MCP tools for Selling module.

Customer, Sales Order, Quotation, Lead, Opportunity.
"""

from mcp.server.fastmcp import FastMCP
from ..erpnext_client import erpnext


def register(mcp: FastMCP):

    @mcp.tool()
    def list_customers(fields: list[str] | None = None, filters: list | None = None, limit: int = 20) -> dict:
        """List customers.

        Args:
            fields: Fields to return. Default: all. Example: ["name", "customer_name", "territory"]
            filters: ERPNext filters. Example: [["Customer", "territory", "=", "Malaysia"]]
            limit: Max results (default 20)
        """
        return erpnext.list_documents("Customer", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_customer(name: str) -> dict:
        """Get customer details.

        Args:
            name: Customer name/ID (e.g. 'CUST-00001')
        """
        return erpnext.get_document("Customer", name)

    @mcp.tool()
    def create_customer(customer_name: str, customer_group: str = "All Customer Groups",
                        territory: str = "All Territories", tax_id: str = "",
                        customer_type: str = "Company") -> dict:
        """Create a new customer.

        Args:
            customer_name: Company or individual name
            customer_group: Customer group (default: All Customer Groups)
            territory: Territory (default: All Territories)
            tax_id: Tax registration number (optional)
            customer_type: 'Company' or 'Individual'
        """
        data = {
            "customer_name": customer_name,
            "customer_group": customer_group,
            "territory": territory,
            "customer_type": customer_type,
        }
        if tax_id:
            data["tax_id"] = tax_id
        return erpnext.create_document("Customer", data)

    @mcp.tool()
    def list_sales_orders(fields: list[str] | None = None, filters: list | None = None,
                          limit: int = 20) -> dict:
        """List sales orders.

        Args:
            fields: Fields to return. Example: ["name", "customer", "grand_total", "status"]
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Sales Order", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_sales_order(name: str) -> dict:
        """Get sales order details.

        Args:
            name: Sales Order name/ID
        """
        return erpnext.get_document("Sales Order", name)

    @mcp.tool()
    def list_quotations(fields: list[str] | None = None, filters: list | None = None,
                        limit: int = 20) -> dict:
        """List sales quotations.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Quotation", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_quotation(name: str) -> dict:
        """Get quotation details.

        Args:
            name: Quotation name/ID
        """
        return erpnext.get_document("Quotation", name)

    @mcp.tool()
    def make_sales_order_from_quotation(quotation: str) -> dict:
        """Convert a quotation to a sales order.

        Args:
            quotation: Quotation name/ID to convert
        """
        return erpnext.make_sales_order_from_quotation(quotation)

    @mcp.tool()
    def make_sales_invoice_from_sales_order(sales_order: str) -> dict:
        """Create a sales invoice from a sales order.

        Args:
            sales_order: Sales Order name/ID
        """
        return erpnext.make_sales_invoice_from_sales_order(sales_order)

    @mcp.tool()
    def make_delivery_note_from_sales_order(sales_order: str) -> dict:
        """Create a delivery note from a sales order.

        Args:
            sales_order: Sales Order name/ID
        """
        return erpnext.make_delivery_note_from_sales_order(sales_order)

    @mcp.tool()
    def make_sales_return(sales_invoice: str) -> dict:
        """Create a sales return (credit note) from an existing invoice.

        Args:
            sales_invoice: Sales Invoice name/ID to return
        """
        return erpnext.make_sales_return(sales_invoice)

    # ── CRM ───────────────────────────────────────────────

    @mcp.tool()
    def list_leads(fields: list[str] | None = None, filters: list | None = None,
                   limit: int = 20) -> dict:
        """List leads.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Lead", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_lead(name: str) -> dict:
        """Get lead details.

        Args:
            name: Lead name/ID
        """
        return erpnext.get_document("Lead", name)

    @mcp.tool()
    def make_opportunity_from_lead(lead: str) -> dict:
        """Convert a lead to an opportunity.

        Args:
            lead: Lead name/ID
        """
        return erpnext.make_opportunity_from_lead(lead)

    @mcp.tool()
    def make_customer_from_lead(lead: str) -> dict:
        """Convert a lead to a customer.

        Args:
            lead: Lead name/ID
        """
        return erpnext.make_customer_from_lead(lead)

    @mcp.tool()
    def list_opportunities(fields: list[str] | None = None, filters: list | None = None,
                           limit: int = 20) -> dict:
        """List sales opportunities.

        Args:
            fields: Fields to return
            filters: ERPNext filters
            limit: Max results
        """
        return erpnext.list_documents("Opportunity", fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def make_quotation_from_opportunity(opportunity: str) -> dict:
        """Create a quotation from an opportunity.

        Args:
            opportunity: Opportunity name/ID
        """
        return erpnext.make_quotation_from_opportunity(opportunity)
