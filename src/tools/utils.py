"""Shared utilities for curated MCP tools."""

import re


def doctype_to_url_path(doctype: str) -> str:
    """Convert an ERPNext DocType name to its URL path slug.

    Examples:
        'Sales Invoice' -> 'sales-invoice'
        'Purchase Order' -> 'purchase-order'
        'Payment Entry' -> 'payment-entry'
        'BOM' -> 'bom'
        'Item' -> 'item'
    """
    return re.sub(r'\s+', '-', doctype).lower()
