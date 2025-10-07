import base64, json, urllib.request, ssl, re
from typing import Optional, Any
from datetime import datetime

from src.config import s3, S3_BUCKET, PRESIGNED_URL_EXPIRATION
from src.quickbase_api import qb_headers

def process_attachment(
    table_id: str,
    record_id: int,
    field_id: int,
    version: int = 1,
    s3_name_prefix: str = "record"
) -> Optional[str]:
    """
    Download any file from Quickbase and upload to S3.
    Supports binary files, Base64-encoded RTF, and plain text.
    """
    try:
        url = f"https://api.quickbase.com/v1/files/{table_id}/{record_id}/{field_id}/{version}"
        req = urllib.request.Request(url, headers=qb_headers(), method="GET")
        context = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=60, context=context) as resp:
            file_data = resp.read()
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
        if file_data.startswith(b"e1xydGY"):
            try:
                decoded = base64.b64decode(file_data)
                if decoded.startswith(b"{\\rtf"):
                    print("INFO: Decoded Base64 RTF content")
                    file_data = decoded
                    content_type = "application/rtf"
            except Exception as e:
                print(f"WARNING: Failed to decode Base64 RTF: {e}")
        ext_map = {
            "application/pdf": ".pdf",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "text/plain": ".txt",
            "application/rtf": ".rtf",
            "application/json": ".json",
            "text/csv": ".csv",
        }
        ext = ext_map.get(content_type, ".bin")
        key = f"attachments/{s3_name_prefix}_{record_id}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}{ext}"
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=file_data, ContentType=content_type)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        print(f"INFO: Uploaded attachment for record {record_id} ({content_type}, {len(file_data)} bytes)")
        return url
    except Exception as e:
        print(f"Attachment download failed for record {record_id}: {e}")
        return None

def _is_qb_attachment_value(val: Any) -> bool:
    return isinstance(val, dict) and any(k in val for k in ("url", "fileName", "contentType", "versionNumber"))
