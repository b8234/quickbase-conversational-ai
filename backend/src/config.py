import os, json, io, csv, boto3, urllib.request, ssl, re, time, traceback, logging, base64
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from field_allowlist import ALLOW_LISTS

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Environment variables
QB_APP_ID = os.getenv("QB_APP_ID")
QB_REALM = os.getenv("QB_REALM")
QB_USER_TOKEN = os.getenv("QB_USER_TOKEN")

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("AWS_REGION_NAME")

SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Query thresholds
QB_LARGE_QUERY_THRESHOLD = int(os.getenv("QB_LARGE_QUERY_THRESHOLD", "20000"))
PRESIGNED_URL_EXPIRATION = int(os.getenv("PRESIGNED_URL_EXPIRATION", "3600"))
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", "104857600"))

# Feature flags
EXPORT_FLATTEN_MODE = os.getenv("EXPORT_FLATTEN_MODE", "true").lower() == "true"
INCLUDE_ATTACHMENTS = os.getenv("INCLUDE_ATTACHMENTS", "false").lower() == "true"

# Slack constants
SLACK_MAX_MESSAGE_SIZE = 3500
SLACK_BATCH_SEPARATOR = "\n\n" + "─" * 50 + "\n\n"

# AWS Clients
s3 = boto3.client("s3", region_name=S3_REGION)
cloudwatch = boto3.client("cloudwatch", region_name=S3_REGION)

# Cache expiration time in seconds (default 10 minutes)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "600"))
