import os
import json
import streamlit as st
from anthropic import Anthropic
from PyPDF2 import PdfReader
from datetime import datetime, timedelta
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import timezone
# ── Clients ───────────────────────────────────────────────────────────────────
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Google Calendar via service account ───────────────────────────────────────
AMANDA_CALENDAR = "amandamah1@gmail.com"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets"
]

def get_google_creds():
    try:
        token_info = json.loads(os.environ.get("GOOGLE_TOKEN", "{}"))
        if not token_info:
            return None
        
        creds = Credentials(
            token=token_info.get("token"),
            refresh_token=token_info.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_info.get("client_id"),
            client_secret=token_info.get("client_secret"),
            scopes=SCOPES
        )
        
        # Auto-refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        return creds
    except Exception as e:
        return None

def get_calendar_events(days_ahead=14):
    """Fetch real events from Amanda's Google Calendar."""
    try:
        creds = get_google_creds()
        if not creds:
            return {"error": "Service account credentials not found"}
        service = build("calendar", "v3", credentials=creds)
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"
        events_result = service.events().list(
            calendarId=AMANDA_CALENDAR,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        busy_slots = []
        for event in events:
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date"))
            end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date"))
            # busy_slots.append({"summary": event.get("summary", "Busy"), "start": start, "end": end})
            
            # Convert UTC to SGT for display
            busy_slots.append({
                "summary": event.get("summary", "Busy"), 
                "start": start,
                "end": end,
                "timezone": "Asia/Singapore"
            })
        return {"busy_slots": busy_slots, "total": len(busy_slots)}
    except Exception as e:
        return {"error": str(e)}

def create_calendar_event(title, start_datetime, end_datetime, attendee_email, description=""):
    """Create a real calendar event and send email invites."""
    try:
        creds = get_google_creds()
        if not creds:
            return {"error": "Service account credentials not found"}
        service = build("calendar", "v3", credentials=creds)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_datetime, "timeZone": "Asia/Singapore"},
            "end": {"dateTime": end_datetime, "timeZone": "Asia/Singapore"},
            "attendees": [
                {"email": AMANDA_CALENDAR},
                {"email": attendee_email}
            ],
            "sendUpdates": "all"
        }
        created = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"
        ).execute()
        return {"success": True, "event_id": created.get("id"), "link": created.get("htmlLink")}
    except Exception as e:
        return {"error": str(e)}

# ── Anthropic tools ───────────────────────────────────────────────────────────
CALENDAR_TOOLS = [
    {
        "name": "get_calendar_availability",
        "description": "Check Amanda's real Google Calendar for busy times in the next 2 weeks so you can suggest free slots.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Days ahead to check. Default 14.", "default": 14}
            },
            "required": []
        }
    },
    {
        "name": "book_calendar_meeting",
        "description": "Create a real Google Calendar event and send email invites to all attendees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_datetime": {"type": "string", "description": "ISO format with SGT offset e.g. 2026-05-27T10:00:00+08:00"},
                "end_datetime": {"type": "string", "description": "ISO format with SGT offset e.g. 2026-05-27T11:00:00+08:00"},
                "attendee_email": {"type": "string", "description": "Visitor email address"},
                "description": {"type": "string", "description": "Event description"}
            },
            "required": ["title", "start_datetime", "end_datetime", "attendee_email"]
        }
    },
    {
        "name": "check_slot_availability",
        "description": "Verify whether a SPECIFIC time slot is free on Amanda's calendar before booking. ALWAYS call this when the visitor requests a custom time that wasn't in the original offered slots.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_datetime": {"type": "string", "description": "ISO format with SGT offset e.g. 2026-06-04T12:30:00+08:00"},
                "end_datetime": {"type": "string", "description": "ISO format with SGT offset e.g. 2026-06-04T13:30:00+08:00"}
            },
            "required": ["start_datetime", "end_datetime"]
        }
    }
]

