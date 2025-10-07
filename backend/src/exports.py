import io, csv
from typing import Any, Optional, Dict, List

from src.config import s3, S3_BUCKET, PRESIGNED_URL_EXPIRATION
from datetime import datetime

def save_to_s3(
    data: Any,
    prefix: str = "reports",
    record_name: Optional[str] = None,
    expires: Optional[int] = None
) -> str:
    """
    Save report to S3 as CSV only.
    """
    if expires is None:
        expires = PRESIGNED_URL_EXPIRATION
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    key = f"{prefix}/{record_name or 'all'}_{timestamp}.csv"
    if not data or not isinstance(data, (list, tuple)) or not isinstance(data[0], dict):
        raise ValueError("CSV export expects a non-empty list of dictionaries")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    body = output.getvalue()
    print(f"Uploading CSV: {len(body.encode('utf-8'))/1000:.1f}KB → s3://{S3_BUCKET}/{key}")
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body, ContentType="text/csv")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires
    )

def save_all_formats(
    data: Any,
    rec_name: str,
    formats: List[str],
    parent: Optional[Dict[str, str]] = None,
    child: Optional[Dict[str, str]] = None,
    summary: Optional[str] = None
) -> Dict[str, str]:
    """
    CSV-only version of save_all_formats().
    """
    urls: Dict[str, str] = {}
    try:
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise ValueError("CSV export expects list of dicts")
        print(f"Saving {len(data)} record(s) to CSV for '{rec_name}'...")
        urls["csv"] = save_to_s3(data, prefix="reports", record_name=rec_name)
        print(f"SUCCESS: Saved CSV → {urls['csv']}")
    except Exception as e:
        print(f"ERROR: Failed to save CSV for {rec_name}: {e}")
        import traceback; traceback.print_exc()
    return urls
