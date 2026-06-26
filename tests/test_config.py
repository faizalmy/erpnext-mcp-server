"""Integration tests for config.py — Settings class."""

import pytest
from src.config import Settings


class TestSettingsDefaults:
    """Verify default values for all Settings fields."""

    def test_timeout_default(self):
        s = Settings()
        assert s.timeout == 30.0

    def test_concise_descriptions_default(self):
        s = Settings()
        assert s.concise_descriptions is False

    def test_http_host_default(self):
        s = Settings()
        assert s.http_host == "127.0.0.1"

    def test_http_port_default(self):
        s = Settings()
        assert s.http_port == 3000

    def test_discovery_include_default(self):
        s = Settings()
        assert s.discovery_include == ""

    def test_discovery_exclude_default(self):
        s = Settings()
        assert s.discovery_exclude == ""

    def test_discovery_modules_default(self):
        s = Settings()
        assert s.discovery_modules == ""

    def test_max_response_chars_default(self):
        s = Settings()
        assert s.max_response_chars == 0

    def test_mcp_api_key_default(self):
        s = Settings()
        assert s.mcp_api_key == ""


class TestDiscoveryIncludeList:
    """Test discovery_include_list property parsing."""

    def test_include_list_normal(self):
        s = Settings(discovery_include="Customer,Item")
        assert s.discovery_include_list == ["Customer", "Item"]

    def test_include_list_with_spaces(self):
        s = Settings(discovery_include=" Customer , Item , Sales Invoice ")
        assert s.discovery_include_list == ["Customer", "Item", "Sales Invoice"]

    def test_include_list_empty(self):
        s = Settings(discovery_include="")
        assert s.discovery_include_list is None

    def test_include_list_single(self):
        s = Settings(discovery_include="Customer")
        assert s.discovery_include_list == ["Customer"]

    def test_include_list_filters_blanks(self):
        s = Settings(discovery_include="Customer,,Item,")
        assert s.discovery_include_list == ["Customer", "Item"]


class TestDiscoveryExcludeList:
    """Test discovery_exclude_list property parsing."""

    def test_exclude_list_normal(self):
        s = Settings(discovery_exclude="System Manager,Note")
        assert s.discovery_exclude_list == ["System Manager", "Note"]

    def test_exclude_list_empty(self):
        s = Settings(discovery_exclude="")
        assert s.discovery_exclude_list is None

    def test_exclude_list_with_spaces(self):
        s = Settings(discovery_exclude=" System Manager , Note ")
        assert s.discovery_exclude_list == ["System Manager", "Note"]


class TestDiscoveryModulesList:
    """Test discovery_modules_list property parsing."""

    def test_modules_list_normal(self):
        s = Settings(discovery_modules="Selling,Buying")
        assert s.discovery_modules_list == ["Selling", "Buying"]

    def test_modules_list_empty(self):
        s = Settings(discovery_modules="")
        assert s.discovery_modules_list is None

    def test_modules_list_with_spaces(self):
        s = Settings(discovery_modules=" Selling , Buying , Stock ")
        assert s.discovery_modules_list == ["Selling", "Buying", "Stock"]


class TestEnvOverride:
    """Test that env vars override defaults."""

    def test_timeout_override(self, monkeypatch):
        monkeypatch.setenv("TIMEOUT", "60")
        s = Settings()
        assert s.timeout == 60.0

    def test_http_port_override(self, monkeypatch):
        monkeypatch.setenv("HTTP_PORT", "8080")
        s = Settings()
        assert s.http_port == 8080

    def test_concise_descriptions_override(self, monkeypatch):
        monkeypatch.setenv("CONCISE_DESCRIPTIONS", "true")
        s = Settings()
        assert s.concise_descriptions is True

    def test_discovery_include_override(self, monkeypatch):
        monkeypatch.setenv("DISCOVERY_INCLUDE", "Sales Invoice,Purchase Invoice")
        s = Settings()
        assert s.discovery_include_list == ["Sales Invoice", "Purchase Invoice"]

    def test_max_response_chars_override(self, monkeypatch):
        monkeypatch.setenv("MAX_RESPONSE_CHARS", "50000")
        s = Settings()
        assert s.max_response_chars == 50000
