# field_allowlist.py
# Per-table allow lists by *label*. Only these labels will be queried/formatted.
# 
# SPECIAL MARKERS (optional - for explicit control):
# - Add "[KEY]" suffix to mark the primary search field (e.g., "Customer Name [KEY]")
# - Add "[DATE]" suffix to mark the date filter field (e.g., "Date Opened [DATE]")
# - Add "[RELATED KEY]" suffix to mark relationship fields for searching (e.g., "Related Customer [RELATED KEY]")
# - Add "[UNIQUE]" suffix to mark fields that should ONLY be searched when contextually relevant
#   (e.g., "Ticket ID [UNIQUE]", "Email [UNIQUE]", "Phone [UNIQUE]")
# 
# If no [KEY] marker, auto-detection will find fields with "name", "customer", "title", etc.
# If no [DATE] marker, auto-detection will find fields with "date", "created", "opened", etc.
# [RELATED KEY] fields will be combined with [KEY] fields in searches using OR logic.
# [UNIQUE] fields are only searched when query contains matching keywords (ticket→Ticket ID, email→Email, etc.)

ALLOW_LISTS = {
    "Customers": {
        "id": "your-table-id",
        "fields": [
            "Record ID# [KEY]",
            "Customer Name [UNIQUE]",
            "Contact Person",
            "Email",
            "Phone",
            "Account Type",
            "Annual Revenue"
        ]
    },
    "Customer Support Tickets": {
        "id": "your-table-id",
        "fields": [
            "Record ID# [KEY]",
            "Ticket Id [UNIQUE]",
            "Issue Description",
            "Priority",
            "Status",
            "Date Opened [DATE]",
            "Related Customer [RELATED KEY]",
            "Customer Name",
            "Attachment",
            "Has Attachment?"
        ]
    }
}
