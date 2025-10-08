import json, urllib.request, ssl, time
from typing import Dict, Any, Optional, List

from src.config import QB_REALM, QB_USER_TOKEN
from src.cache_utils import _field_map_cache, _is_cache_valid
from src.config import CACHE_TTL_SECONDS

def qb_headers() -> Dict[str, str]:
    return {
        "QB-Realm-Hostname": QB_REALM,
        "Authorization": f"QB-USER-TOKEN {QB_USER_TOKEN}",
        "User-Agent": "lambda-function"
    }

def quickbase_get(url: str, retries: int = 3) -> Dict[str, Any]:
    """GET request to QuickBase with retry logic."""
    req = urllib.request.Request(url, headers=qb_headers(), method="GET")
    context = ssl.create_default_context()
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30, context=context) as resp:
                response = json.loads(resp.read().decode("utf-8"))
                if not isinstance(response, (dict, list)):
                    raise ValueError(f"Invalid QuickBase API response type: {type(response).__name__}")
                if isinstance(response, dict):
                    if "error" in response:
                        raise ValueError(f"QuickBase API error: {response.get('error')}")
                    if response.get("status") == "error":
                        raise ValueError(f"QuickBase error: {response.get('message', 'Unknown error')}")
                return response
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                wait_time = 2 ** attempt
                print(f"WARNING: API error {e.code}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                print(f"WARNING: Network error, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")

def quickbase_query(table_id: str, body: Dict[str, Any], max_records: Optional[int] = None, retries: int = 3) -> List[Dict[str, Any]]:
    """Query QuickBase records with pagination."""
    url = "https://api.quickbase.com/v1/records/query"
    headers = {**qb_headers(), "Content-Type": "application/json"}
    all_data, skip = [], 0
    page_size = body.get("options", {}).get("top", 1000)
    if max_records:
        page_size = min(page_size, max_records)
    while True:
        body["from"] = table_id
        body.setdefault("options", {})
        body["options"]["skip"], body["options"]["top"] = skip, page_size
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
                context = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=30, context=context) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Query error {e.code}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Network error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        page_data = result.get("data", [])
        all_data.extend(page_data)
        if not page_data or len(page_data) < page_size:
            break
        skip += page_size
        if max_records and len(all_data) >= max_records:
            return all_data[:max_records]
    return all_data

def load_field_map(table_id: str) -> Dict[str, Dict[str, Any]]:
    """Load field metadata with TTL-based caching. Returns {label: {"id": int, "type": str}}."""
    entry = _field_map_cache.get(table_id)
    if _is_cache_valid(entry):
        print(f"INFO: Using cached field map for table {table_id}")
        return entry["data"]
    elif entry:
        print(f"INFO: Field map cache expired for table {table_id}, refreshing...")
    print(f"INFO: Fetching field map for table {table_id}")
    fields = quickbase_get(f"https://api.quickbase.com/v1/fields?tableId={table_id}")
    if not isinstance(fields, list):
        raise ValueError(f"Expected list of fields, got {type(fields).__name__}")
    for field in fields:
        if not isinstance(field, dict):
            raise ValueError(f"Invalid field format: {type(field).__name__}")
        if "label" not in field or "id" not in field:
            raise ValueError(f"Field missing required keys: {field}")
    result = {f["label"]: {"id": f["id"], "type": f.get("fieldType")} for f in fields}
    _field_map_cache[table_id] = {"timestamp": time.time(), "data": result}
    print(f"INFO: Cached field map for table {table_id} ({len(result)} fields)")
    return result
