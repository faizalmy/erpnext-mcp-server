"""Configuration for erpnext-mcp-server.

Reads from environment variables or .env file.
Points directly at an ERPNext instance.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings — point at any ERPNext instance."""

    # ERPNext connection
    erpnext_url: str = "http://localhost:8080"
    erpnext_api_key: str = ""
    erpnext_api_secret: str = ""

    # Auth fallback (password-based, for dev)
    erpnext_usr: str = "Administrator"
    erpnext_pwd: str = "admin"

    # Discovery filter (comma-separated DocType names)
    discovery_include: str = ""   # Only these DocTypes (empty = all)
    discovery_exclude: str = ""   # Skip these DocTypes (empty = none)

    # Timeouts (seconds)
    timeout: float = 30.0

    # HTTP transport settings (for --http mode)
    http_host: str = "127.0.0.1"
    http_port: int = 3000

    # API key for HTTP transport auth (empty = no auth)
    mcp_api_key: str = ""

    model_config = {"env_file": ".env"}

    @property
    def discovery_include_list(self) -> list[str] | None:
        if not self.discovery_include:
            return None
        return [s.strip() for s in self.discovery_include.split(",") if s.strip()]

    @property
    def discovery_exclude_list(self) -> list[str] | None:
        if not self.discovery_exclude:
            return None
        return [s.strip() for s in self.discovery_exclude.split(",") if s.strip()]

    @property
    def api_base(self) -> str:
        """Base URL for ERPNext REST API."""
        return f"{self.erpnext_url}/api/resource"

    @property
    def method_base(self) -> str:
        """Base URL for ERPNext method calls."""
        return f"{self.erpnext_url}/api/method"

    @property
    def auth_header(self) -> dict[str, str]:
        """Authentication header."""
        h: dict[str, str] = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.erpnext_api_key and self.erpnext_api_secret:
            h["Authorization"] = f"token {self.erpnext_api_key}:{self.erpnext_api_secret}"
        return h


settings = Settings()
