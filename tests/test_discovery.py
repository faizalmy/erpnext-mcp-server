"""Integration tests for discovery.py — schema generation, sanitization, cache, and DiscoveryEngine."""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch

from src.discovery import (
    _field_type_to_schema,
    _build_schema,
    _get_required_fields,
    _sanitize_json_schema,
    _load_cache,
    _save_cache,
    _get_cache_path,
    _get_cache_ttl,
    DiscoveryEngine,
    DEFAULT_DISCOVERY_INCLUDE,
)


# ═══════════════════════════════════════════════════════════════
# Field-type → JSON Schema
# ═══════════════════════════════════════════════════════════════

class TestFieldTypeToSchema:
    """Test _field_type_to_schema mapping."""

    def test_data_type(self):
        assert _field_type_to_schema({"fieldtype": "Data"}) == {"type": "string"}

    def test_int_type(self):
        assert _field_type_to_schema({"fieldtype": "Int"}) == {"type": "integer"}

    def test_float_type(self):
        assert _field_type_to_schema({"fieldtype": "Float"}) == {"type": "number"}

    def test_currency_type(self):
        assert _field_type_to_schema({"fieldtype": "Currency"}) == {"type": "number"}

    def test_check_type(self):
        assert _field_type_to_schema({"fieldtype": "Check"}) == {"type": "boolean"}

    def test_date_type(self):
        result = _field_type_to_schema({"fieldtype": "Date"})
        assert result == {"type": "string", "format": "date"}

    def test_datetime_type(self):
        result = _field_type_to_schema({"fieldtype": "Datetime"})
        assert result == {"type": "string", "format": "date-time"}

    def test_time_type(self):
        result = _field_type_to_schema({"fieldtype": "Time"})
        assert result == {"type": "string", "format": "time"}

    def test_small_text_type(self):
        assert _field_type_to_schema({"fieldtype": "Small Text"}) == {"type": "string"}

    def test_text_editor_type(self):
        assert _field_type_to_schema({"fieldtype": "Text Editor"}) == {"type": "string"}

    def test_select_with_options(self):
        field = {"fieldtype": "Select", "options": "Draft\nSubmitted\nCancelled"}
        result = _field_type_to_schema(field)
        assert result["type"] == "string"
        assert result["enum"] == ["Draft", "Submitted", "Cancelled"]

    def test_select_without_options(self):
        result = _field_type_to_schema({"fieldtype": "Select", "options": ""})
        assert result == {"type": "string"}
        assert "enum" not in result

    def test_link_with_target(self):
        field = {"fieldtype": "Link", "options": "Customer"}
        result = _field_type_to_schema(field)
        assert result["type"] == "string"
        assert "Customer" in result["description"]

    def test_link_without_target(self):
        result = _field_type_to_schema({"fieldtype": "Link", "options": ""})
        assert result == {"type": "string"}

    def test_table_type(self):
        field = {"fieldtype": "Table", "options": "Sales Invoice Item"}
        result = _field_type_to_schema(field)
        assert result["type"] == "array"
        assert result["items"] == {"type": "object"}
        assert "Sales Invoice Item" in result["description"]

    def test_unknown_type_fallback(self):
        result = _field_type_to_schema({"fieldtype": "SomeNewType"})
        assert result == {"type": "string"}

    def test_percent_type(self):
        assert _field_type_to_schema({"fieldtype": "Percent"}) == {"type": "number"}

    def test_rating_type(self):
        assert _field_type_to_schema({"fieldtype": "Rating"}) == {"type": "number"}

    def test_long_int_type(self):
        assert _field_type_to_schema({"fieldtype": "Long Int"}) == {"type": "integer"}

    def test_duration_type(self):
        assert _field_type_to_schema({"fieldtype": "Duration"}) == {"type": "integer"}


# ═══════════════════════════════════════════════════════════════
# Build schema from field list
# ═══════════════════════════════════════════════════════════════

