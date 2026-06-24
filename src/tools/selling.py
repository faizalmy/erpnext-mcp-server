"""Selling MCP tools — URL generation and document conversions for the sales pipeline."""

import re
from urllib.parse import urlencode

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext, get_request_url


def _doctype_to_url_path(doctype: str) -> str:
    """Convert an ERPNext DocType name to its URL path slug.

    Examples:
        'Sales Invoice' -> 'sales-invoice'
        'Purchase Order' -> 'purchase-order'
        'Payment Entry' -> 'payment-entry'
        'BOM' -> 'bom'
        'Item' -> 'item'
    """
    return re.sub(r'\s+', '-', doctype).lower()


def register(mcp: FastMCP):

    @mcp.tool()
    def get_erpnext_url(
        doctype: str,
        name: str | None = None,
        filters: dict[str, str] | None = None,
    ) -> dict:
        """Generate a direct link to an ERPNext page for a given DocType.

        Use this when the user asks for a link to open ERPNext directly,
        e.g. "link to overdue invoices" or "take me to that customer record".

        Returns a URL you can present to the user as a clickable link.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice', 'Customer', 'Purchase Order')
            name: Optional document name/ID for form view (e.g. 'SINV-00001').
                  If omitted, generates a list view URL.
            filters: Optional dict of filter params for the list view.
                     Example: {"status": "Overdue", "customer": "West View Software"}
        """
        base = (get_request_url() or "http://localhost:8080").rstrip("/")
        path = _doctype_to_url_path(doctype)

        url = f"{base}/desk/{path}"

        if name:
            url = f"{url}/{name}"
        elif filters:
            qs = urlencode(filters)
            url = f"{url}?{qs}"

        description_parts = [f"Open {doctype}"]

        if name:
            description_parts.append(f"record \"{name}\"")
        elif filters:
            filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items())
            description_parts.append(f"filtered by ({filter_desc})")

        return {
            "url": url,
            "doctype": doctype,
            "name": name,
            "filters": filters,
            "description": " ".join(description_parts),
        }

    @mcp.tool()
    def convert_quotation_to_sales_order(quotation: str) -> dict:
        """Convert an accepted Quotation into a Sales Order.

        Creates a new Sales Order with items from the quotation.
        The quotation must be in 'Submitted' status.

        Args:
            quotation: Quotation name/ID (e.g. 'QTN-00001')
        """
        return erpnext.make_sales_order_from_quotation(source_name=quotation)

    @mcp.tool()
    def convert_sales_order_to_invoice(sales_order: str) -> dict:
        """Convert a Sales Order into a Sales Invoice.

        Creates an invoice from the order for billing.
        The sales order must be submitted.

        Args:
            sales_order: Sales Order name/ID (e.g. 'SAL-ORD-00001')
        """
        return erpnext.make_sales_invoice_from_sales_order(source_name=sales_order)

    @mcp.tool()
    def convert_sales_order_to_delivery(sales_order: str) -> dict:
        """Convert a Sales Order into a Delivery Note.

        Creates a delivery note for shipping/fulfillment.
        Used when goods are ready to ship.

        Args:
            sales_order: Sales Order name/ID (e.g. 'SAL-ORD-00001')
        """
        return erpnext.make_delivery_note_from_sales_order(source_name=sales_order)

    @mcp.tool()
    def convert_opportunity_to_quotation(opportunity: str) -> dict:
        """Convert an Opportunity into a Quotation.

        Creates a quotation from a sales opportunity.
        Used in the CRM pipeline: Lead → Opportunity → Quotation.

        Args:
            opportunity: Opportunity name/ID (e.g. 'CRM-OPP-00001')
        """
        return erpnext.make_quotation_from_opportunity(source_name=opportunity)

    @mcp.tool()
    def convert_lead_to_opportunity(lead: str) -> dict:
        """Convert a Lead into an Opportunity.

        First step in the sales pipeline when a lead shows interest.

        Args:
            lead: Lead name/ID (e.g. 'CRM-LEAD-00001')
        """
        return erpnext.make_opportunity_from_lead(source_name=lead)

    @mcp.tool()
    def convert_lead_to_customer(lead: str) -> dict:
        """Convert a Lead directly into a Customer.

        Skips the opportunity stage — use when the lead is ready to buy.

        Args:
            lead: Lead name/ID (e.g. 'CRM-LEAD-00001')
        """
        return erpnext.make_customer_from_lead(source_name=lead)
