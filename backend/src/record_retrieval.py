import json, time
from typing import Dict, Any, Optional, List

from src.quickbase_api import load_field_map, quickbase_query
from src.config import ALLOW_LISTS, QB_LARGE_QUERY_THRESHOLD
from src.field_detection import (
    find_date_field_from_allowlist, find_name_field_from_allowlist,
    find_related_key_fields_from_allowlist, find_unique_fields_from_allowlist,
    get_relationship_operator, get_sort_field_id, clean_field_name
)
from src.table_relationships import list_relationships
from src.formatters import format_record
from src.attachments import process_attachment

def get_records(table: Dict[str, str], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    field_map = load_field_map(table["id"])
    table_entry = ALLOW_LISTS.get(table["name"], {})
    allow_list = table_entry.get("fields", [])
    select_fields = [field_map[lbl]["id"] for lbl in allow_list if lbl in field_map]
    if "Record ID#" in field_map:
        rid = field_map["Record ID#"]["id"]
        if rid not in select_fields:
            select_fields.insert(0, rid)
    body = {"select": select_fields} if select_fields else {}
    return quickbase_query(table["id"], body, max_records=limit or QB_LARGE_QUERY_THRESHOLD)

def get_child_records(
    parent_table: Dict[str, str],
    child_table: Dict[str, str],
    parent_record_id: int,
    date_filter_value: Optional[int] = None,
    date_filter_unit: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch child records with optional date filtering."""
    print(f"DEBUG: get_child_records() called")
    print(f"DEBUG: parent = '{parent_table['name']}', child = '{child_table['name']}'")
    print(f"DEBUG: parent_record_id = {parent_record_id}")
    print(f"DEBUG: parent_table['id'] = '{parent_table['id']}'")
    print(f"DEBUG: child_table['id'] = '{child_table['id']}'")
    print(f"DEBUG: date_filter_value = {date_filter_value}, date_filter_unit = {date_filter_unit}")
    rels = list_relationships(child_table["id"])
    print(f"DEBUG: Found {len(rels)} relationships for child table")
    print(f"DEBUG: Raw relationships data: {json.dumps(rels, default=str, indent=2)}")
    for r in rels:
        print(f"DEBUG: Processing relationship: {json.dumps(r, default=str, indent=2)}")
        foreign_id = r.get("parentTableId")
        print(f"DEBUG: Checking relationship - parentTableId = '{foreign_id}' vs parent id = '{parent_table['id']}'")
        if foreign_id == parent_table["id"]:
            print(f"DEBUG: ✓ Relationship matched!")
            ref_field_id = r.get("foreignKeyField", {}).get("id")
            ref_field_label = r.get("foreignKeyField", {}).get("label", "")
            if not ref_field_id:
                print(f"ERROR: No foreign key field ID found in relationship")
                continue
            operator = get_relationship_operator(parent_table["name"], child_table["name"], ref_field_label)
            print(f"DEBUG: Using foreign key field ID: {ref_field_id} with operator {operator}")
            where_clauses = [f"{{{ref_field_id}{operator}{parent_record_id}}}"]
            if date_filter_value and date_filter_unit:
                print(f"DEBUG: Date filtering requested - loading child field map")
                child_map = load_field_map(child_table["id"])
                print(f"DEBUG: Calling find_date_field_from_allowlist for '{child_table['name']}'")
                date_fid = find_date_field_from_allowlist(child_table["name"], child_map)
                print(f"DEBUG: find_date_field_from_allowlist returned: {date_fid}")
                if date_fid:
                    unit_map = {'d': 'days','w': 'weeks','m': 'months','y': 'years'}
                    unit_text = unit_map.get(date_filter_unit, 'days')
                    date_clause = f"{{{date_fid}.OAF.'{date_filter_value} {unit_text} ago'}}"
                    where_clauses.append(date_clause)
                    print(f"DEBUG: Added date filter: {date_clause}")
                else:
                    print(f"WARNING: No date field in ALLOW_LIST for '{child_table['name']}'")
            else:
                print(f"DEBUG: No date filtering - date_filter_value={date_filter_value}, date_filter_unit={date_filter_unit}")
            where_clause = " AND ".join(where_clauses)
            body = {"where": where_clause}
            print(f"DEBUG: Child query WHERE: {where_clause}")
            print(f"DEBUG: Executing Quickbase child query → table={child_table['id']}")
            children_result = quickbase_query(child_table["id"], body, max_records=QB_LARGE_QUERY_THRESHOLD)
            print(f"DEBUG: Child query returned {len(children_result)} records")
            if children_result:
                print(f"DEBUG: First child record sample:\n{json.dumps(children_result[0], indent=2)}")
            else:
                print(f"WARNING: Query executed successfully but returned no child records.")
            return children_result
    print(f"WARNING: No matching relationship found between '{parent_table['name']}' and '{child_table['name']}'")
    return []