class TestBuildSchema:
    """Test _build_schema conversion."""

    def test_basic_fields(self):
        fields = [
            {"fieldname": "customer_name", "fieldtype": "Data", "label": "Customer Name"},
            {"fieldname": "credit_limit", "fieldtype": "Currency", "label": "Credit Limit"},
        ]
        schema = _build_schema(fields)
        assert "customer_name" in schema
        assert "credit_limit" in schema
        assert schema["customer_name"]["type"] == "string"
        assert schema["credit_limit"]["type"] == "number"

    def test_skips_hidden_fields(self):
        fields = [
            {"fieldname": "visible_field", "fieldtype": "Data", "label": "Visible"},
            {"fieldname": "hidden_field", "fieldtype": "Data", "label": "Hidden", "hidden": 1},
        ]
        schema = _build_schema(fields)
        assert "visible_field" in schema
        assert "hidden_field" not in schema

    def test_skips_section_break(self):
        fields = [
            {"fieldname": "section_break_1", "fieldtype": "Section Break", "label": "Section"},
            {"fieldname": "real_field", "fieldtype": "Data", "label": "Real"},
        ]
        schema = _build_schema(fields)
        assert "section_break_1" not in schema
        assert "real_field" in schema

    def test_skips_column_break(self):
        fields = [
            {"fieldname": "col_break", "fieldtype": "Column Break"},
        ]
        schema = _build_schema(fields)
        assert "col_break" not in schema

    def test_skips_tab_break(self):
        fields = [
            {"fieldname": "tab1", "fieldtype": "Tab Break"},
        ]
        schema = _build_schema(fields)
        assert "tab1" not in schema

    def test_skips_html(self):
        fields = [
            {"fieldname": "html_block", "fieldtype": "HTML"},
        ]
        schema = _build_schema(fields)
        assert "html_block" not in schema

    def test_skips_heading(self):
        fields = [
            {"fieldname": "heading1", "fieldtype": "Heading"},
        ]
        schema = _build_schema(fields)
        assert "heading1" not in schema

    def test_includes_label_in_description(self):
        fields = [
            {"fieldname": "customer", "fieldtype": "Link", "options": "Customer",
             "label": "Customer Name"},
        ]
        schema = _build_schema(fields)
        assert "Customer Name" in schema["customer"]["description"]

    def test_skips_empty_fieldname(self):
        fields = [
            {"fieldname": "", "fieldtype": "Data"},
            {"fieldname": "valid", "fieldtype": "Data", "label": "Valid"},
        ]
        schema = _build_schema(fields)
        assert "" not in schema
        assert "valid" in schema


# ═══════════════════════════════════════════════════════════════
# Required fields
# ═══════════════════════════════════════════════════════════════

class TestGetRequiredFields:
    """Test _get_required_fields extraction."""

    def test_returns_required_fields(self):
        meta = {
            "fields": [
                {"fieldname": "customer", "reqd": 1},
                {"fieldname": "posting_date", "reqd": 1},
                {"fieldname": "optional_field", "reqd": 0},
            ]
        }
        schema_keys = {"customer", "posting_date", "optional_field"}
        result = _get_required_fields(meta, schema_keys)
        assert "customer" in result
        assert "posting_date" in result
        assert "optional_field" not in result

    def test_excludes_fields_not_in_schema(self):
        meta = {
            "fields": [
                {"fieldname": "visible_req", "reqd": 1},
                {"fieldname": "hidden_req", "reqd": 1},
            ]
        }
        schema_keys = {"visible_req"}
        result = _get_required_fields(meta, schema_keys)
        assert "visible_req" in result
        assert "hidden_req" not in result

    def test_empty_meta(self):
        assert _get_required_fields({}, set()) == []

    def test_no_required_fields(self):
        meta = {"fields": [{"fieldname": "x", "reqd": 0}]}
        assert _get_required_fields(meta, {"x"}) == []


# ═══════════════════════════════════════════════════════════════
# JSON Schema sanitizer
# ═══════════════════════════════════════════════════════════════

