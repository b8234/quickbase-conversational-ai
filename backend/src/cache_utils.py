from typing import Dict, Any, Optional
import time

from src.config import CACHE_TTL_SECONDS

# ============================================================================
# CACHE REGISTRIES
# ============================================================================
_field_map_cache: Dict[str, Dict[str, Any]] = {}
_relationship_cache: Dict[str, Dict[str, Any]] = {}
_table_metadata_cache: Dict[str, Dict[str, Any]] = {}

def _is_cache_valid(entry: Optional[Dict[str, Any]], ttl: int = CACHE_TTL_SECONDS) -> bool:
    """True if a cache entry is present and not expired."""
    if not entry or "timestamp" not in entry:
        return False
    return (time.time() - entry["timestamp"]) < ttl

# --- First (detailed) version preserved under a different name
def get_cache_stats_detailed() -> Dict[str, Any]:
    """Return cache statistics for diagnostics (detailed ages)."""
    now = time.time()
    def _age(entry):
        return round(now - entry["timestamp"], 1) if entry and "timestamp" in entry else None
    return {
        "cached_fields": len(_field_map_cache),
        "cached_relationships": len(_relationship_cache),
        "cached_metadata": len(_table_metadata_cache),
        "metadata_age_sec": {k: _age(v) for k, v in _table_metadata_cache.items()},
        "fields_age_sec": {k: _age(v) for k, v in _field_map_cache.items()},
        "relationships_age_sec": {k: _age(v) for k, v in _relationship_cache.items()},
    }

def clear_all_caches() -> None:
    """Manually clear all cached field, relationship, and metadata entries."""
    _field_map_cache.clear()
    _relationship_cache.clear()
    _table_metadata_cache.clear()
    print("INFO: Cleared all caches")

# --- Second (later in your file) version that effectively overwrote the first
def get_cache_stats() -> Dict[str, Any]:
    """Return cache statistics for diagnostics."""
    return {
        "cached_tables": len(_field_map_cache),
        "cached_relationships": len(_relationship_cache),
        "cached_metadata": len(_table_metadata_cache),
        "table_ids": list(_field_map_cache.keys()),
    }
