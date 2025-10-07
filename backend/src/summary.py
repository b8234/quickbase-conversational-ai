from typing import Dict, List, Any

def generate_summary(records: List[Dict[str, Any]], table_name: str, rec_name: str) -> Dict[str, Any]:
    """Generate analytical summary for any table."""
    if not records:
        return {
            "title": f"{rec_name} Summary",
            "statistics": {"total_records": 0},
            "insights": f"No {table_name} records found matching your criteria.",
            "bedrock_context": "No matching records found."
        }
    total = len(records)
    stats = {"total_records": total}
    field_analysis = {}
    date_fields = []
    for record in records:
        for field_name, value in record.items():
            if value is None or value == "":
                continue
            if field_name not in field_analysis:
                field_analysis[field_name] = {"values": {}, "type": None}
            str_val = str(value)
            field_analysis[field_name]["values"][str_val] = field_analysis[field_name]["values"].get(str_val, 0) + 1
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                field_analysis[field_name]["type"] = "numeric"
            elif "date" in field_name.lower() or "created" in field_name.lower():
                field_analysis[field_name]["type"] = "date"
                date_fields.append(value)
    key_fields = []
    for field, data in field_analysis.items():
        value_count = len(data["values"])
        if 2 <= value_count <= 10 and len(records) > value_count:
            breakdown = ", ".join([
                f"{count} {val}"
                for val, count in sorted(data["values"].items(), key=lambda x: -x[1])[:5]
            ])
            stats[field] = breakdown
            key_fields.append(field)
    if date_fields:
        try:
            sorted_dates = sorted([d for d in date_fields if d])
            if sorted_dates:
                stats["date_range"] = f"{sorted_dates[0]} to {sorted_dates[-1]}"
        except:
            pass
    insights = []
    insights.append(f"*{rec_name} Overview:*")
    insights.append(f"• Total {table_name.lower()}: {total}")
    for field in key_fields[:3]:
        insights.append(f"• {field}: {stats[field]}")
    if "date_range" in stats:
        insights.append(f"• Date range: {stats['date_range']}")
    insights.append("\nReview the attached report for complete details.")
    bedrock_context = (
        f"Analyze this {table_name} data and provide 1-2 sentences about patterns, "
        f"trends, or notable observations. Consider {', '.join(key_fields[:2]) if key_fields else 'all fields'}."
    )
    return {
        "title": f"{rec_name} {table_name} Summary",
        "statistics": stats,
        "insights": "\n".join(insights),
        "bedrock_context": bedrock_context,
        "raw_data_sample": records[:3] if len(records) > 3 else records
    }
