import streamlit as st
import json, requests, uuid, os, base64, time, random
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder  # pip install audio-recorder-streamlit

# ---------- Environment ----------
load_dotenv()
API_URL = os.getenv("API_URL")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_KEY = os.getenv("DEMO_KEY")

# ---------- Validate Live Mode Configuration ----------
def validate_live_mode_config():
    """Validate that required configuration is present for live mode"""
    if not DEMO_MODE:
        errors = []
        
        if not API_URL or API_URL == "your-api-gateway-endpoint":
            errors.append("❌ **API_URL** is not configured in .env file")
        
        if not DEMO_KEY or DEMO_KEY == "your-secret-key":
            errors.append("❌ **DEMO_KEY** is not configured in .env file")
        
        return errors
    return []

# ---------- Load Demo Responses ----------
def load_demo_responses():
    """Load mock responses from JSON file for demo mode"""
    try:
        with open('demo_responses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"responses": [], "default_response": "💬 Demo Mode: This is a simulated response for demonstration."}

def get_demo_response(query):
    """Get appropriate demo response based on query keywords"""
    demo_data = load_demo_responses()
    query_lower = query.lower()
    
    # Search for matching keywords
    for response_item in demo_data.get("responses", []):
        keywords = response_item.get("keywords", [])
        if any(keyword in query_lower for keyword in keywords):
            return response_item.get("response")
    
    # Return default response if no match found
    default = demo_data.get("default_response", "💬 Demo Mode: This is a simulated response for demonstration.")
    return default.replace("{query}", query)

st.set_page_config(
    page_title="Quickbase Conversational AI powered by Amazon Bedrock",
    page_icon="🤖",
    layout="centered",
)

# ---------- Basic Styling ----------
st.markdown("""
<style>
    body { font-family: 'Inter', sans-serif; }
    .main { background-color: var(--background-color); }

    .app-header { text-align: center; margin-bottom: 1rem; font-weight: 700; font-size: 1.4rem; }
    .app-subtitle { text-align: center; color: gray; margin-top: -0.5rem; font-size: 0.95rem; margin-bottom: 2rem; }

    [data-testid="stChatMessage"] > div {
        border-radius: 16px; padding: 0.75rem 1rem; line-height: 1.6;
        font-size: 1rem; max-width: 720px; margin: 0.35rem auto;
    }
    [data-testid="stChatMessage"][data-testid*="user"] > div {
        background-color: #eef6ff; border: 1px solid #cfe2ff; color: #1e293b;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] > div {
        background-color: #ffffff; border: 1px solid #e5e7eb; color: #111827;
    }

    .footer { text-align: center; margin-top: 2rem; color: gray; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ---------- Session Setup ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    st.caption("Manage your chat session below.")

    # --- Mode indicator ---
    if DEMO_MODE:
        st.warning("🚧 Demo Mode — responses are simulated locally.")
    elif DEMO_KEY:
        st.info("🔒 Private Mode — Secure backend access enabled.")
    else:
        st.error("⚠️ Unauthorized: DEMO_KEY missing. Lambda will reject calls.")

    st.divider()

    # --- Clear chat button ---
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.success("Chat history cleared.")

    st.divider()
    
    # --- Refresh variables button ---
    if st.button("🔄 Refresh Variables"):
        load_dotenv()
        st.rerun()

    st.divider()
    st.subheader("🎙️ Interaction Mode")

    mode_label = "Currently: Voice Mode" if st.session_state.voice_mode else "Currently: Text Mode"
    st.caption(mode_label)
    if st.session_state.voice_mode:
        if st.button("💬 Switch to Text Mode"):
            st.session_state.voice_mode = False
    else:
        if st.button("🎤 Switch to Voice Mode"):
            st.session_state.voice_mode = True

    st.divider()
    st.caption("Session ID")
    st.code(st.session_state.get("session_id", "Not started"), language="bash")

# ---------- Header ----------
st.markdown("""
<div class="app-header">Quickbase Conversational AI powered by Amazon Bedrock</div>
<div class="app-subtitle">A modern conversational interface for your Bedrock Agent.</div>
""", unsafe_allow_html=True)

# ---------- Check Live Mode Configuration ----------
config_errors = validate_live_mode_config()
if config_errors:
    st.error("### ⚠️ Configuration Error")
    for error in config_errors:
        st.markdown(error)
    
    st.info("""
    ### 💡 To run in live mode:
    
    1. **Update your `.env` file** in the `frontend/` directory
    2. **Set API_URL** to your API Gateway endpoint
    3. **Set DEMO_KEY** to match your Lambda configuration
    4. **Restart the app** after updating
    
    **OR**
    
    Switch to **Demo Mode** by setting `DEMO_MODE=true` in `.env`
    """)
    st.stop()

# ---------- Demo Mode Banner ----------
if DEMO_MODE:
    st.info("🧪 **Demo Mode Active** — You are viewing simulated responses with sample data. Connect to AWS to see real Quickbase data.", icon="ℹ️")

# ---------- Display Chat ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ---------- Voice Mode ----------
if st.session_state.voice_mode:
    with st.expander("🎙️ Voice Mode Active — Speak to your Bedrock Agent", expanded=True):
        audio_bytes = audio_recorder(pause_threshold=1.0, sample_rate=44100)
        if audio_bytes:
            st.info("Processing your voice input...")
            try:
                if DEMO_MODE:
                    # Simulate thinking time (3-4 seconds)
                    time.sleep(random.uniform(3.0, 4.0))
                    
                    # Simulate transcription with a random demo query
                    demo_queries = [
                        "Show me support tickets",
                        "List customer records", 
                        "What are the open tasks?",
                        "Show projects and tasks",
                        "Get customers and invoices",
                        "Display orders and items"
                    ]
                    transcribed_text = random.choice(demo_queries)
                    
                    # Use smart demo response matching (same as text mode)
                    demo_response = get_demo_response(transcribed_text)
                    
                    data = {
                        "reply": f"🎙️ **Voice Input Processed**\n\n_Transcribed:_ \"{transcribed_text}\"\n\n---\n\n{demo_response}"
                    }
                else:
                    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

                    headers = {}
                    # Always send x-demo-key header in live mode
                    headers["x-demo-key"] = DEMO_KEY if DEMO_KEY else ""

                    res = requests.post(API_URL, json={
                        "audio_base64": encoded_audio,
                        "session_id": st.session_state.session_id,
                        "voice_mode": True
                    }, headers=headers)
                    res.raise_for_status()
                    data = res.json()

                reply = data.get("reply", "No reply received.")
                url = data.get("url")
                if url:
                    reply += f"\n\n[📎 Download CSV Here]({url})"
                # Escape dollar signs to prevent Streamlit markdown issues
                reply = reply.replace("$", "\\$")

                st.chat_message("assistant").markdown(reply, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Display AI transparency actions if present
                actions = data.get("actions", [])
                if actions:
                    with st.expander("What happened behind the scenes?"):
                        for act in actions:
                            st.markdown(f"- **{act['service']}**: {act['action']}")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    st.error("🚫 Unauthorized: Invalid or missing DEMO_KEY.")
                elif e.response.status_code == 500:
                    error_body = e.response.json() if e.response.headers.get('content-type') == 'application/json' else {}
                    error_msg = error_body.get('error', str(e))
                    if 'DEMO_KEY' in error_msg or 'misconfiguration' in error_msg.lower():
                        st.error("⚙️ **Server Configuration Error:** DEMO_KEY is not configured in the Lambda function. Contact your administrator.")
                    else:
                        st.error(f"🔧 Server Error: {error_msg}")
                else:
                    st.error(f"API Error: {e}")
            except Exception as e:
                st.error(f"Audio processing failed: {e}")

# ---------- Text Mode ----------
else:
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("_Thinking..._")

            try:
                if DEMO_MODE:
                    # Simulate thinking time (3-4 seconds)
                    time.sleep(random.uniform(3.0, 4.0))
                    # Use smart demo response matching
                    reply = get_demo_response(prompt)
                    data = {"reply": reply}
                else:
                    headers = {}
                    # Always send x-demo-key header in live mode
                    headers["x-demo-key"] = DEMO_KEY if DEMO_KEY else ""

                    res = requests.post(API_URL, json={
                        "prompt": prompt,
                        "session_id": st.session_state.session_id
                    }, headers=headers)
                    res.raise_for_status()
                    data = res.json()

                reply = data.get("reply", "No reply received.")
                url = data.get("url")
                if url:
                    reply += f"\n\n[📎 Download CSV Here]({url})"
                # Escape dollar signs to prevent Streamlit markdown issues
                reply = reply.replace("$", "\\$")

                placeholder.markdown(reply, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Display AI transparency actions if present
                actions = data.get("actions", [])
                if actions:
                    with st.expander("What happened behind the scenes?"):
                        for act in actions:
                            st.markdown(f"- **{act['service']}**: {act['action']}")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    placeholder.markdown("🚫 Unauthorized: Invalid or missing DEMO_KEY.")
                elif e.response.status_code == 500:
                    try:
                        error_body = e.response.json() if e.response.headers.get('content-type') == 'application/json' else {}
                        error_msg = error_body.get('error', str(e))
                        if 'DEMO_KEY' in error_msg or 'misconfiguration' in error_msg.lower():
                            placeholder.markdown("⚙️ **Server Configuration Error:** DEMO_KEY is not configured in the Lambda function. Contact your administrator.")
                        else:
                            placeholder.markdown(f"🔧 Server Error: {error_msg}")
                    except:
                        placeholder.markdown(f"🔧 Server Error: {e}")
                else:
                    placeholder.markdown(f"API Error: {e}")
            except Exception as e:
                placeholder.markdown(f"Error: {e}")

# ---------- Footer ----------
st.markdown("""
<div class="footer">
    Built with Streamlit • Amazon Bedrock • AWS Lambda • API Gateway
</div>
""", unsafe_allow_html=True)
