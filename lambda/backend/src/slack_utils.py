import json, urllib.request, ssl, time
from typing import Dict, Any, Optional, List

from src.config import SLACK_BOT_TOKEN, SLACK_BATCH_SEPARATOR, SLACK_MAX_MESSAGE_SIZE

def send_slack_message(channel: str, text: str) -> Optional[Dict[str, Any]]:
    """Send Slack message."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    }
    payload = json.dumps({
        "channel": channel,
        "text": text,
        "mrkdwn": True
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=10, context=context) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if not result.get("ok"):
                print("Slack error:", result)
            return result
    except Exception as e:
        print(f"Slack post failed: {e}")
        return None

def send_batched_slack_messages(
    results: List[Dict[str, Any]],
    channel_id: str,
    bot_token: str,
    max_chars: int = SLACK_MAX_MESSAGE_SIZE
) -> None:
    """Send Slack messages in batches."""
    if not results or not channel_id or not bot_token:
        return
    batches = []
    current_batch = []
    current_size = 0
    separator_size = len(SLACK_BATCH_SEPARATOR)
    for result in results:
        if not result.get("reports"):
            continue
        link = f"<{result['reports'][0]['url']}|View File>"
        message_block = f"{result['summary']['insights']}\n\n*{result['record_name']} Report:* {link}"
        block_size = len(message_block) + separator_size
        if current_size + block_size > max_chars and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_size = 0
        current_batch.append(message_block)
        current_size += block_size
    if current_batch:
        batches.append(current_batch)
    for i, batch in enumerate(batches):
        header = f"📊 *Report Batch {i+1}/{len(batches)}*\n\n" if len(batches) > 1 else ""
        message = header + SLACK_BATCH_SEPARATOR.join(batch)
        send_slack_message(channel_id, message)
        if i < len(batches) - 1:
            time.sleep(1)
    print(f"✓ Sent {len(results)} reports in {len(batches)} Slack message(s)")
