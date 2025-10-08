import json
import boto3
import os
import sys
import traceback
import base64
import asyncio
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler


# ---------- Logging ----------
def log(msg):
    print(msg)
    sys.stdout.flush()


# ---------- Environment ----------
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_API_KEY = os.getenv("DEMO_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")
ALIAS_ID = os.getenv("ALIAS_ID")
REGION = os.getenv("REGION", "us-east-1")

# AWS clients (only initialized in non-demo mode)
bedrock = boto3.client("bedrock-agent-runtime", region_name=REGION)


# ---------- Transcribe Event Handler ----------
class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, transcript_result_stream):
        super().__init__(transcript_result_stream)
        self.full_text = ""

    async def handle_transcript_event(self, transcript_event):
        results = transcript_event.transcript.results
        for result in results:
            if result.alternatives and not result.is_partial:
                self.full_text += result.alternatives[0].transcript.strip() + " "


# ---------- Async Transcribe ----------
async def transcribe_audio(audio_bytes: bytes) -> str:
    """Stream audio bytes to Amazon Transcribe and return transcript."""
    client = TranscribeStreamingClient(region=REGION)
    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=44100,
        media_encoding="pcm"
    )

    handler = MyEventHandler(stream.output_stream)

    async def send_audio():
        chunk_size = 1024 * 16
        for i in range(0, len(audio_bytes), chunk_size):
            await stream.input_stream.send_audio_event(audio_chunk=audio_bytes[i:i+chunk_size])
        await stream.input_stream.end_stream()

    await asyncio.gather(send_audio(), handler.handle_events())
    return handler.full_text.strip()


# ---------- Lambda Handler ----------
def lambda_handler(event, context):
    log("===== INVOCATION START =====")

    try:
        # --- Parse body & headers ---
        headers = event.get("headers", {}) or {}
        body_raw = event.get("body", "{}")
        body = json.loads(body_raw)
        session_id = body.get("session_id", "default-session")
        prompt = body.get("prompt")
        audio_base64 = body.get("audio_base64")

        # --- Validate demo key ---
        received_key = headers.get("x-demo-key")
        if not DEMO_MODE:
            if not DEMO_API_KEY:
                log("Missing DEMO_API_KEY in environment")
                return {
                    "statusCode": 500,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({"error": "Server misconfiguration: DEMO_API_KEY not set"})
                }

            if received_key != DEMO_API_KEY:
                log("Unauthorized request: invalid or missing DEMO_API_KEY")
                return {
                    "statusCode": 403,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({"error": "Unauthorized: Invalid or missing DEMO_API_KEY"})
                }

        # --- DEMO MODE (no AWS cost) ---
        if DEMO_MODE:
            log("DEMO MODE ENABLED — returning static response")
            fake_response = {
                "reply": "Demo Mode: This is a simulated Bedrock response.",
                "session_id": session_id,
            }
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json",
                },
                "body": json.dumps(fake_response),
            }

        # --- Transcribe Audio if Present ---
        if audio_base64:
            log("Decoding audio and starting transcription...")
            audio_bytes = base64.b64decode(audio_base64)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            transcript = loop.run_until_complete(transcribe_audio(audio_bytes))
            log(f"Transcribed Text: {transcript}")
            prompt = transcript or "Unable to transcribe audio."

        # --- Validate prompt ---
        if not prompt:
            raise ValueError("No 'prompt' or 'audio_base64' provided in request.")

        # --- Invoke Bedrock Agent ---
        log("Invoking Bedrock Agent...")
        response = bedrock.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=session_id,
            inputText=prompt,
        )

        reply_text = ""
        csv_url = None
        for event_item in response["completion"]:
            if "chunk" in event_item:
                chunk_str = event_item["chunk"]["bytes"].decode("utf-8")
                try:
                    chunk_json = json.loads(chunk_str)
                    if "text" in chunk_json:
                        reply_text += chunk_json["text"]
                    if "url" in chunk_json:
                        csv_url = chunk_json["url"]
                except json.JSONDecodeError:
                    reply_text += chunk_str
            elif "completion" in event_item:
                break

        log(f"Final Reply: {reply_text.strip()}")
        log(f"CSV URL: {csv_url}")

        # --- Build Response ---
        result = {
            "reply": reply_text.strip(),
            "url": csv_url,
            "session_id": session_id,
        }

        if audio_base64:
            result["transcribed_text"] = prompt

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json",
            },
            "body": json.dumps(result),
        }

    except Exception as e:
        log("===== ERROR =====")
        log(f"{type(e).__name__}: {e}")
        log(traceback.format_exc())
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
