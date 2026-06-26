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
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP
from pydantic import create_model, Field

from .config import settings
from .erpnext_client import erpnext, get_request_url

log = logging.getLogger(__name__)

# ── Field-type → JSON Schema lookup ───────────────────────────
_SIMPLE_TYPES: dict[str, dict] = {}
for _t in ("Int", "Long Int", "Duration"):
    _SIMPLE_TYPES[_t] = {"type": "integer"}
for _t in ("Float", "Percent", "Currency", "Rating"):
    _SIMPLE_TYPES[_t] = {"type": "number"}
_SIMPLE_TYPES["Check"] = {"type": "boolean"}
_SIMPLE_TYPES["Date"] = {"type": "string", "format": "date"}
_SIMPLE_TYPES["Datetime"] = {"type": "string", "format": "date-time"}
_SIMPLE_TYPES["Time"] = {"type": "string", "format": "time"}
for _t in ("Small Text", "Text", "Text Editor", "HTML Editor",
           "Markdown Editor", "Code", "JSON"):
    _SIMPLE_TYPES[_t] = {"type": "string"}

# ── Cache (delegated to discovery_cache module) ───────────────
from .discovery_cache import (
    DEFAULT_CACHE_DIR,
    DEFAULT_CACHE_FILE,
    DEFAULT_CACHE_TTL,
    get_cache_path,
    get_cache_ttl,
    load_cache,
    save_cache,
)


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

    if ft in _SIMPLE_TYPES:
        return _SIMPLE_TYPES[ft]

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


def _sanitize_json_schema(schema: dict) -> dict:
    """Strip fields DeepSeek rejects from JSON Schema."""
    if not isinstance(schema, dict):
        return schema

    # anyOf/oneOf with null branch -> take non-null branch
    for key in ("anyOf", "oneOf"):
        if key in schema:
            non_null = [v for v in schema[key] if v.get("type") != "null"]
            if len(non_null) == 1:
                return _sanitize_json_schema(non_null[0])
            schema[key] = [_sanitize_json_schema(v) for v in non_null]

    # Strip non-standard keys
    for k in ("title", "additionalProperties", "$schema", "$id"):
        schema.pop(k, None)

    # Empty items -> {type: "string"}
    if "items" in schema and not schema["items"]:
        schema["items"] = {"type": "string"}

    # Array without items -> add {type: "string"}
    if schema.get("type") == "array" and "items" not in schema:
        schema["items"] = {"type": "string"}

    # Recurse into properties
    if "properties" in schema:
        schema["properties"] = {
            k: _sanitize_json_schema(v)
            for k, v in schema["properties"].items()
        }
    # Recurse into items
    if "items" in schema:
        schema["items"] = _sanitize_json_schema(schema["items"])

    return schema