def handle_tool_call(tool_name, tool_input):
    if tool_name == "get_calendar_availability":
        result = get_calendar_events(tool_input.get("days_ahead", 14))
        return json.dumps(result)
    elif tool_name == "book_calendar_meeting":
        result = create_calendar_event(
            title=tool_input["title"],
            start_datetime=tool_input["start_datetime"],
            end_datetime=tool_input["end_datetime"],
            attendee_email=tool_input["attendee_email"],
            description=tool_input.get("description", "Coffee chat arranged via Amanda's resume chatbot")
        )
        return json.dumps(result)
    elif tool_name == "check_slot_availability":
        result = check_slot_free(tool_input["start_datetime"], tool_input["end_datetime"])
        return json.dumps(result)
    return json.dumps({"error": "Unknown tool"})


def check_slot_free(start_iso, end_iso):
    """Check if a specific slot is free on Amanda's calendar."""
    try:
        creds = get_google_creds()
        if not creds:
            return {"free": False, "error": "No credentials"}
        service = build("calendar", "v3", credentials=creds)
        body = {
            "timeMin": start_iso,
            "timeMax": end_iso,
            "timeZone": "Asia/Singapore",
            "items": [{"id": AMANDA_CALENDAR}]
        }
        result = service.freebusy().query(body=body).execute()
        busy = result["calendars"][AMANDA_CALENDAR]["busy"]
        return {"free": len(busy) == 0, "conflicts": busy}
    except Exception as e:
        return {"free": False, "error": str(e)}

# ── Google Sheets logging ─────────────────────────────────────────────────────
def log_to_sheets(question_summary, topics, meeting_booked):
    try:
        sheet_id = os.environ.get("SHEET_ID", "")
        if not sheet_id:
            return
        creds = get_google_creds()
        if not creds:
            return
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(sheet_id).sheet1
        if not sheet.get_all_values():
            sheet.append_row(["Timestamp", "Question Summary", "Topics", "Meeting Booked"])
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            question_summary, topics,
            "Yes" if meeting_booked else "No"
        ])
    except Exception:
        pass

# ── Resume loader ─────────────────────────────────────────────────────────────
RESUME_FILE_PATH = "Amanda_Mah_Resume_Apr 2026.pdf"

def load_resume_text(filepath):
    try:
        pdf_reader = PdfReader(filepath)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception:
        return ""

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chat with Amanda", page_icon="💼", layout="centered")

