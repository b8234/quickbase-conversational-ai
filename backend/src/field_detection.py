import re
from typing import Dict, Any, Optional, List

from src.config import ALLOW_LISTS
from src.quickbase_api import load_field_map

def clean_field_name(label: str) -> str:
    """
    Strip markers like [KEY], [DATE], [UNIQUE], [RELATED KEY] from field labels.
    Returns clean Quickbase field label.
    """
    if not label:
        return label
    return re.sub(r"\s*\[[A-Z ]+\]\s*", "", label).strip()

def find_date_field_from_allowlist(table_name: str, field_map: Dict[str, Dict[str, Any]]) -> Optional[int]:
    """Find date field using [DATE] marker only."""
    table_entry = ALLOW_LISTS.get(table_name, {})
    allow_list = table_entry.get("fields", [])
    print(f"INFO: Searching for date field in table '{table_name}'")
    for field_name in allow_list:
        if "[DATE]" in field_name:
            clean_name = clean_field_name(field_name)
            if clean_name in field_map:
                field_id = field_map[clean_name]["id"]
                print(f"INFO: Date field '{clean_name}' (FID {field_id}) found in '{table_name}'")
                return field_id
            else:
                print(f"WARNING: Date field '{clean_name}' marked in ALLOW_LIST but not found in QuickBase")
    print(f"WARNING: No [DATE] marker in ALLOW_LIST for '{table_name}'")
    return None

def find_name_field_from_allowlist(table_name: str, field_map: Dict[str, Dict[str, Any]]) -> Optional[int]:
    """Find name field using [KEY] marker only."""
    table_entry = ALLOW_LISTS.get(table_name, {})
    allow_list = table_entry.get("fields", [])
    for field_name in allow_list:
        if "[KEY]" in field_name:
            clean_name = clean_field_name(field_name)
            if clean_name in field_map:
                return field_map[clean_name]["id"]
    print(f"WARNING: No [KEY] marker found in ALLOW_LIST for '{table_name}'")
    return None

def find_related_key_fields_from_allowlist(table_name: str, field_map: Dict[str, Dict[str, Any]]) -> List[int]:
    """Find all [RELATED KEY] fields from ALLOW_LIST."""
    table_entry = ALLOW_LISTS.get(table_name, {})
    allow_list = table_entry.get("fields", [])
    related_fids = []
    for field_name in allow_list:
        if "[RELATED KEY]" in field_name:
            clean_name = clean_field_name(field_name)
            if clean_name in field_map:
                field_id = field_map[clean_name]["id"]
                related_fids.append(field_id)
                print(f"DEBUG: Found RELATED KEY field '{clean_name}' (FID {field_id})")
    return related_fids

def find_unique_fields_from_allowlist(query: str, table_name: str, field_map: Dict[str, Dict[str, Any]]) -> List[int]:
    """Find [UNIQUE] fields - no keyword matching, just return all marked fields."""
    table_entry = ALLOW_LISTS.get(table_name, {})
    allow_list = table_entry.get("fields", [])
    unique_fids = []
    for field_name in allow_list:
        if "[UNIQUE]" in field_name:
            clean_name = clean_field_name(field_name)
            if clean_name in field_map:
                unique_fids.append(field_map[clean_name]["id"])
    return unique_fids

def get_relationship_operator(parent_table: str, child_table: str, ref_field_label: str) -> str:
    """
    Return .TV. only for Record ID# ↔ Related Key relationships.
    All other comparisons use .EX.
    """
    parent_entry = ALLOW_LISTS.get(parent_table, {})
    child_entry = ALLOW_LISTS.get(child_table, {})
    parent_fields = parent_entry.get("fields", [])
    child_fields = child_entry.get("fields", [])
    parent_uses_record_id_key = any("[KEY]" in f and "Record ID#" in f for f in parent_fields)
    child_has_related_key = any("[RELATED KEY]" in f and ref_field_label in f for f in child_fields)
    if parent_uses_record_id_key and child_has_related_key:
        operator = ".TV."
    else:
        operator = ".EX."
    print(
        f"INFO: Operator decision → parent={parent_table}, child={child_table}, "
        f"field='{ref_field_label}', operator={operator}"
    )
    return operator

def get_sort_field_id(sort_field_name: str, table_name: str, field_map: Dict[str, Dict[str, Any]]) -> Optional[int]:
    """Get field ID for exact field name - Bedrock provides exact name."""
    if sort_field_name in field_map:
        field_id = field_map[sort_field_name]["id"]
        print(f"DEBUG: Found sort field '{sort_field_name}' (FID {field_id})")
        return field_id
    print(f"WARNING: Sort field '{sort_field_name}' not found in '{table_name}'")
    return None
