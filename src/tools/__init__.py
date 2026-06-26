"""Curated MCP tools — high-level ERPNext operations registered as FastMCP tools."""

from . import generic, accounting, selling, buying, stock, hr, manufacturing, projects, assets

def register(mcp) -> None:
    """Register all curated tools on the given FastMCP instance."""
    generic.register(mcp)
    accounting.register(mcp)
    selling.register(mcp)
    buying.register(mcp)
    stock.register(mcp)
    hr.register(mcp)
    manufacturing.register(mcp)
    projects.register(mcp)
    assets.register(mcp)
