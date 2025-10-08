from typing import Dict, Any, List

from src.config import ALLOW_LISTS, QB_APP_ID
from src.table_relationships import get_table_metadata

def extract_bedrock_parameters(event: Dict[str, Any]) -> Dict[str, Any]:
    params = {'limit': 50, 'sort_order': 'DESC'}
    UNIT_MAP = {'days': 'd','weeks': 'w','months': 'm','years': 'y','d':'d','w':'w','m':'m','y':'y'}
    for param in event.get('parameters', []):
        name = param.get('name')
        value = param.get('value')
        if name == 'prompt':
            params['prompt'] = value or ''
        elif name == 'table_names':
            if isinstance(value, list):
                params['table_names'] = value
            elif isinstance(value, str) and value:
                cleaned = value.strip('[]').strip()
                params['table_names'] = [t.strip().strip("'\"") for t in cleaned.split(',') if t.strip()]
        elif name == 'entity_names':
            if isinstance(value, list):
                params['entity_names'] = value
            elif isinstance(value, str) and value:
                cleaned = value.strip('[]').strip()
                params['entity_names'] = [n.strip().strip("'\"") for n in cleaned.split(',') if n.strip()]
        elif name == 'date_filter_value':
            params['date_filter_value'] = int(value) if value else None
        elif name == 'date_filter_unit':
            params['date_filter_unit'] = UNIT_MAP.get(value.lower(), value) if value else None
        elif name == 'sort_field':
            params['sort_field'] = value
            prompt_lower = params.get('prompt', '').lower()
            if 'top' in prompt_lower or 'highest' in prompt_lower or 'most' in prompt_lower:
                params['sort_order'] = 'DESC'
            elif 'bottom' in prompt_lower or 'lowest' in prompt_lower or 'least' in prompt_lower:
                params['sort_order'] = 'ASC'
        elif name == 'sort_order':
            params['sort_order'] = value.upper() if value else 'DESC'
        elif name == 'limit':
            params['limit'] = int(value) if value else 50
    return params

def validate_and_match_tables(suggested_tables: List[str], app_id: str) -> Dict[str, Any]:
    """
    Validate LLM-suggested tables using ALLOW_LISTS.
    Uses lightweight get_table_metadata() instead of full list_tables().
    """
    matched = []
    for suggested in suggested_tables:
        entry = ALLOW_LISTS.get(suggested)
        if entry and "id" in entry:
            table_id = entry["id"]
            table_info = get_table_metadata(table_id, app_id)
            matched.append(table_info)
            print(f"INFO: Matched table '{table_info['name']}' ({table_info['id']})")
        else:
            matched_entry = None
            for name, data in ALLOW_LISTS.items():
                if name.lower() == suggested.lower():
                    matched_entry = data
                    table_info = get_table_metadata(data["id"], app_id)
                    matched.append(table_info)
                    print(f"INFO: Matched table '{name}' ({data['id']}) via case-insensitive match")
                    break
            if not matched_entry:
                available = list(ALLOW_LISTS.keys())
                print(f"WARNING: Table '{suggested}' not found in ALLOW_LISTS")
                
                # Create a formatted list of available tables
                table_list = "\n".join([f"- {table}" for table in available])
                
                return {
                    "needs_clarification": True,
                    "error": f"Table '{suggested}' not found in ALLOW_LISTS",
                    "available_tables": available,
                    "suggestion": f"Table '{suggested}' is not available. Please specify one of these tables:\n\n{table_list}"
                }
    mode = "parent+child" if len(matched) == 2 else "single"
    return {"ok": True, "tables": matched, "mode": mode}

def format_bedrock_response(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """Format response for Bedrock."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get('actionGroup', ''),
            "function": event.get('function', ''),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json_dumps(data)
                    }
                }
            }
        }
    }

# local wrapper so we don't pull json at top if you prefer to keep imports minimal elsewhere
def json_dumps(data):
    import json
    return json.dumps(data)
