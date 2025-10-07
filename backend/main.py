import os, json, time, traceback
from datetime import datetime
from typing import Any, Dict

from src.config import *
from src.cache_utils import clear_all_caches, get_cache_stats
from src.bedrock_integration import extract_bedrock_parameters, validate_and_match_tables, format_bedrock_response
from src.query_handlers import handle_single_table, handle_parent_child
from src.table_relationships import send_cloudwatch_metrics

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Hybrid approach: LLM extracts tables, Lambda validates and executes.
    Handles both query_simple and query_advanced functions.
    """
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        clear_all_caches()
    start_time = time.time()
    try:
        print(f"Received event: {json.dumps(event, default=str)}")
        function_name = event.get('function', 'query_simple')
        params = extract_bedrock_parameters(event)
        print(f"Function: {function_name}")
        print(f"Extracted parameters:")
        print(f"  - Prompt: '{params.get('prompt')}'")
        print(f"  - Table Names: {params.get('table_names')}")
        if function_name == 'query_simple':
            if params.get('entity_names'):
                print(f"  - Entity Names: {params['entity_names']}")
            print(f"  - Limit: {params.get('limit', 50)}")
        elif function_name == 'query_advanced':
            if params.get('date_filter_value') and params.get('date_filter_unit'):
                print(f"  - Date Filter: {params['date_filter_value']} {params['date_filter_unit']}")
            if params.get('sort_field'):
                print(f"  - Sort: {params['sort_field']} ({params.get('sort_order', 'DESC')})")
        if not params.get('prompt'):
            raise ValueError("Missing required parameter: prompt")
        if not params.get('table_names'):
            raise ValueError("Missing required parameter: table_names")
        validation = validate_and_match_tables(params['table_names'], QB_APP_ID)
        if validation.get('needs_clarification'):
            elapsed = time.time() - start_time
            print(f"INFO: Table validation failed - {elapsed:.2f}s")
            return format_bedrock_response(event, {
                "ok": False,
                "needs_clarification": True,
                "message": validation['suggestion'],
                "details": {
                    "type": "table_not_found",
                    "requested": params['table_names'],
                    "available": validation['available_tables']
                }
            })
        parsed = {
            "mode": validation["mode"],
            "tables": validation["tables"],
            "names": params.get('entity_names', []),
            "formats": ["csv"],
            "original_prompt": params['prompt'],
            "date_filter_value": params.get('date_filter_value'),
            "date_filter_unit": params.get('date_filter_unit'),
            "sort_by": params.get('sort_field'),
            "sort_order": params.get('sort_order', 'DESC')
        }
        print(f"DEBUG: mode={parsed['mode']}, tables={[t['name'] for t in parsed['tables']]}")
        results = []
        if parsed["mode"] == "single":
            results = handle_single_table(parsed, params.get('limit', 50))
        elif parsed["mode"] == "parent+child":
            results = handle_parent_child(parsed, params.get('limit', 50))
        elapsed = time.time() - start_time
        cache_stats = get_cache_stats()
        print(
            f"SUCCESS: {len(results)} reports in {elapsed:.2f}s | "
            f"Caches -> tables: {cache_stats.get('cached_tables')}, "
            f"relationships: {cache_stats.get('cached_relationships')}, "
            f"metadata: {cache_stats.get('cached_metadata')}"
        )
        send_cloudwatch_metrics([
            {'MetricName': 'ReportsGenerated', 'Value': len(results), 'Unit': 'Count', 'Timestamp': datetime.utcnow()},
            {'MetricName': 'ExecutionTime', 'Value': elapsed, 'Unit': 'Seconds', 'Timestamp': datetime.utcnow()},
            {'MetricName': 'SuccessfulInvocations', 'Value': 1, 'Unit': 'Count', 'Timestamp': datetime.utcnow()}
        ])
        return format_bedrock_response(event, {
            "ok": True,
            "reports": results,
            "summary": f"Processed {len(results)} record(s)"
        })
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"ERROR after {elapsed:.2f}s: {str(e)}")
        print(traceback.print_exc())
        return format_bedrock_response(event, {"ok": False, "error": str(e)})
