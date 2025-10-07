import streamlit as st
import json, requests, uuid, os, base64
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder  # pip install audio-recorder-streamlit

# ---------- Environment ----------
load_dotenv()
API_URL = os.getenv("API_URL")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_KEY = os.getenv("DEMO_KEY")

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
                    data = {"reply": "🧠 Demo Mode: Pretending to process your voice input."}
                else:
                    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

                    headers = {}
                    if DEMO_KEY:
                        headers["x-demo-key"] = DEMO_KEY

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

                st.chat_message("assistant").markdown(reply, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    st.error("🚫 Unauthorized: Invalid or missing DEMO_KEY.")
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
                    data = {"reply": "💬 Demo Mode: This is a simulated response for demonstration."}
                else:
                    headers = {}
                    if DEMO_KEY:
                        headers["x-demo-key"] = DEMO_KEY

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

                placeholder.markdown(reply, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    placeholder.markdown("🚫 Unauthorized: Invalid or missing DEMO_KEY.")
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