class TestSanitizeJsonSchema:
    """Test _sanitize_json_schema cleaning."""

    def test_strips_title(self):
        schema = {"type": "string", "title": "Foo"}
        result = _sanitize_json_schema(schema)
        assert "title" not in result

    def test_strips_additional_properties(self):
        schema = {"type": "object", "additionalProperties": False}
        result = _sanitize_json_schema(schema)
        assert "additionalProperties" not in result

    def test_strips_schema_id(self):
        schema = {"$schema": "http://json-schema.org/draft-07/schema#",
                   "$id": "test", "type": "string"}
        result = _sanitize_json_schema(schema)
        assert "$schema" not in result
        assert "$id" not in result

    def test_anyof_null_collapsed(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        result = _sanitize_json_schema(schema)
        assert result == {"type": "string"}

    def test_oneof_null_collapsed(self):
        schema = {"oneOf": [{"type": "integer"}, {"type": "null"}]}
        result = _sanitize_json_schema(schema)
        assert result == {"type": "integer"}

    def test_anyof_multiple_kept(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        result = _sanitize_json_schema(schema)
        assert "anyOf" in result
        assert len(result["anyOf"]) == 2

    def test_empty_items_replaced(self):
        schema = {"type": "array", "items": {}}
        result = _sanitize_json_schema(schema)
        assert result["items"] == {"type": "string"}

    def test_array_without_items_gets_default(self):
        schema = {"type": "array"}
        result = _sanitize_json_schema(schema)
        assert result["items"] == {"type": "string"}

    def test_recurses_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "title": "Name"},
                "nested": {
                    "type": "object",
                    "properties": {
                        "inner": {"type": "string", "title": "Inner"},
                    },
                },
            },
        }
        result = _sanitize_json_schema(schema)
        assert "title" not in result["properties"]["name"]
        assert "title" not in result["properties"]["nested"]["properties"]["inner"]

    def test_recurses_items(self):
        schema = {
            "type": "array",
            "items": {"type": "object", "title": "Item"},
        }
        result = _sanitize_json_schema(schema)
        assert "title" not in result["items"]

    def test_non_dict_passthrough(self):
        assert _sanitize_json_schema("not a dict") == "not a dict"
        assert _sanitize_json_schema(42) == 42
        assert _sanitize_json_schema(None) is None


# ═══════════════════════════════════════════════════════════════
# Cache
# ═══════════════════════════════════════════════════════════════

class TestCache:
    """Test cache save/load/expiry."""

    def test_save_and_load_roundtrip(self, tmp_path):
        cache_file = tmp_path / "test_cache.json"
        data = {"doctypes": ["Customer", "Item"], "metadata": {"Customer": {"fields": []}}}
        _save_cache(cache_file, data)
        loaded = _load_cache(cache_file)
        assert loaded is not None
        assert loaded["doctypes"] == ["Customer", "Item"]
        assert loaded["metadata"]["Customer"] == {"fields": []}
        assert "_cached_at" in loaded

    def test_load_expired_cache(self, tmp_path):
        cache_file = tmp_path / "expired.json"
        data = {"doctypes": ["Customer"], "_cached_at": time.time() - 200000}
        cache_file.write_text(json.dumps(data))
        with patch("src.discovery_cache.get_cache_ttl", return_value=86400):
            result = _load_cache(cache_file)
        assert result is None

    def test_load_nonexistent_file(self, tmp_path):
        result = _load_cache(tmp_path / "nonexistent.json")
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        cache_file = tmp_path / "bad.json"
        cache_file.write_text("not json{{{")
        result = _load_cache(cache_file)
        assert result is None

    def test_save_creates_parent_dirs(self, tmp_path):
        cache_file = tmp_path / "sub" / "dir" / "cache.json"
        _save_cache(cache_file, {"test": True})
        assert cache_file.exists()
        loaded = _load_cache(cache_file)
        assert loaded["test"] is True

    def test_ttl_zero_skips_expiry_check(self, tmp_path):
        cache_file = tmp_path / "ttl0.json"
        data = {"doctypes": ["X"], "_cached_at": time.time() - 999999}
        cache_file.write_text(json.dumps(data))
        with patch("src.discovery_cache.get_cache_ttl", return_value=0):
            result = _load_cache(cache_file)
        assert result is not None


# ═══════════════════════════════════════════════════════════════
# Pydantic model generation
# ═══════════════════════════════════════════════════════════════

