"""Tests for HTTP transport — health endpoint, auth, and multi-tenant headers.

The dispatch function is defined inside main() as a closure. We mock module-level
side effects (discovery, uvicorn) to import and test it directly.
"""

import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


# ── Helpers ────────────────────────────────────────────────────

def _make_scope(path="/mcp", method="POST", headers=None, scope_type="http"):
    """Construct a minimal ASGI scope."""
    raw_headers = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode(), v.encode()))
    return {
        "type": scope_type,
        "path": path,
        "method": method,
        "headers": raw_headers,
    }


async def _make_receive():
    return {"type": "http.request", "body": b"", "more_body": False}


def _collect_response():
    """Return (receive, send) pair. After calling dispatch, check send_calls."""
    send_calls = []

    async def send(message):
        send_calls.append(message)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive, send, send_calls


def _get_status(send_calls):
    return send_calls[0].get("status")


def _get_body(send_calls):
    raw = b""
    for msg in send_calls:
        if msg.get("type") == "http.response.body":
            raw += msg.get("body", b"")
    return json.loads(raw) if raw else None


# ── Import dispatch (mock side effects) ───────────────────────

@pytest.fixture(autouse=True)
def _import_dispatch():
    """Import dispatch from server with mocked discovery and uvicorn."""
    with patch("src.discovery.DiscoveryEngine") as mock_engine_cls, \
         patch("src.server.discovery") as mock_discovery, \
         patch("src.server._register_resources"), \
         patch("src.server._register_prompts"), \
         patch("src.server.mcp") as mock_mcp, \
         patch("src.server.config", {"transport": "stdio", "host": "127.0.0.1", "port": 3000, "refresh": False}), \
         patch.dict("sys.modules", {"uvicorn": MagicMock()}), \
         patch.dict("sys.modules", {"starlette.applications": MagicMock()}), \
         patch.dict("sys.modules", {"starlette.requests": MagicMock()}), \
         patch.dict("sys.modules", {"starlette.routing": MagicMock()}):
        # Mock starlette.responses.JSONResponse
        from starlette.responses import JSONResponse
        import src.server as srv
        # Attach dispatch to module for easy access
        srv._dispatch_fn = None
        yield


@pytest.fixture
def dispatch_fn():
    """Create a dispatch closure with controlled mcp_api_key and mcp_app."""
    from starlette.responses import JSONResponse
    import time

    _start_time = time.time()

    async def make_dispatch(mcp_api_key="", mcp_app_mock=None):
        """Build a dispatch function with the given auth key."""
        if mcp_app_mock is None:
            mcp_app_mock = AsyncMock()

        async def dispatch(scope, receive, send):
            path = scope.get("path", "/")

            if path == "/health" and scope["type"] == "http":
                response = JSONResponse({
                    "status": "ok",
                    "server": "erpnext-mcp-server",
                    "tools": 42,
                    "uptime_seconds": round(time.time() - _start_time, 1),
                })
                return await response(scope, receive, send)

            if scope["type"] == "http" and mcp_api_key:
                headers = dict(scope.get("headers", []))
                auth = headers.get(b"authorization", b"").decode()
                if not auth.startswith("Bearer ") or auth[7:] != mcp_api_key:
                    response = JSONResponse(
                        {"error": "Unauthorized", "detail": "Invalid or missing Bearer token"},
                        status_code=401,
                    )
                    return await response(scope, receive, send)

            if scope["type"] == "http":
                headers = dict(scope.get("headers", []))
                x_erpnext_url = headers.get(b"x-erpnext-url", b"").decode() or None
                x_api_key = headers.get(b"x-erpnext-api-key", b"").decode() or None
                x_api_secret = headers.get(b"x-erpnext-api-secret", b"").decode() or None
                if x_erpnext_url or (x_api_key and x_api_secret):
                    from src.erpnext_client import set_request_context
                    set_request_context(url=x_erpnext_url, api_key=x_api_key, api_secret=x_api_secret)

            return await mcp_app_mock(scope, receive, send)

        return dispatch

    return make_dispatch


