"""Auto-discovery engine for ERPNext DocTypes.

Fetches DocType metadata from ERPNext at startup and generates
CRUD MCP tools dynamically. No hardcoded tool definitions —
the server adapts to whatever DocTypes exist in the connected instance.

Metadata is cached to disk (default: .cache/doctypes.json) so subsequent
startups are instant. Use --refresh or set ERPNEXT_CACHE_TTL=0 to force
re-fetch from ERPNext.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from .erpnext_client import erpnext

log = logging.getLogger(__name__)

# ── Cache ─────────────────────────────────────────────────────

DEFAULT_CACHE_DIR = ".cache"
DEFAULT_CACHE_FILE = "doctypes.json"
DEFAULT_CACHE_TTL = 86400  # 24 hours


def _get_cache_path() -> Path:
    """Resolve cache file path from env or default."""
    cache_dir = os.environ.get("ERPNEXT_CACHE_DIR", DEFAULT_CACHE_DIR)
    cache_file = os.environ.get("ERPNEXT_CACHE_FILE", DEFAULT_CACHE_FILE)
    return Path(cache_dir) / cache_file


def _get_cache_ttl() -> int:
    """Cache TTL in seconds. 0 = always refresh."""
    return int(os.environ.get("ERPNEXT_CACHE_TTL", str(DEFAULT_CACHE_TTL)))


def _load_cache(path: Path) -> dict | None:
    """Load cached metadata if valid and fresh."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = data.get("_cached_at", 0)
        ttl = _get_cache_ttl()
        if ttl > 0 and (time.time() - cached_at) > ttl:
            log.info("Cache expired (%.0fh old, TTL=%dh)", (time.time() - cached_at) / 3600, ttl / 3600)
            return None
        return data
    except (json.JSONDecodeError, KeyError) as e:
        log.warning("Invalid cache file, will re-fetch: %s", e)
        return None