class TestSchemaToPydanticModel:
    """Test _schema_to_pydantic_model from DiscoveryEngine."""

    def test_creates_valid_model(self):
        engine = DiscoveryEngine()
        schema = {
            "customer_name": {"type": "string", "description": "Name"},
            "credit_limit": {"type": "number", "description": "Limit"},
        }
        model = engine._schema_to_pydantic_model("TestDT", schema, required=["customer_name"])
        assert model.__name__ == "TestDTData"
        # Verify it can be instantiated
        instance = model(customer_name="Acme", credit_limit=1000.0)
        assert instance.customer_name == "Acme"

    def test_required_fields_have_no_default(self):
        engine = DiscoveryEngine()
        schema = {
            "name_field": {"type": "string", "description": "Name"},
            "opt_field": {"type": "string", "description": "Optional"},
        }
        model = engine._schema_to_pydantic_model("TestDT", schema, required=["name_field"])
        fields = model.model_fields
        assert fields["name_field"].is_required()
        assert not fields["opt_field"].is_required()

    def test_optional_fields_default_to_none(self):
        engine = DiscoveryEngine()
        schema = {
            "req": {"type": "string", "description": "Required"},
            "opt": {"type": "string", "description": "Optional"},
        }
        model = engine._schema_to_pydantic_model("TestDT", schema, required=["req"])
        instance = model(req="hello")
        assert instance.opt is None

    def test_enum_fields_in_schema_extra(self):
        engine = DiscoveryEngine()
        schema = {
            "status": {"type": "string", "description": "Status",
                        "enum": ["Draft", "Submitted", "Cancelled"]},
        }
        model = engine._schema_to_pydantic_model("TestDT", schema, required=["status"])
        field_info = model.model_fields["status"]
        assert field_info.json_schema_extra is not None
        assert field_info.json_schema_extra["enum"] == ["Draft", "Submitted", "Cancelled"]

    def test_type_mapping(self):
        engine = DiscoveryEngine()
        schema = {
            "str_field": {"type": "string", "description": ""},
            "int_field": {"type": "integer", "description": ""},
            "float_field": {"type": "number", "description": ""},
            "bool_field": {"type": "boolean", "description": ""},
            "list_field": {"type": "array", "description": ""},
            "dict_field": {"type": "object", "description": ""},
        }
        model = engine._schema_to_pydantic_model("TestDT", schema, required=[])
        instance = model(str_field="a", int_field=1, float_field=1.5,
                         bool_field=True, list_field=[1], dict_field={"k": "v"})
        assert isinstance(instance.str_field, str)
        assert isinstance(instance.int_field, int)


# ═══════════════════════════════════════════════════════════════
# DiscoveryEngine — discover and register (mocked ERPNext)
# ═══════════════════════════════════════════════════════════════

class TestDiscoveryEngineDiscover:
    """Test DiscoveryEngine.discover with mocked ERPNext API."""

    def _mock_erpnext_list(self, doctypes_data):
        """Create a mock that returns doctypes_data for list_documents."""
        from unittest.mock import MagicMock, patch
        mock_client = MagicMock()
        mock_client.list_documents.return_value = {"data": doctypes_data}
        return mock_client

    def test_discover_returns_doctypes(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "Item", "module": "Stock", "issingle": 0, "istable": 0},
        ])
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover(include=["Customer", "Item"])
        assert "Customer" in result
        assert "Item" in result

    def test_discover_with_include_filter(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "Item", "module": "Stock", "issingle": 0, "istable": 0},
            {"name": "Supplier", "module": "Buying", "issingle": 0, "istable": 0},
        ])
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover(include=["Customer", "Item"])
        assert "Customer" in result
        assert "Item" in result
        assert "Supplier" not in result

    def test_discover_with_exclude_filter(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "Note", "module": "Core", "issingle": 0, "istable": 0},
        ])
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover(include=["Customer", "Note"], exclude=["Note"])
        assert "Customer" in result
        assert "Note" not in result

    def test_discover_skips_system_doctypes(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "DocType", "module": "Core", "issingle": 0, "istable": 0},
        ])
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover(include=["Customer", "DocType"])
        assert "Customer" in result
        assert "DocType" not in result

    def test_discover_skips_single_doctypes(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "System Settings", "module": "Core", "issingle": 1, "istable": 0},
        ])
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover(include=["Customer", "System Settings"])
        assert "Customer" in result
        assert "System Settings" not in result

    def test_discover_with_module_filter(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "Item", "module": "Stock", "issingle": 0, "istable": 0},
        ])
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover(include=["Customer", "Item"], modules=["Selling"])
        assert "Customer" in result
        assert "Item" not in result

    def test_discover_api_failure_returns_empty(self):
        engine = DiscoveryEngine()
        mock_client = self._mock_erpnext_list([])
        mock_client.list_documents.side_effect = Exception("Connection refused")
        with patch("src.discovery.erpnext", mock_client):
            result = engine.discover()
        assert result == []


