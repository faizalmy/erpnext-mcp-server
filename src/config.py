"""Configuration for erpnext-mcp-server.

Reads from environment variables or .env file.
Points directly at an ERPNext instance.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings — point at any ERPNext instance."""

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



settings = Settings()