def _save_cache(path: Path, data: dict) -> None:
    """Save metadata to cache file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = time.time()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        log.info("Cache saved to %s", path)
    except Exception as e:
        log.warning("Could not save cache: %s", e)


# Skip these — they're internal to Frappe/ERPNext framework
SYSTEM_DOCTYPES = frozenset({
    "DocType", "DocField", "DocPerm", "DocAction", "DocType Action",
    "DocType Layout", "DocType Link", "Custom Field", "Customize Form",
    "Property Setter", "Server Script", "Client Script",
    "Print Format", "Print Style", "Letter Head",
    "Workflow", "Workflow State", "Workflow Action",
    "Role", "Role Profile", "User Permission",
    "Comment", "Version", "Activity Log", "Access Log",
    "Error Log", "Scheduled Job Type", "Scheduler Log",
    "System Settings", "Email Domain", "Email Account",
    "Auto Email Report", "Notification",
    "Data Import", "Data Export", "Data Import Log",
    "Module Def", "Page", "Report", "Dashboard", "Dashboard Chart",
    "Workspace", "Onboarding Step", "Module Onboarding",
    "Deleted Document", "Prepared Report", "Integration Request",
    "OAuth Bearer Token", "OAuth Client", "OAuth Provider",
    "Connected App", "Token Cache",
    "Patch Log", "Installed Applications",
    "File", "Communication", "ToDo", "Event",
    "Note", "SMS Log", "Assignment Rule",
})


# These are always discovered — the core business DocTypes.
# Users can extend via ERPNEXT_DISCOVERY_INCLUDE env var.
DEFAULT_DISCOVERY_INCLUDE = [
    # Accounting
    "Account", "Journal Entry", "Payment Entry",
    "Sales Invoice", "Purchase Invoice",
    "Pricing Rule", "Tax Rule",
    # Selling
    "Customer", "Lead", "Opportunity", "Quotation", "Sales Order",
    # Buying
    "Supplier", "Purchase Order", "Purchase Receipt", "Material Request",
    "Supplier Quotation",
    # Stock
    "Item", "Stock Entry", "Delivery Note", "Batch", "Serial No",
    "Warehouse", "Item Group", "Brand",
    # HR
    "Employee", "Department", "Leave Application", "Leave Allocation",
    "Attendance", "Expense Claim", "Salary Slip", "Payroll Entry",
    # Manufacturing
    "Work Order", "BOM", "Production Plan", "Job Card",
    # Projects
    "Project", "Task", "Timesheet",
    # Assets
    "Asset", "Asset Category", "Asset Movement",
    # CRM
    "Campaign", "Email Campaign",
    # Misc
    "Company", "Currency Exchange", "Terms and Conditions",
    "Address", "Contact", "Note",
]


def _field_type_to_schema(field: dict) -> dict[str, Any]:
    """Map ERPNext field type to JSON Schema type."""
    ft = field.get("fieldtype", "Data")

    if ft in ("Int", "Long Int", "Duration"):
        return {"type": "integer"}
    if ft in ("Float", "Percent", "Currency", "Rating"):
        return {"type": "number"}
    if ft == "Check":
        return {"type": "boolean"}
    if ft in ("Date", "Datetime", "Time"):
        fmt = "date" if ft == "Date" else ("date-time" if ft == "Datetime" else "time")
        return {"type": "string", "format": fmt}
    if ft in ("Small Text", "Text", "Text Editor", "HTML Editor",
              "Markdown Editor", "Code", "JSON"):
        return {"type": "string"}
    if ft == "Select":
        s: dict[str, Any] = {"type": "string"}
        options = field.get("options", "")
        if options and not options.startswith("link:"):
            opts = [o.strip() for o in str(options).split("\n") if o.strip()]
            if opts:
                s["enum"] = opts
        return s
    if ft == "Link":
        target = field.get("options", "")
        s = {"type": "string"}
        if target:
            s["description"] = f"Must be a valid {target} name"
        return s
    if ft == "Table":
        child = field.get("options", "")
        return {"type": "array", "items": {"type": "object"},
                "description": f"Array of {child} rows"}

    return {"type": "string"}


def _build_schema(fields: list[dict]) -> dict[str, Any]:
    """Convert ERPNext field list to JSON Schema properties."""
    props = {}
    for f in fields:
        ft = f.get("fieldtype", "")
        fn = f.get("fieldname", "")
        if not fn or ft in ("Section Break", "Column Break", "Tab Break",
                            "Fold", "HTML", "Heading", "Table MultiSelect"):
            continue
        if f.get("hidden"):
            continue
        schema = _field_type_to_schema(f)
        label = f.get("label", "")
        if label and label != fn:
            desc = schema.get("description", "")
            schema["description"] = f"{label}" + (f". {desc}" if desc else "")
        props[fn] = schema
    return props


def _get_required_fields(meta: dict, schema_keys: set) -> list[str]:
    """Get required field names from DocType metadata."""
    return [
        f["fieldname"] for f in meta.get("fields", [])
        if f.get("reqd") and f["fieldname"] in schema_keys
    ]


class DiscoveryEngine:
    """Fetches ERPNext DocTypes and generates CRUD MCP tools."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._doctypes: list[str] = []

    def discover(self, include: list[str] | None = None,
                 exclude: list[str] | None = None) -> list[str]:
        """Fetch available DocTypes from ERPNext.

        Args:
            include: Only discover these DocTypes (None = use defaults)
            exclude: Skip these DocTypes (None = no exclusions)

        Returns:
            List of discovered DocType names.
        """
        # Default to core business DocTypes unless user overrides
        if include is None:
            include = DEFAULT_DISCOVERY_INCLUDE
        try:
            result = erpnext.list_documents(
                "DocType",
                fields=["name", "module", "issingle", "istable", "custom"],
                filters=[["DocType", "istable", "!=", 1]],
                limit=9999,
            )
        except Exception as e:
            log.error("Failed to discover DocTypes: %s", e)
            return []

        skip = SYSTEM_DOCTYPES | set(exclude or [])
        doctypes = []

        for item in result.get("data", []):
            name = item.get("name", "")
            if not name or name in skip:
                continue
            if item.get("issingle"):
                continue
            if include and name not in include:
                continue
            doctypes.append(name)

        self._doctypes = sorted(doctypes)
        log.info("Discovered %d DocTypes", len(self._doctypes))
        return self._doctypes

    def get_meta(self, doctype: str) -> dict | None:
        """Get DocType metadata (fields, naming, etc.)."""
        if doctype in self._cache:
            return self._cache[doctype]
        try:
            result = erpnext.call_method(
                "frappe.client.get",
                doctype="DocType",
                name=doctype,
            )
            meta = result if isinstance(result, dict) else {}
            self._cache[doctype] = meta
            return meta
        except Exception as e:
            log.warning("Could not get meta for %s: %s", doctype, e)
            return None

    def _make_list_fn(self, doctype: str, schema_props: list[str]) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(limit: int = 20, filters: list | None = None,
               fields: list[str] | None = None) -> dict:
            return erpnext.list_documents(
                doctype,
                fields=fields or schema_props or ["name"],
                filters=filters, limit=limit,
            )
        config = {
            "name": f"list_{safe}",
            "description": (f"List {doctype} records. "
                            f"Available fields: {', '.join(schema_props[:15])}"),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20,
                              "description": "Max records to return"},
                    "filters": {"type": "array",
                                "description": 'ERPNext filters: [["DocType","field","op","value"]]'},
                    "fields": {"type": "array", "items": {"type": "string"},
                               "description": "Fields to return (default: first 15)"},
                },
            },
        }
        return fn, config

    def _make_get_fn(self, doctype: str) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(name: str) -> dict:
            return erpnext.get_document(doctype, name)
        config = {
            "name": f"get_{safe}",
            "description": f"Get a single {doctype} by name/ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string",
                             "description": f"The {doctype} name or ID"},
                },
                "required": ["name"],
            },
        }
        return fn, config

    def _make_create_fn(self, doctype: str, schema: dict,
                        required: list[str]) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(data: dict) -> dict:
            return erpnext.create_document(doctype, data)
        desc = f"Create a new {doctype}."
        if required:
            desc += f" Required: {', '.join(required)}."
        desc += f" Fields: {', '.join(list(schema.keys())[:20])}"
        config = {
            "name": f"create_{safe}",
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object",
                             "description": f"Field values for the new {doctype}",
                             "properties": schema},
                },
                "required": ["data"],
            },
        }
        return fn, config

    def _make_update_fn(self, doctype: str, schema: dict) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(name: str, data: dict) -> dict:
            return erpnext.update_document(doctype, name, data)
        config = {
            "name": f"update_{safe}",
            "description": f"Update an existing {doctype} (partial update).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string",
                             "description": f"The {doctype} name or ID to update"},
                    "data": {"type": "object",
                             "description": "Fields to update (partial)",
                             "properties": schema},
                },
                "required": ["name", "data"],
            },
        }
        return fn, config

    def _make_delete_fn(self, doctype: str) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(name: str) -> dict:
            return erpnext.delete_document(doctype, name)
        config = {
            "name": f"delete_{safe}",
            "description": f"Delete a {doctype} permanently.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string",
                             "description": f"The {doctype} name or ID to delete"},
                },
                "required": ["name"],
            },
        }
        return fn, config

    def register_tools(self, mcp: FastMCP,
                       include: list[str] | None = None,
                       exclude: list[str] | None = None,
                       force_refresh: bool = False) -> int:
        """Discover DocTypes and register CRUD tools on the MCP server.

        Uses file cache when available. Set force_refresh=True or
        ERPNEXT_CACHE_TTL=0 to bypass cache.

        Returns the number of tools registered.
        """
        cache_path = _get_cache_path()
        cached = None if force_refresh else _load_cache(cache_path)

        if cached:
            # Load from cache — instant startup
            self._doctypes = cached.get("doctypes", [])
            self._cache = cached.get("metadata", {})
            log.info("Loaded %d DocTypes + %d metadata entries from cache (%s)",
                     len(self._doctypes), len(self._cache), cache_path)
        else:
            # Fresh fetch from ERPNext
            doctypes = self.discover(include=include, exclude=exclude)
            log.info("Fetching metadata for %d DocTypes...", len(doctypes))
            for dt in doctypes:
                self.get_meta(dt)

            # Save to cache
            _save_cache(cache_path, {
                "doctypes": self._doctypes,
                "metadata": self._cache,
            })

        # Register tools from in-memory data
        tool_count = 0
        for dt in self._doctypes:
            meta = self._cache.get(dt) or self.get_meta(dt)
            if not meta:
                continue

            schema = _build_schema(meta.get("fields", []))
            schema_props = list(schema.keys())
            required = _get_required_fields(meta, set(schema.keys()))

            builders = [
                self._make_list_fn(dt, schema_props),
                self._make_get_fn(dt),
                self._make_create_fn(dt, schema, required),
                self._make_update_fn(dt, schema),
                self._make_delete_fn(dt),
            ]

            for fn, config in builders:
                try:
                    mcp.tool(name=config["name"],
                             description=config["description"])(fn)
                    tool_count += 1
                except Exception as e:
                    log.warning("Failed to register %s: %s",
                                config["name"], e)

        log.info("Registered %d auto-discovered CRUD tools", tool_count)
        return tool_count


# Singleton
discovery = DiscoveryEngine()