class TestDiscoveryEngineRegisterTools:
    """Test DiscoveryEngine.register_tools with mocked metadata."""

    def test_register_tools_returns_count(self):
        engine = DiscoveryEngine()
        mock_meta = {
            "fields": [
                {"fieldname": "customer_name", "fieldtype": "Data", "label": "Name"},
            ]
        }
        from unittest.mock import MagicMock, patch
        mock_client = MagicMock()
        mock_client.list_documents.return_value = {
            "data": [{"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0}]
        }
        mock_client.call_method.return_value = mock_meta

        mcp = MagicMock()
        mcp._tool_manager._tools = {}

        def fake_tool(**kwargs):
            def decorator(fn):
                mcp._tool_manager._tools[kwargs.get("name", fn.__name__)] = fn
                return fn
            return decorator
        mcp.tool = fake_tool

        with patch("src.discovery.erpnext", mock_client), \
             patch("src.discovery._load_cache", return_value=None), \
             patch("src.discovery._save_cache"):
            count = engine.register_tools(mcp, include=["Customer"], force_refresh=True)

        assert count == 5  # list, get, create, update, delete

    def test_register_tools_creates_expected_tool_names(self):
        engine = DiscoveryEngine()
        mock_meta = {
            "fields": [
                {"fieldname": "customer_name", "fieldtype": "Data", "label": "Name"},
            ]
        }
        from unittest.mock import MagicMock, patch
        mock_client = MagicMock()
        mock_client.list_documents.return_value = {
            "data": [{"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0}]
        }
        mock_client.call_method.return_value = mock_meta

        registered = {}
        mcp = MagicMock()

        def fake_tool(**kwargs):
            def decorator(fn):
                registered[kwargs.get("name", fn.__name__)] = fn
                return fn
            return decorator
        mcp.tool = fake_tool

        with patch("src.discovery.erpnext", mock_client), \
             patch("src.discovery._load_cache", return_value=None), \
             patch("src.discovery._save_cache"):
            engine.register_tools(mcp, include=["Customer"], force_refresh=True)

        assert "list_Customer" in registered
        assert "get_Customer" in registered
        assert "create_Customer" in registered
        assert "update_Customer" in registered
        assert "delete_Customer" in registered


# ═══════════════════════════════════════════════════════════════
# Make functions — annotation correctness
# ═══════════════════════════════════════════════════════════════

class TestMakeFunctionsAnnotations:
    """Test that CRUD builders produce correct annotations."""

    def test_list_fn_readonly(self):
        engine = DiscoveryEngine()
        fn, config = engine._make_list_fn("Customer", ["name", "customer_name"])
        assert config["annotations"]["readOnlyHint"] is True
        assert config["annotations"]["destructiveHint"] is False
        assert config["name"] == "list_Customer"

    def test_get_fn_readonly(self):
        engine = DiscoveryEngine()
        fn, config = engine._make_get_fn("Customer")
        assert config["annotations"]["readOnlyHint"] is True
        assert config["name"] == "get_Customer"

    def test_create_fn_not_readonly(self):
        engine = DiscoveryEngine()
        schema = {"customer_name": {"type": "string", "description": "Name"}}
        fn, config = engine._make_create_fn("Customer", schema, ["customer_name"])
        assert config["annotations"]["readOnlyHint"] is False
        assert config["annotations"]["destructiveHint"] is False
        assert config["name"] == "create_Customer"

    def test_update_fn_not_readonly(self):
        engine = DiscoveryEngine()
        schema = {"customer_name": {"type": "string", "description": "Name"}}
        fn, config = engine._make_update_fn("Customer", schema)
        assert config["annotations"]["readOnlyHint"] is False
        assert config["name"] == "update_Customer"

    def test_delete_fn_destructive(self):
        engine = DiscoveryEngine()
        fn, config = engine._make_delete_fn("Customer")
        assert config["annotations"]["readOnlyHint"] is False
        assert config["annotations"]["destructiveHint"] is True
        assert config["name"] == "delete_Customer"
