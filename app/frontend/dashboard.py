import streamlit as st
import requests
import time
import base64
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8502")  # Fixed port + IP

st.set_page_config(page_title="FlowScribe", layout="wide")
st.title("FlowScribe – Real-time Transcription Tool")

# Force longer default timeout
requests.adapters.DEFAULT_TIMEOUT = 30

# ────────────────────────────────────────────────
# Sidebar – Keywords
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("Keyword Configuration")

    try:
        resp = requests.get(f"{BACKEND_URL}/keywords", timeout=30)
        keywords = resp.json().get("keywords", ["vote", "motion", "objection", "bill passed", "adjourned"])
    except Exception as e:
        keywords = ["vote", "motion", "objection", "bill passed", "adjourned"]
        st.warning(f"Could not load keywords: {str(e)}")

    new_kw = st.text_input("Add new keyword")
    if st.button("Add Keyword") and new_kw.strip():
        try:
            requests.post(f"{BACKEND_URL}/add_keyword", json={"keyword": new_kw.strip()}, timeout=30)
        except Exception as e:
            st.error(f"Add failed: {e}")
        st.rerun()

    for kw in keywords[:]:
        cols = st.columns([5,1])
        cols[0].write(kw)
        if cols[1].button("×", key=f"del_{kw}"):
            try:
                requests.post(f"{BACKEND_URL}/remove_keyword", json={"keyword": kw}, timeout=30)
            except Exception as e:
                st.error(f"Remove failed: {e}")
            st.rerun()

# ────────────────────────────────────────────────
# Main area
# ────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Live Transcript")
    transcript_placeholder = st.empty()

with col2:
    st.subheader("Alerts")
    alert_placeholder = st.empty()

# ────────────────────────────────────────────────
# Stream controls
# ────────────────────────────────────────────────
st.subheader("Manage Streams")
url = st.text_input("Stream URL", placeholder="https://www.youtube.com/live/... (must be LIVE now)")
source_type = st.radio("Type", ["rtsp", "youtube"], horizontal=True)

c1, c2 = st.columns(2)
if c1.button("Start Stream"):
    if url.strip():
        try:
            r = requests.post(
                f"{BACKEND_URL}/start_stream",
                params={"url": url.strip(), "source_type": source_type},
                timeout=60  # Extra long for model init
            )
            st.success(r.json().get("message", "Started"))
        except Exception as e:
            st.error(f"Failed to start: {str(e)}")
    else:
        st.warning("Enter a LIVE URL first")

if c2.button("Stop All Streams"):
    try:
        # Get current active URLs from a new endpoint or simulate (for MVP, call stop on known URLs or add /stop_all)
        # For now, stop all known processors via new endpoint (add below)
        r = requests.post(f"{BACKEND_URL}/stop_all", timeout=30)
        st.success(r.json().get("message", "All streams stopped"))
    except Exception as e:
        st.error(f"Stop failed: {str(e)}")

# Download hint
if st.button("Download Transcript"):
    st.info("Check product_created/transcripts/ manually")

# Preload beep (optional)
BEEP_FILE = "beep.wav"
beep_data = None
if os.path.exists(BEEP_FILE):
    with open(BEEP_FILE, "rb") as f:
        beep_data = f.read()

# ────────────────────────────────────────────────
# Live update loop (longer timeout)
# ────────────────────────────────────────────────
while True:
    try:
        data = requests.get(f"{BACKEND_URL}/transcript", timeout=30).json()  # 30s timeout
        transcript = data.get("transcript", "No stream started yet...")
        transcript_placeholder.markdown(f"```\n{transcript}\n```")

        alerts = data.get("alerts", [])
        if alerts:
            alert_placeholder.warning("\n".join(alerts[-5:]))
            if beep_data:
                encoded = base64.b64encode(beep_data).decode()
                alert_placeholder.markdown(
                    f'<audio autoplay="true" src="data:audio/wav;base64,{encoded}"></audio>',
                    unsafe_allow_html=True
                )
        else:
            alert_placeholder.info("No alerts yet")

    except Exception as e:
        transcript_placeholder.error(f"Backend error: {str(e)} – Check backend terminal")

    time.sleep(5)  # Poll every 5s to reduce load