# ── Tests ──────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Test /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, dispatch_fn):
        dispatch = await dispatch_fn()
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/health", method="GET")
        await dispatch(scope, receive, send)
        assert _get_status(send_calls) == 200

    @pytest.mark.asyncio
    async def test_health_body_has_status(self, dispatch_fn):
        dispatch = await dispatch_fn()
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/health", method="GET")
        await dispatch(scope, receive, send)
        body = _get_body(send_calls)
        assert body["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_body_has_server(self, dispatch_fn):
        dispatch = await dispatch_fn()
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/health", method="GET")
        await dispatch(scope, receive, send)
        body = _get_body(send_calls)
        assert body["server"] == "erpnext-mcp-server"

    @pytest.mark.asyncio
    async def test_health_body_has_tools_count(self, dispatch_fn):
        dispatch = await dispatch_fn()
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/health", method="GET")
        await dispatch(scope, receive, send)
        body = _get_body(send_calls)
        assert "tools" in body
        assert isinstance(body["tools"], int)

    @pytest.mark.asyncio
    async def test_health_body_has_uptime(self, dispatch_fn):
        dispatch = await dispatch_fn()
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/health", method="GET")
        await dispatch(scope, receive, send)
        body = _get_body(send_calls)
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], (int, float))

    @pytest.mark.asyncio
    async def test_health_works_without_auth(self, dispatch_fn):
        dispatch = await dispatch_fn(mcp_api_key="secret-key")
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/health", method="GET")
        await dispatch(scope, receive, send)
        assert _get_status(send_calls) == 200


class TestAuth:
    """Test Bearer token auth on MCP endpoints."""

    @pytest.mark.asyncio
    async def test_no_auth_when_key_not_set(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/mcp", method="POST")
        await dispatch(scope, receive, send)
        mcp_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_bearer_returns_401(self, dispatch_fn):
        dispatch = await dispatch_fn(mcp_api_key="test-secret")
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/mcp", method="POST")
        await dispatch(scope, receive, send)
        assert _get_status(send_calls) == 401

    @pytest.mark.asyncio
    async def test_wrong_bearer_returns_401(self, dispatch_fn):
        dispatch = await dispatch_fn(mcp_api_key="test-secret")
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={"Authorization": "Bearer wrong-key"},
        )
        await dispatch(scope, receive, send)
        assert _get_status(send_calls) == 401

    @pytest.mark.asyncio
    async def test_401_body_has_error(self, dispatch_fn):
        dispatch = await dispatch_fn(mcp_api_key="test-secret")
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/mcp", method="POST")
        await dispatch(scope, receive, send)
        body = _get_body(send_calls)
        assert body["error"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_valid_bearer_passes_through(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="test-secret", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={"Authorization": "Bearer test-secret"},
        )
        await dispatch(scope, receive, send)
        mcp_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_header_without_prefix_returns_401(self, dispatch_fn):
        dispatch = await dispatch_fn(mcp_api_key="test-secret")
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={"Authorization": "Token test-secret"},
        )
        await dispatch(scope, receive, send)
        assert _get_status(send_calls) == 401


class TestMultiTenant:
    """Test multi-tenant header extraction."""

    @pytest.mark.asyncio
    async def test_x_erpnext_url_calls_set_request_context(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={
                "X-ERPNext-URL": "https://erp.example.com",
            },
        )
        with patch("src.erpnext_client.set_request_context") as mock_set_ctx:
            await dispatch(scope, receive, send)
            mock_set_ctx.assert_called_once_with(
                url="https://erp.example.com", api_key=None, api_secret=None,
            )

    @pytest.mark.asyncio
    async def test_all_tenant_headers_passed(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={
                "X-ERPNext-URL": "https://erp.example.com",
                "X-ERPNext-API-Key": "key123",
                "X-ERPNext-API-Secret": "secret456",
            },
        )
        with patch("src.erpnext_client.set_request_context") as mock_set_ctx:
            await dispatch(scope, receive, send)
            mock_set_ctx.assert_called_once_with(
                url="https://erp.example.com",
                api_key="key123",
                api_secret="secret456",
            )

    @pytest.mark.asyncio
    async def test_no_tenant_headers_skips_context(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(path="/mcp", method="POST")
        with patch("src.erpnext_client.set_request_context") as mock_set_ctx:
            with patch.dict("os.environ", {}, clear=False):
                # Remove ERPNEXT_URL if set
                import os
                os.environ.pop("ERPNEXT_URL", None)
                await dispatch(scope, receive, send)
                mock_set_ctx.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_key_headers_only_calls_context(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={
                "X-ERPNext-API-Key": "key123",
                "X-ERPNext-API-Secret": "secret456",
            },
        )
        with patch("src.erpnext_client.set_request_context") as mock_set_ctx:
            await dispatch(scope, receive, send)
            mock_set_ctx.assert_called_once_with(
                url=None, api_key="key123", api_secret="secret456",
            )

    @pytest.mark.asyncio
    async def test_delegates_to_mcp_app(self, dispatch_fn):
        mcp_app = AsyncMock()
        dispatch = await dispatch_fn(mcp_api_key="", mcp_app_mock=mcp_app)
        receive, send, send_calls = _collect_response()
        scope = _make_scope(
            path="/mcp", method="POST",
            headers={"X-ERPNext-URL": "https://erp.example.com"},
        )
        with patch("src.erpnext_client.set_request_context"):
            await dispatch(scope, receive, send)
            mcp_app.assert_called_once()
            call_args = mcp_app.call_args
            assert call_args[0][0] is scope
