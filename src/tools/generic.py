"""Generic MCP tools — flexible document operations."""

from mcp.server.fastmcp import FastMCP

from ..erpnext_client import erpnext, get_request_url
from .utils import doctype_to_url_path


def register(mcp: FastMCP):

    @mcp.tool()
    def list_documents(
        doctype: str,
        fields: list[str] | None = None,
        filters: list | None = None,
        limit: int = 20,
    ) -> dict:
        """List documents of any ERPNext DocType with full filter support.

        Use this for flexible queries when the auto-generated list_* tools
        are too restrictive. Supports ERPNext filter syntax.

        Args:
            doctype: DocType name (e.g. 'Customer', 'Sales Invoice')
            fields: Fields to return. Example: ["name", "customer_name"]
            filters: ERPNext filters. Example: [["Customer", "territory", "=", "Malaysia"]]
            limit: Max records (default 20)
        """
        return erpnext.list_documents(doctype, fields=fields, filters=filters, limit=limit)

    @mcp.tool()
    def get_document(doctype: str, name: str) -> dict:
        """Get any ERPNext document by DocType and name.

        Use this when you need a specific document and know its exact DocType.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice')
            name: Document name/ID (e.g. 'SINV-00001')
        """
        return erpnext.get_document(doctype, name)

    @mcp.tool()
    def submit_document(doctype: str, name: str) -> dict:
        """Submit (finalize) a draft document.

        ERPNext has draft → submitted workflow for many DocTypes
        (Sales Invoice, Purchase Order, Stock Entry, etc.).
        Once submitted, the document cannot be edited — only cancelled.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice')
            name: Document name/ID to submit
        """
        return erpnext.submit_document(doctype, name)

    @mcp.tool()
    def cancel_document(doctype: str, name: str) -> dict:
        """Cancel a submitted document.

        Reverses the effects of submission. The document returns to draft state.

        Args:
            doctype: DocType name (e.g. 'Sales Invoice')
            name: Document name/ID to cancel
        """
        return erpnext.cancel_document(doctype, name)
