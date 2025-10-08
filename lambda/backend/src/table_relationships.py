import json, time, logging
from typing import Dict, Any, List, Optional

from src.config import cloudwatch
from src.quickbase_api import quickbase_get, load_field_map
from src.cache_utils import _relationship_cache, _is_cache_valid, _table_metadata_cache
from src.config import ALLOW_LISTS

logger = logging.getLogger("quickbase-agent")

def send_cloudwatch_metrics(metric_data: List[Dict[str, Any]]) -> None:
    """Send metrics to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='QuickBaseAgent',
            MetricData=metric_data
        )
    except Exception as e:
        logger.warning(f"Failed to send CloudWatch metrics: {e}")

def get_table_metadata(table_id: str, app_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch metadata for a single Quickbase table with TTL-based caching.
    """
    entry = _table_metadata_cache.get(table_id)
    if _is_cache_valid(entry):
        logger.info(f"Using cached metadata for table {table_id}")
        return entry["data"]
    elif entry:
        logger.info(f"Cache expired for table {table_id}, refreshing...")
    url = f"https://api.quickbase.com/v1/tables/{table_id}"
    if app_id:
        url += f"?appId={app_id}"
    table_info = quickbase_get(url)
    if not isinstance(table_info, dict):
        raise ValueError(f"Unexpected response type for table {table_id}: {type(table_info).__name__}")
    _table_metadata_cache[table_id] = {"timestamp": time.time(), "data": table_info}
    logger.info(f"Cached table metadata for '{table_info.get('name')}' ({table_info.get('id')})")
    return table_info

def list_relationships(table_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve relationships for a given Quickbase table.
    TTL-cached to reduce API calls and includes detailed debug logs.
    """
    entry = _relationship_cache.get(table_id)
    if _is_cache_valid(entry):
        logger.info(f"Using cached relationships for table {table_id}")
        return entry["data"]
    elif entry:
        logger.info(f"Relationship cache expired for table {table_id}, refreshing...")
    url = f"https://api.quickbase.com/v1/tables/{table_id}/relationships"
    rels_data = quickbase_get(url)
    rels = rels_data.get("relationships", []) if isinstance(rels_data, dict) else []
    if not rels:
        logger.warning(f"No relationships found for table {table_id}")
        _relationship_cache[table_id] = {"timestamp": time.time(), "data": []}
        return []
    logger.info(f"Found {len(rels)} relationship(s) for table {table_id}")
    for r in rels:
        parent_id = r.get("parentTableId")
        child_id = r.get("childTableId")
        fk_field = r.get("foreignKeyField", {}).get("id")
        fk_label = r.get("foreignKeyField", {}).get("label")
        print(
            f"INFO: Relationship — Parent: {parent_id}, "
            f"Child: {child_id}, Foreign Key FID: {fk_field} ({fk_label})"
        )
    _relationship_cache[table_id] = {"timestamp": time.time(), "data": rels}
    return rels

def normalize_record_name(
    table: Dict[str, str],
    record: Optional[Dict[str, Any]] = None,
    parsed_names: Optional[List[str]] = None,
    default: str = "record",
    field_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> str:
    """Generate safe record name for S3 filenames."""
    base = table["name"].replace(" ", "_")
    table_entry = ALLOW_LISTS.get(table["name"], {})
    allow_list = table_entry.get("fields", [])
    if record and allow_list:
        if field_map is None:
            field_map = load_field_map(table["id"])
        for field in allow_list:
            if field in field_map:
                val = record.get(str(field_map[field]["id"]), {}).get("value")
                if val:
                    safe_val = str(val).strip().replace(" ", "_")[:50]
                    return f"{base}_{safe_val}"
    if parsed_names:
        ignore = {"show", "list", "get", "return"}
        for name in parsed_names:
            if name.lower() not in ignore:
                safe_name = name.strip().replace(" ", "_")
                return f"{base}_{safe_name}"
    return f"{base}_{default}"
