import os
import streamlit as st
from google import genai
from google.genai import types
from PyPDF2 import PdfReader

# Initialize Gemini Client
client = genai.Client()

def load_resume_text(filepath, output_filepath="extracted_resume.txt"):
    try:
        pdf_reader = PdfReader(filepath)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if text.strip():
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(text)
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return ""

RESUME_FILE_PATH = "Amanda_Mah_Resume_Apr 2026.pdf"

st.set_page_config(page_title="Chat with Amanda", page_icon="💼", layout="centered")

# --- Shared styles ---
st.markdown("""
<style>
  .pill {
    display: inline-block; font-size: 12px; font-weight: 500;
    padding: 4px 12px; border-radius: 20px; margin: 3px 2px;
  }
  .p-purple { background: #EEEDFE; color: #3C3489; }
  .p-teal   { background: #E1F5EE; color: #0F6E56; }
  .p-blue   { background: #E6F1FB; color: #185FA5; }
  .p-amber  { background: #FAEEDA; color: #854F0B; }
  .bento-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .bento-cell { background: #f8f8f6; border-radius: 10px; padding: 16px; }
  .bento-title { font-size: 14px; font-weight: 600; margin: 6px 0 4px; color: #1a1a1a; }
  .bento-sub { font-size: 13px; color: #666; line-height: 1.5; margin: 0; }
  .bento-icon { font-size: 22px; }
  .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .stat-cell { background: #f8f8f6; border-radius: 10px; padding: 14px 10px; text-align: center; }
  .stat-n { font-size: 24px; font-weight: 600; color: #1a1a1a; }
  .stat-l { font-size: 11px; color: #888; margin-top: 2px; }
  .section-label {
    font-size: 11px; font-weight: 600; letter-spacing: .07em;
    text-transform: uppercase; color: #aaa; margin: 0 0 8px;
  }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Amanda Mah")
    st.markdown(
        "<p style='font-size:13px;color:#666;line-height:1.6'>"
        "HR Analytics professional at the intersection of people, data, and technology. "
        "10+ years building HR tech. Senator, I'm Singaporean."
        "</p>",
        unsafe_allow_html=True
    )
    st.divider()

    if os.path.exists(RESUME_FILE_PATH):
        with open(RESUME_FILE_PATH, "rb") as file:
            st.download_button(
                label="📄 Download PDF Resume",
                data=file,
                file_name="Amanda_Resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("Resume PDF not found.")

# --- About Me Section ---
st.markdown("""
<div style="display:flex; align-items:center; gap:16px; margin-bottom:20px; margin-top:8px">
  <div style="width:56px;height:56px;border-radius:50%;background:#EEEDFE;color:#3C3489;
              display:flex;align-items:center;justify-content:center;font-size:18px;
              font-weight:600;flex-shrink:0;">AM</div>
  <div>
    <h2 style="margin:0; font-size:22px">Hi, I love turning ideas into meaningful experiences at the intersection of design, technology, and the world of work.</h2>
    <p style="margin:4px 0 0; color:#666; font-size:14px">
      People analyst. Pipeline builder. Occasional destroyer of unnecessary spreadsheets and steps.
    </p>
  </div>
</div>
<p style="font-size:15px; line-height:2; color:#666; margin-bottom:20px">
  I'm an HR Analytics professional with a Computing background and 10+ years at the
  intersection of people, data, and tech. My job is to bridge the gap between
  <em>"HR data"</em> and <em>"what you should actually do about it"</em>
  — and to build the infrastructure so that conversation can happen again tomorrow, automatically.
</p>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stat-grid">
  <div class="stat-cell"><div class="stat-n">10+</div><div class="stat-l">Years in HR tech</div></div>
  <div class="stat-cell"><div class="stat-n">3</div><div class="stat-l">HRIS platforms shipped</div></div>
  <div class="stat-cell"><div class="stat-n">IHRP-CP</div><div class="stat-l">Certified practitioner</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="bento-grid">
  <div class="bento-cell">
    <div class="bento-icon">🗄️</div>
    <p class="bento-title">Data infrastructure</p>
    <p class="bento-sub">Snowflake pipelines, Power BI dashboards, and architecture that doesn't collapse when someone adds a new column.</p>
  </div>
  <div class="bento-cell">
    <div class="bento-icon">⚙️</div>
    <p class="bento-title">Automation & code</p>
    <p class="bento-sub">Python, VBA, RPA — if a human is doing a repetitive data task, I'm probably already writing something to fix that.</p>
  </div>
  <div class="bento-cell">
    <div class="bento-icon">👥</div>
    <p class="bento-title">People analytics</p>
    <p class="bento-sub">Translating HR business problems into actual insights. Not just charts — answers.</p>
  </div>
  <div class="bento-cell">
    <div class="bento-icon">🤖</div>
    <p class="bento-title">AI strategy</p>
    <p class="bento-sub">Building capability so HR teams can actually use AI — not just talk about it at conferences.</p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<p class="section-label">Tech stack</p>', unsafe_allow_html=True)
st.markdown("""
<div style="line-height:2.4; margin-bottom:8px">
  <span class="pill p-teal">❄️ Snowflake</span>
  <span class="pill p-teal">📊 Power BI</span>
  <span class="pill p-purple">🐍 Python</span>
  <span class="pill p-purple">📋 VBA</span>
  <span class="pill p-purple">🔄 RPA</span>
  <span class="pill p-blue">🏢 Workday</span>
  <span class="pill p-blue">🏢 SAP SuccessFactors</span>
  <span class="pill p-blue">🏢 SAP HCM</span>
  <span class="pill p-amber">🎓 IHRP-CP</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Chatbot Section ---
st.markdown("### 💼 Ask me anything about my work experience")

if "resume_context" not in st.session_state:
    if os.path.exists(RESUME_FILE_PATH):
        st.session_state.resume_context = load_resume_text(RESUME_FILE_PATH)
    else:
        st.session_state.resume_context = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

system_instruction = f"""
You are an AI assistant representing Amanda Mah, the candidate whose resume is provided below.
Answer questions accurately based *only* on the provided resume context.
Keep answers conversational, warm, and concise — you're representing a real person.

Candidate Resume Context:
\"\"\"
{st.session_state.resume_context}
\"\"\"
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("CHAT HERE >>> Ask about my experience, skills, or projects..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        try:
            history_contents = [
                types.Content(
                    role="user" if msg["role"] == "user" else "model",
                    parts=[types.Part.from_text(text=msg["content"])]
                ) for msg in st.session_state.messages
            ]

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=history_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )

            ai_response = response.text
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})

        except Exception as e:
            st.error(f"Error: {e}")
