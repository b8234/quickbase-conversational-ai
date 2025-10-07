import json, re
from typing import Dict, Any, Optional, List

from src.quickbase_api import load_field_map
from src.config import ALLOW_LISTS
from src.field_detection import clean_field_name
from src.attachments import process_attachment

def format_record(
    record: Dict[str, Any],
    table: Dict[str, str],
    field_labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Format a record and, for any Quickbase file fields, upload the file to S3
    and replace the value with a presigned S3 URL so the CSV has a direct link.
    """
    field_map = load_field_map(table["id"])
    table_entry = ALLOW_LISTS.get(table["name"], {})
    if not field_labels:
        field_labels = table_entry.get("fields", list(field_map.keys()))
    output: Dict[str, Any] = {}
    rid_meta = field_map.get("Record ID#")
    record_id: Optional[int] = None
    if rid_meta:
        rid_fid = str(rid_meta["id"])
        record_id = record.get(rid_fid, {}).get("value")
        if isinstance(record_id, str) and record_id.isdigit():
            record_id = int(record_id)
        elif isinstance(record_id, (int, float)):
            record_id = int(record_id)
        else:
            record_id = None
    for label in field_labels:
        clean_label = clean_field_name(label)
        if clean_label not in field_map:
            continue
        meta = field_map[clean_label]
        fid_str = str(meta["id"])
        ftype = meta.get("type")
        raw = record.get(fid_str, {})
        val = raw.get("value")
        if ftype == "file" and isinstance(val, dict):
            qb_url = val.get("url") or ""
            version = 1
            versions = val.get("versions", [])
            if isinstance(versions, list) and versions:
                vnum = versions[0].get("versionNumber")
                if isinstance(vnum, (int, float)) or (isinstance(vnum, str) and vnum.isdigit()):
                    version = int(vnum)
            rid = record_id
            if not rid and qb_url:
                m = re.match(r"^/files/[^/]+/(\d+)/(\d+)/(?:\d+)", qb_url)
                if m:
                    rid = int(m.group(1))
                    m_ver = re.match(r"^/files/[^/]+/\d+/\d+/(\d+)", qb_url)
                    if m_ver:
                        version = int(m_ver.group(1))
            if rid:
                try:
                    s3_url = process_attachment(
                        table_id=table["id"],
                        record_id=int(rid),
                        field_id=int(fid_str),
                        version=int(version),
                        s3_name_prefix=table["name"].lower().replace(" ", "_")
                    )
                    output[clean_label] = s3_url or qb_url
                except Exception as e:
                    print(f"ERROR: Attachment handling failed for '{clean_label}' (record {rid}): {e}")
                    output[clean_label] = qb_url
            else:
                output[clean_label] = qb_url
            continue
        output[clean_label] = val
    return output

def format_parent_with_children(
    parent_record: Dict[str, Any],
    parent_table: Dict[str, str],
    child_records: List[Dict[str, Any]],
    child_table: Dict[str, str],
    parent_fields: Optional[List[str]] = None,
    child_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    from src.formatters import format_record as _format_record  # avoid circular refs if any
    return {
        parent_table["name"]: _format_record(parent_record, parent_table, parent_fields),
        child_table["name"]: [_format_record(c, child_table, child_fields) for c in child_records]
    }