st.markdown("""
<style>
  .pill { display:inline-block; font-size:12px; font-weight:500; padding:4px 12px; border-radius:20px; margin:3px 2px; }
  .p-purple { background:#EEEDFE; color:#3C3489; }
  .p-teal   { background:#E1F5EE; color:#0F6E56; }
  .p-blue   { background:#E6F1FB; color:#185FA5; }
  .p-amber  { background:#FAEEDA; color:#854F0B; }
  .bento-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .bento-cell { background:#f8f8f6; border-radius:10px; padding:16px; }
  .bento-title { font-size:14px; font-weight:600; margin:6px 0 4px; color:#1a1a1a; }
  .bento-sub { font-size:13px; color:#666; line-height:1.5; margin:0; }
  .bento-icon { font-size:22px; }
  .stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
  .stat-cell { background:#f8f8f6; border-radius:10px; padding:14px 10px; text-align:center; }
  .stat-n { font-size:24px; font-weight:600; color:#1a1a1a; }
  .stat-l { font-size:11px; color:#888; margin-top:2px; }
  .section-label { font-size:11px; font-weight:600; letter-spacing:.07em; text-transform:uppercase; color:#aaa; margin:0 0 8px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Amanda Mah")
    st.markdown(
        "<p style='font-size:13px;color:#666;line-height:1.6'>"
        "HR Analytics professional at the intersection of people, data, and technology. "
        "10+ years building HR tech in Singapore."
        "</p>",
        unsafe_allow_html=True
    )
    st.divider()
    if os.path.exists(RESUME_FILE_PATH):
        with open(RESUME_FILE_PATH, "rb") as f:
            st.download_button(
                label="📄 Download PDF Resume",
                data=f,
                file_name="Amanda_Resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("Resume PDF not found.")

    # # ── TEMP DEBUG ──
    # st.divider()
    # st.markdown("**🔧 Debug**")
    # creds_check = get_google_creds()
    # st.write(f"Service account: `{'✅ connected' if creds_check else '❌ missing'}`")
    # if st.button("Test Calendar API"):
    #     with st.spinner("Testing..."):
    #         result = get_calendar_events(days_ahead=7)
    #         st.json(result)

# ── About Me ──────────────────────────────────────────────────────────────────
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
    <div class="bento-icon">💡</div>
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

# ── Chatbot ───────────────────────────────────────────────────────────────────
st.markdown("### 💼 Ask me anything about my work experience")

if "resume_context" not in st.session_state:
    st.session_state.resume_context = load_resume_text(RESUME_FILE_PATH) if os.path.exists(RESUME_FILE_PATH) else ""

if "messages" not in st.session_state:
    st.session_state.messages = []

SYSTEM_PROMPT = f"""
You are an AI assistant representing Amanda Mah, an HR Analytics professional based in Singapore.
Answer questions accurately based *only* on the resume context below.
Keep answers conversational, warm, and concise.

CALENDAR BOOKING:
- If the visitor wants to connect, use get_calendar_availability to fetch busy slots,
  then suggest 3 free time slots in SGT (UTC+8).
- IMPORTANT: If the visitor requests a time slot DIFFERENT from the ones you offered,
  you MUST call check_slot_availability first to verify it's free before agreeing.
  If it returns free=false, apologize and offer the original slots again.
- Once visitor confirms a slot and provides name and email, use book_calendar_meeting.
- If book_calendar_meeting returns an error containing "Domain-Wide Delegation" or
  "attendees", respond: "I've reserved the slot on Amanda's calendar! However, the
  automated invite couldn't be sent. Please email Amanda at amandamah1@hotmail.com
  or WhatsApp 92950251 to confirm — mention [date/time] and your email."
- Event title: "Coffee Chat with [visitor name] & Amanda Mah"
- Today is {datetime.now().strftime("%B %d, %Y")}. Never suggest past dates.
- All calendar times are in UTC. Add 8 hours to convert to SGT.
- CRITICAL: Today is {datetime.now().strftime("%A, %B %d, %Y")} SGT.
  When displaying slots, the day name MUST match the actual calendar date in SGT.
  June 3 2026 = Wednesday, June 4 2026 = Thursday, June 5 2026 = Friday, June 6 2026 = Saturday,
  June 7 2026 = Sunday, June 8 2026 = Monday, June 9 2026 = Tuesday.
  Double-check every slot: if the date is June 4 2026, the day MUST be Thursday, not Wednesday.
  - IMPORTANT: If the visitor requests a time slot DIFFERENT from the ones you offered,
  you MUST call check_slot_availability BEFORE booking. Do NOT skip this step.
  If free=false, say "Sorry, that slot isn't available" and re-offer the original 3 slots.
  Only call book_calendar_meeting AFTER check_slot_availability confirms free=true.
...
Resume Context:
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
        with st.spinner("Thinking..."):
            try:
                messages = list(st.session_state.messages)
                while True:
                    response = anthropic_client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        tools=CALENDAR_TOOLS,
                        messages=messages,
                    )
                    if response.stop_reason == "tool_use":
                        messages.append({"role": "assistant", "content": response.content})
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                result = handle_tool_call(block.name, block.input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result
                                })
                        messages.append({"role": "user", "content": tool_results})
                    else:
                        ai_response = next(
                            (b.text for b in response.content if hasattr(b, "text")), ""
                        )
                        st.markdown(ai_response)
                        st.session_state.messages.append({
                            "role": "assistant", "content": ai_response
                        })
                        meeting_booked = any(w in ai_response.lower()
                                           for w in ["booked", "scheduled", "confirmed", "calendar invite"])
                        topics = ", ".join([w for w in ["experience", "skills", "projects", "availability", "booking"]
                                          if w in user_input.lower()]) or "general"
                        log_to_sheets(user_input[:200], topics, meeting_booked)
                        break
            except Exception as e:
                st.error(f"Error: {e}")
