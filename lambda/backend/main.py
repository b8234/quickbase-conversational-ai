import os, json, time, traceback, logging
from datetime import datetime
from typing import Any, Dict

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("quickbase-agent")

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
    actions = []  # Collect service-agnostic action summaries
    def log_action(service, action):
        actions.append({"service": service, "action": action})
    try:
        logger.info(json.dumps({
            "event": event,
            "message": "Received event"
        }, default=str))
        function_name = event.get('function', 'query_simple')
        params = extract_bedrock_parameters(event)
        logger.info(json.dumps({
            "function": function_name,
            "params": {
                "prompt": params.get('prompt'),
                "table_names": params.get('table_names'),
                "entity_names": params.get('entity_names'),
                "limit": params.get('limit', 50),
                "date_filter_value": params.get('date_filter_value'),
                "date_filter_unit": params.get('date_filter_unit'),
                "sort_field": params.get('sort_field'),
                "sort_order": params.get('sort_order', 'DESC')
            },
            "message": "Extracted parameters"
        }, default=str))
        # Additional logging for specific parameters if needed
        if function_name == 'query_simple':
            if params.get('entity_names'):
                logger.info(json.dumps({
                    "entity_names": params['entity_names'],
                    "message": "Entity Names"
                }))
            logger.info(json.dumps({
                "limit": params.get('limit', 50),
                "message": "Limit"
            }))
        elif function_name == 'query_advanced':
            if params.get('date_filter_value') and params.get('date_filter_unit'):
                logger.info(json.dumps({
                    "date_filter_value": params['date_filter_value'],
                    "date_filter_unit": params['date_filter_unit'],
                    "message": "Date Filter"
                }))
            if params.get('sort_field'):
                logger.info(json.dumps({
                    "sort_field": params['sort_field'],
                    "sort_order": params.get('sort_order', 'DESC'),
                    "message": "Sort Field"
                }))
        if not params.get('prompt'):
            raise ValueError("Missing required parameter: prompt")
        if not params.get('table_names'):
            raise ValueError("Missing required parameter: table_names")
        validation = validate_and_match_tables(params['table_names'], QB_APP_ID)
        if validation.get('needs_clarification'):
            elapsed = time.time() - start_time
            logger.warning(json.dumps({
                "message": "Table validation failed",
                "elapsed": elapsed
            }))
            # Do not include actions in clarification response
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
        logger.debug(json.dumps({
            "mode": parsed['mode'],
            "tables": [t['name'] for t in parsed['tables']],
            "message": "Parsed mode and tables"
        }))
        results = []
        # Log Quickbase query action
        log_action("Quickbase", f"Queried tables: {[t['name'] for t in parsed['tables']]}")
        if parsed["mode"] == "single":
            results = handle_single_table(parsed, params.get('limit', 50))
            log_action("Slack", "Sent notification to Slack channel")
            log_action("S3", "Stored CSV report and generated presigned URL")
        elif parsed["mode"] == "parent+child":
            results = handle_parent_child(parsed, params.get('limit', 50))
            log_action("Slack", "Sent notification to Slack channel")
            log_action("S3", "Stored CSV report and generated presigned URL")
        elapsed = time.time() - start_time
        cache_stats = get_cache_stats()
        logger.info(json.dumps({
            "actions": actions,
            "message": "Action log"
        }))
        logger.info(json.dumps({
            "result_count": len(results),
            "elapsed": elapsed,
            "cache_stats": cache_stats,
            "message": "Report generation summary"
        }))
        send_cloudwatch_metrics([
            {'MetricName': 'ReportsGenerated', 'Value': len(results), 'Unit': 'Count', 'Timestamp': datetime.utcnow()},
            {'MetricName': 'ExecutionTime', 'Value': elapsed, 'Unit': 'Seconds', 'Timestamp': datetime.utcnow()},
            {'MetricName': 'SuccessfulInvocations', 'Value': 1, 'Unit': 'Count', 'Timestamp': datetime.utcnow()}
        ])
        # Guarantee 'actions' is always present in the response
        if not actions:
            actions = []
        return format_bedrock_response(event, {
            "ok": True,
            "reports": results,
            "summary": f"Processed {len(results)} record(s)",
            "actions": actions
        })
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(json.dumps({
            "error": str(e),
            "elapsed": elapsed,
            "trace": traceback.format_exc(),
            "message": "Exception occurred"
        }))
    # Do not include actions in error response
    return format_bedrock_response(event, {"ok": False, "error": str(e)})
