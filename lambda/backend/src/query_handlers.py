import json, logging
from typing import Dict, Any, List

from src.quickbase_api import quickbase_query, load_field_map
from src.config import ALLOW_LISTS, SLACK_CHANNEL_ID, SLACK_BOT_TOKEN
from src.field_detection import (
    clean_field_name, find_name_field_from_allowlist,
    find_related_key_fields_from_allowlist, find_unique_fields_from_allowlist,
    find_date_field_from_allowlist, get_sort_field_id
)
from src.formatters import format_record
from src.table_relationships import normalize_record_name
from src.summary import generate_summary
from src.exports import save_all_formats, save_to_s3
from src.slack_utils import send_batched_slack_messages
from src.record_retrieval import get_child_records

logger = logging.getLogger("quickbase-agent")

def handle_single_table(parsed: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Process single table query."""
    results = []
    table = parsed["tables"][0] if parsed["tables"] else None
    if not table:
        return results
    field_map = load_field_map(table["id"])
    table_entry = ALLOW_LISTS.get(table["name"], {})
    allow_list = table_entry.get("fields", [])
    body = {}
    where_clauses = []
    if parsed["names"] and allow_list:
        name_fid = find_name_field_from_allowlist(table["name"], field_map)
        related_fids = find_related_key_fields_from_allowlist(table["name"], field_map)
        unique_fids = find_unique_fields_from_allowlist(parsed.get("original_prompt", ""), table["name"], field_map)
        if name_fid or related_fids or unique_fids:
            search_fids = []
            if name_fid:
                search_fids.append(name_fid)
            search_fids.extend(related_fids)
            search_fids.extend(unique_fids)
            name_clauses = []
            for name in parsed["names"]:
                field_clauses = [f"{{{fid}.EX.'{name}'}}" for fid in search_fids]
                name_clauses.append("OR".join(field_clauses))
            if len(name_clauses) > 1:
                where_clauses.append("(" + "OR".join([f"({c})" for c in name_clauses]) + ")")
            elif name_clauses:
                where_clauses.append("(" + name_clauses[0] + ")")
    if parsed.get("date_filter_value") and parsed.get("date_filter_unit"):
        value = parsed["date_filter_value"]
        unit = parsed["date_filter_unit"]
        date_fid = find_date_field_from_allowlist(table["name"], field_map)
        if date_fid:
            date_clause = f"{{{date_fid}.OAF.'today-{value}{unit}'}}"
            where_clauses.append(date_clause)
            logger.debug(f"Added date filter: {date_clause}")
        else:
            logger.warning(f"No date field in ALLOW_LIST for '{table['name']}'")
    if where_clauses:
        where_clause = "AND".join(where_clauses)
        body["where"] = where_clause
        logger.debug(f"Query WHERE: {where_clause}")
    if parsed.get("sort_by"):
        sort_field_id = get_sort_field_id(parsed["sort_by"], table["name"], field_map)
        if sort_field_id:
            sort_order = parsed.get("sort_order", "DESC")
            body["sortBy"] = [{"fieldId": sort_field_id, "order": sort_order}]
            logger.debug(f"Sort by FID {sort_field_id} ({sort_order})")
    select_fields = []
    for lbl in allow_list:
        clean_lbl = clean_field_name(lbl)
        if clean_lbl in field_map:
            select_fields.append(field_map[clean_lbl]["id"])
        else:
            logger.warning(f"Field '{clean_lbl}' not found in field_map for table '{table['name']}'")
    if "Record ID#" in field_map:
        rid_field_id = field_map["Record ID#"]["id"]
        if rid_field_id not in select_fields:
            select_fields.insert(0, rid_field_id)
    if select_fields:
        body["select"] = select_fields
    rows = quickbase_query(table["id"], body, max_records=limit)
    all_records = []
    for r in rows:
        formatted = format_record(r, table, field_labels=allow_list)
        all_records.append(formatted)
    if all_records:
        rec_name = normalize_record_name(table, record=rows[0], parsed_names=parsed["names"], field_map=field_map)
        summary_data = generate_summary(all_records, table["name"], rec_name)
        urls = save_all_formats(
            all_records,
            rec_name,
            parsed["formats"],
            summary=summary_data["insights"]
        )
        reports = []
        for fmt in ["csv", "json"]:
            if fmt in urls and urls[fmt]:
                reports.append({
                    "format": fmt.upper(),
                    "label": f"Download {fmt.upper()} Report",
                    "url": urls[fmt]
                })
        results.append({
            "record_name": rec_name,
            "summary": summary_data,
            "reports": reports
        })
    send_batched_slack_messages(results, SLACK_CHANNEL_ID, SLACK_BOT_TOKEN)
    return results

def handle_parent_child(parsed: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Process parent+child query with S3 presigned URLs for attachments (CSV-only)."""
    results = []
    parent, child = parsed["tables"][:2]
    parent_map = load_field_map(parent["id"])
    body = {}
    where_clauses = []
    if parsed["names"]:
        parent_entry = ALLOW_LISTS.get(parent["name"], {})
        allow_list = parent_entry.get("fields", [])
        if allow_list:
            name_fid = find_name_field_from_allowlist(parent["name"], parent_map)
            related_fids = find_related_key_fields_from_allowlist(parent["name"], parent_map)
            unique_fids = find_unique_fields_from_allowlist(parsed.get("original_prompt", ""), parent["name"], parent_map)
            if name_fid or related_fids or unique_fids:
                search_fids = []
                if name_fid:
                    search_fids.append(name_fid)
                search_fids.extend(related_fids)
                search_fids.extend(unique_fids)
                name_clauses = []
                for name in parsed["names"]:
                    field_clauses = [f"{{{fid}.EX.'{name}'}}" for fid in search_fids]
                    name_clauses.append("OR".join(field_clauses))
                if len(name_clauses) > 1:
                    where_clauses.append("(" + "OR".join([f"({c})" for c in name_clauses]) + ")")
                elif name_clauses:
                    where_clauses.append("(" + name_clauses[0] + ")")
    if where_clauses:
        body["where"] = "AND".join(where_clauses)
    if parsed.get("sort_by"):
        sort_field_id = get_sort_field_id(parsed["sort_by"], parent["name"], parent_map)
        if sort_field_id:
            sort_order = parsed.get("sort_order", "DESC")
            body["sortBy"] = [{"fieldId": sort_field_id, "order": sort_order}]
            print(f"DEBUG: Parent sort by FID {sort_field_id} ({sort_order})")
    allow_list = ALLOW_LISTS.get(parent["name"], [])
    select_fields = []
    for lbl in allow_list:
        clean_lbl = clean_field_name(lbl)
        if clean_lbl in parent_map:
            select_fields.append(parent_map[clean_lbl]["id"])
    rid_field_id = parent_map["Record ID#"]["id"]
    if rid_field_id not in select_fields:
        select_fields.insert(0, rid_field_id)
    if select_fields:
        body["select"] = select_fields
    parents = quickbase_query(parent["id"], body, max_records=limit)
    child_map = load_field_map(child["id"])
    from src.summary import generate_summary
    for p in parents:
        pid = p[str(parent_map["Record ID#"]["id"])]["value"]
        children = get_child_records(
            parent,
            child,
            pid,
            date_filter_value=parsed.get("date_filter_value"),
            date_filter_unit=parsed.get("date_filter_unit")
        )
        print(f"DEBUG: get_child_records() returned {len(children)} rows for parent ID {pid}")
        parent_formatted = format_record(p, parent, field_labels=ALLOW_LISTS.get(parent["name"], []))
        rec_name = normalize_record_name(parent, record=p, parsed_names=parsed["names"], field_map=parent_map)
        all_flat_rows = []
        child_records = []
        child_entry = ALLOW_LISTS.get(child["name"], {})
        child_fields = child_entry.get("fields", [])
        print(f"DEBUG: Building flat rows for '{parent['name']}' + '{child['name']}' ({len(children)} children)")
        if children:
            for idx, c in enumerate(children, start=1):
                child_formatted = format_record(c, child, field_labels=child_fields)
                child_records.append(child_formatted)
                flat_row = {}
                for key, value in parent_formatted.items():
                    if value is not None and value != "":
                        col_name = f"{parent['name']}_{key}"
                        if isinstance(value, dict) and "url" in value and "/files/" in value["url"]:
                            try:
                                version = 1
                                if "versions" in value and value["versions"]:
                                    version = value["versions"][0].get("versionNumber", 1)
                                from src.attachments import process_attachment
                                presigned_url = process_attachment(
                                    table_id=parent["id"],
                                    record_id=int(p.get(str(parent_map["Record ID#"]["id"]))["value"]),
                                    field_id=int(parent_map[key]["id"]),
                                    version=version,
                                    s3_name_prefix=parent["name"].lower().replace(" ", "_")
                                )
                                flat_row[col_name] = presigned_url or value["url"]
                                continue
                            except Exception as e:
                                print(f"ERROR: Failed to upload parent attachment {key}: {e}")
                                flat_row[col_name] = str(value)
                                continue
                        if isinstance(value, (dict, list)):
                            flat_row[col_name] = json.dumps(value)
                        else:
                            flat_row[col_name] = value
                for key, value in child_formatted.items():
                    if value is not None and value != "":
                        col_name = f"{child['name']}_{key}"
                        if isinstance(value, dict) and "url" in value and "/files/" in value["url"]:
                            try:
                                version = 1
                                if "versions" in value and value["versions"]:
                                    version = value["versions"][0].get("versionNumber", 1)
                                from src.attachments import process_attachment
                                presigned_url = process_attachment(
                                    table_id=child["id"],
                                    record_id=int(c.get(str(child_map["Record ID#"]["id"]))["value"]),
                                    field_id=int(child_map[key]["id"]),
                                    version=version,
                                    s3_name_prefix=child["name"].lower().replace(" ", "_")
                                )
                                flat_row[col_name] = presigned_url or value["url"]
                                continue
                            except Exception as e:
                                print(f"ERROR: Failed to upload child attachment {key}: {e}")
                                flat_row[col_name] = str(value)
                                continue
                        if isinstance(value, (dict, list)):
                            flat_row[col_name] = json.dumps(value)
                        else:
                            flat_row[col_name] = value
                if flat_row:
                    all_flat_rows.append(flat_row)
                    if idx == 1:
                        print(f"DEBUG: First flat row has {len(flat_row)} columns: {list(flat_row.keys())[:5]}")
        else:
            flat_row = {}
            for key, value in parent_formatted.items():
                if value is not None and value != "":
                    col_name = f"{parent['name']}_{key}"
                    if isinstance(value, (dict, list)):
                        flat_row[col_name] = json.dumps(value)
                    else:
                        flat_row[col_name] = value
            if flat_row:
                all_flat_rows.append(flat_row)
        print(f"DEBUG: Built {len(all_flat_rows)} total flat rows for CSV")
        print(f"DEBUG: Built {len(child_records)} child records for summary")
        summary_data = generate_summary(child_records, child["name"], rec_name)
        csv_url = None
        try:
            if all_flat_rows:
                csv_url = save_to_s3(all_flat_rows, record_name=rec_name)
                print(f"SUCCESS: Saved CSV with {len(all_flat_rows)} rows")
            else:
                print("WARNING: No data to save for CSV")
        except Exception as e:
            print(f"ERROR: CSV save failed: {e}")
            import traceback; traceback.print_exc()
        reports = []
        if csv_url:
            reports.append({
                "format": "CSV",
                "label": "Download CSV Report",
                "url": csv_url
            })
        if csv_url:
            exports_md = "\n".join(["", "", "**Data Exports:**", f"- [CSV Format]({csv_url})"])
            if isinstance(summary_data, dict):
                for key in ("markdown", "text", "body", "summary"):
                    if key in summary_data and isinstance(summary_data[key], str):
                        summary_data[key] += exports_md
                        break
                else:
                    summary_data["text"] = exports_md.lstrip("\n")
                summary_data.setdefault("exports", {})
                summary_data["exports"]["csv"] = csv_url
            elif isinstance(summary_data, str) or summary_data is None:
                summary_data = (summary_data or "") + exports_md
            else:
                print(f"WARNING: summary_data is type {type(summary_data)}; coercing to string")
                summary_data = str(summary_data) + exports_md
            print("DEBUG: Embedded CSV presigned URL in summary output")
        results.append({
            "record_name": rec_name,
            "summary": summary_data,
            "reports": reports
        })
    from src.config import SLACK_CHANNEL_ID, SLACK_BOT_TOKEN
    from src.slack_utils import send_batched_slack_messages
    send_batched_slack_messages(results, SLACK_CHANNEL_ID, SLACK_BOT_TOKEN)
    return results