class DiscoveryEngine:
    """Fetches ERPNext DocTypes and generates CRUD MCP tools."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._doctypes: list[str] = []

    def discover(self, include: list[str] | None = None,
                 exclude: list[str] | None = None,
                 modules: list[str] | None = None) -> list[str]:
        """Fetch available DocTypes from ERPNext.

        Args:
            include: Only discover these DocTypes (None = use defaults)
            exclude: Skip these DocTypes (None = no exclusions)
            modules: Only discover DocTypes from these ERPNext modules (None = no filter)

        Returns:
            List of discovered DocType names.
        """
        # Default to core business DocTypes unless user overrides
        if include is None:
            include = DEFAULT_DISCOVERY_INCLUDE
        try:
            filters = [["DocType", "istable", "!=", 1]]
            result = erpnext.list_documents(
                "DocType",
                fields=["name", "module", "issingle", "istable", "custom"],
                filters=filters,
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
            # Module filter
            if modules and item.get("module") not in modules:
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
        if settings.concise_descriptions:
            desc = f"List {doctype} records."
        else:
            desc = (f"List {doctype} records. "
                    f"Available fields: {', '.join(schema_props[:15])}")
        config = {
            "name": f"list_{safe}",
            "description": desc,
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
            "parameters": _sanitize_json_schema({
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20,
                              "description": "Max records to return"},
                    "filters": {"type": "array",
                                "description": 'ERPNext filters: [["DocType","field","op","value"]]'},
                    "fields": {"type": "array", "items": {"type": "string"},
                               "description": "Fields to return (default: first 15)"},
                },
            }),
        }
        return fn, config

    def _make_get_fn(self, doctype: str) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(name: str) -> dict:
            return erpnext.get_document(doctype, name)
        config = {
            "name": f"get_{safe}",
            "description": f"Get a single {doctype} by name/ID.",
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
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

    def _schema_to_pydantic_model(self, doctype: str, schema: dict,
                                   required: list[str]) -> type:
        """Create a dynamic Pydantic model from ERPNext field schema.

        This gives FastMCP proper type hints so it generates detailed
        JSON Schema with field descriptions, types, and required markers.
        """
        field_defs: dict[str, Any] = {}
        required_set = set(required)

        for field_name, field_schema in schema.items():
            ftype = field_schema.get("type", "string")
            desc = field_schema.get("description", "")
            enum_vals = field_schema.get("enum")

            # Map JSON Schema type to Python type
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            py_type = type_map.get(ftype, str)

            if enum_vals:
                # For Select fields with known options
                field_defs[field_name] = (
                    py_type,
                    Field(description=desc, json_schema_extra={"enum": enum_vals})
                )
            elif field_name in required_set:
                field_defs[field_name] = (
                    py_type,
                    Field(description=desc)
                )
            else:
                # Optional field — use None default
                field_defs[field_name] = (
                    py_type | None,
                    Field(default=None, description=desc)
                )

        model_name = f"{doctype.replace(' ', '')}Data"
        return create_model(model_name, **field_defs)

    def _make_create_fn(self, doctype: str, schema: dict,
                        required: list[str]) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        DataModel = self._schema_to_pydantic_model(doctype, schema, required)

        def fn(data: DataModel) -> dict:  # type: ignore[type-arg]
            return erpnext.create_document(doctype, data.model_dump(exclude_none=True))

        fn.__name__ = f"create_{safe}"
        fn.__qualname__ = f"create_{safe}"
        if settings.concise_descriptions:
            desc = f"Create a new {doctype}."
            if required:
                desc += f" Required: {', '.join(required)}."
        else:
            desc = f"Create a new {doctype}."
            if required:
                desc += f" Required: {', '.join(required)}."
            desc += f" Fields: {', '.join(list(schema.keys())[:20])}"
        raw_schema = DataModel.model_json_schema()
        clean_params = _sanitize_json_schema(raw_schema)
        config = {
            "name": f"create_{safe}",
            "description": desc,
            "annotations": {"readOnlyHint": False, "destructiveHint": False},
            "parameters": clean_params,
        }
        return fn, config

    def _make_update_fn(self, doctype: str, schema: dict) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        # For update, all fields are optional (partial update)
        DataModel = self._schema_to_pydantic_model(doctype, schema, required=[])

        def fn(name: str, data: DataModel) -> dict:  # type: ignore[type-arg]
            return erpnext.update_document(doctype, name, data.model_dump(exclude_none=True))

        fn.__name__ = f"update_{safe}"
        fn.__qualname__ = f"update_{safe}"
        raw_schema = DataModel.model_json_schema()
        clean_params = _sanitize_json_schema(raw_schema)
        config = {
            "name": f"update_{safe}",
            "description": f"Update an existing {doctype} (partial update).",
            "annotations": {"readOnlyHint": False, "destructiveHint": False},
            "parameters": clean_params,
        }
        return fn, config

    def _make_delete_fn(self, doctype: str) -> tuple[Callable, dict]:
        safe = doctype.replace(" ", "_")
        def fn(name: str) -> dict:
            return erpnext.delete_document(doctype, name)
        config = {
            "name": f"delete_{safe}",
            "description": f"Delete a {doctype} permanently.",
            "annotations": {"readOnlyHint": False, "destructiveHint": True},
            "parameters": _sanitize_json_schema({
                "type": "object",
                "properties": {
                    "name": {"type": "string",
                             "description": f"The {doctype} name or ID to delete"},
                },
                "required": ["name"],
            }),
        }
        return fn, config

    def register_tools(self, mcp: FastMCP,
                       include: list[str] | None = None,
                       exclude: list[str] | None = None,
                       modules: list[str] | None = None,
                       force_refresh: bool = False) -> int:
        """Discover DocTypes and register CRUD tools on the MCP server.

        Uses file cache when available. Set force_refresh=True or
        ERPNEXT_CACHE_TTL=0 to bypass cache.

        Returns the number of tools registered.
        """
        cache_path = get_cache_path()
        cached = None if force_refresh else load_cache(cache_path)

        if cached:
            # Load from cache — instant startup
            self._doctypes = cached.get("doctypes", [])
            self._cache = cached.get("metadata", {})
            log.info("Loaded %d DocTypes + %d metadata entries from cache (%s)",
                     len(self._doctypes), len(self._cache), cache_path)
        else:
            # Fresh fetch from ERPNext
            doctypes = self.discover(include=include, exclude=exclude, modules=modules)
            log.info("Fetching metadata for %d DocTypes...", len(doctypes))
            for dt in doctypes:
                self.get_meta(dt)

            # Save to cache
            save_cache(cache_path, {
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
                    mcp.tool(
                        name=config["name"],
                        description=config["description"],
                        annotations=config.get("annotations"),
                        parameters=config.get("parameters"),
                    )(fn)
                    tool_count += 1
                except Exception as e:
                    log.warning("Failed to register %s: %s",
                                config["name"], e)

        log.info("Registered %d auto-discovered CRUD tools", tool_count)
        return tool_count


# Singleton
discovery = DiscoveryEngine()
