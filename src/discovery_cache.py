"""Cache management for DocType discovery.

Handles loading, saving, and TTL validation of cached DocType metadata.
Separated from discovery engine for modularity.
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path

from .erpnext_client import get_request_url

log = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = ".cache"
DEFAULT_CACHE_FILE = "doctypes.json"
DEFAULT_CACHE_TTL = 86400  # 24 hours


def get_cache_path() -> Path:
    """Resolve cache file path from env or default."""
    cache_dir = os.environ.get("ERPNEXT_CACHE_DIR", DEFAULT_CACHE_DIR)
    cache_file = os.environ.get("ERPNEXT_CACHE_FILE", DEFAULT_CACHE_FILE)
    base_name = Path(cache_file).stem
    suffix = Path(cache_file).suffix
    # Key by tenant URL so each tenant has their own cache
    url = get_request_url() or "default"
    safe_key = hashlib.sha256(url.encode()).hexdigest()[:16]
    return Path(cache_dir) / f"{base_name}_{safe_key}{suffix}"


def get_cache_ttl() -> int:
    """Cache TTL in seconds. 0 = always refresh."""
    return int(os.environ.get("ERPNEXT_CACHE_TTL", str(DEFAULT_CACHE_TTL)))


def load_cache(path: Path) -> dict | None:
    """Load cached metadata if valid and fresh."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = data.get("_cached_at", 0)
        ttl = get_cache_ttl()
        if ttl > 0 and (time.time() - cached_at) > ttl:
            log.info("Cache expired (%.0fh old, TTL=%dh)", (time.time() - cached_at) / 3600, ttl / 3600)
            return None
        return data
    except (json.JSONDecodeError, KeyError) as e:
        log.warning("Invalid cache file, will re-fetch: %s", e)
        return None


def save_cache(path: Path, data: dict) -> None:
    """Save metadata to cache file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = time.time()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        log.info("Cache saved to %s", path)
    except Exception as e:
        log.warning("Could not save cache: %s", e)
