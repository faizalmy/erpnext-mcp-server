"""Configuration for AI-ERP MCP server.

Reads from environment variables or .env file.
All config is about WHERE the gateway is, not HOW to execute anything.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MCP server settings — all gateway-related, no business logic."""

    # Gateway connection
    gateway_url: str = "http://127.0.0.1:8000"
    gateway_api_key: str = ""
    gateway_version: str = "v1"

    # Timeouts (seconds)
    timeout_connect: float = 10.0
    timeout_read: float = 30.0

    model_config = {"env_file": ".env", "env_prefix": "GATEWAY_"}

    @property
    def api_base(self) -> str:
        """Base URL for gateway API calls."""
        return f"{self.gateway_url}/api/{self.gateway_version}"

    @property
    def headers(self) -> dict[str, str]:
        """Headers sent with every gateway request."""
        h = {"Content-Type": "application/json"}
        if self.gateway_api_key:
            h["Authorization"] = f"Bearer {self.gateway_api_key}"
        return h


settings = Settings()
