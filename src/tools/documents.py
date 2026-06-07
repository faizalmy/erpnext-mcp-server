"""MCP tools for generic ERPNext document operations.

These tools work with ANY ERPNext DocType (Customer, Supplier, Item, etc.).
For domain-specific operations (invoices, payroll), see accounting.py and hr.py.
"""

from mcp.server.fastmcp import FastMCP

from ..gateway import gateway


def register(mcp: FastMCP):
    """Register document tools on the MCP server."""

    @mcp.tool()
    def list_documents(
        doctype: str,
        fields: list[str] | None = None,
        filters: list | None = None,
        limit: int = 20,
    ) -> dict:
        """List documents of any ERPNext DocType.

        Use this to browse master data (Customer, Supplier, Item, Employee)
        or transactional data (Sales Order, Purchase Invoice, etc.).

        Args:
            doctype: ERPNext DocType name (e.g. 'Customer', 'Supplier', 'Item')
            fields: Fields to return (default: all). Example: ["name", "customer_name", "territory"]
            filters: ERPNext filters. Example: [["Customer", "territory", "=", "Malaysia"]]
            limit: Max results (default 20, max 200)

        Returns:
            List of documents with ai_context.
        """
        return gateway.list_documents(
            doctype=doctype,
            fields=fields,
            filters=filters,
            limit=min(limit, 200),
        )

    @mcp.tool()
    def get_document(doctype: str, name: str) -> dict:
        """Get a single ERPNext document by name.

        Args:
            doctype: DocType name (e.g. 'Customer', 'Sales Invoice')
            name: Document name/ID (e.g. 'CUST-00001', 'INV-2026-00001')

        Returns:
            Full document with ai_context.
        """
        return gateway.get_document(doctype=doctype, name=name)

    @mcp.tool()
    def create_document(doctype: str, data: dict) -> dict:
        """Create a new ERPNext document (goes through approval).

        Use this for generic DocType creation. For invoices and payroll,
        prefer the specialized tools (create_invoice, run_payroll) which
        include proper previews and statutory validation.

        Args:
            doctype: DocType to create (e.g. 'Customer', 'Supplier', 'Item')
            data: Document fields. Example: {"customer_name": "Acme Sdn Bhd", "customer_group": "All Customer Groups", "territory": "Malaysia"}

        Returns:
            Intent ID and preview for approval.
        """
        return gateway.create_document(doctype=doctype, data=data)

    @mcp.tool()
    def update_document(doctype: str, name: str, data: dict) -> dict:
        """Update an existing ERPNext document (goes through approval).

        Args:
            doctype: DocType name
            name: Document name/ID
            data: Fields to update. Example: {"customer_name": "Acme Corp Sdn Bhd"}

        Returns:
            Intent ID and preview for approval.
        """
        return gateway.update_document(doctype=doctype, name=name, data=data)

    @mcp.tool()
    def submit_document(doctype: str, name: str) -> dict:
        """Submit a draft document (goes through approval).

        Submitting makes a document 'final' — it can no longer be edited,
        only amended. This is how invoices, payments, and stock entries
        become permanent records.

        Args:
            doctype: DocType name
            name: Document name/ID

        Returns:
            Intent ID and preview for approval.
        """
        return gateway.submit_document(doctype=doctype, name=name)
