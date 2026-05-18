import os
import streamlit as st
from google import genai
from google.genai import types
from PyPDF2 import PdfReader

# Initialize Gemini Client
client = genai.Client()

# 1. Function to read the file for the AI context
def load_resume_text(filepath):
    try:
        pdf_reader = PdfReader(filepath)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return ""

# Define the local path where your resume file lives in your project folder
RESUME_FILE_PATH = "my_resume.pdf"

# Streamlit UI Setup
st.set_page_config(page_title="AI Resume Chatbot", page_icon="💼")
st.title("💼 AI Resume Chatbot")

# 2. Sidebar with Download Button
with st.sidebar:
    st.header("About Me")
    st.write("Welcome to my interactive portfolio. Feel free to ask the AI any questions about my background.")
    
    # Check if the file exists before showing the button
    if os.path.exists(RESUME_FILE_PATH):
        with open(RESUME_FILE_PATH, "rb") as file:
            st.download_button(
                label="📄 Download My PDF Resume",
                data=file,
                file_name="Amanda_Resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("Resume PDF file not found on the server.")

# Automatically load context for the AI
if "resume_context" not in st.session_state:
    if os.path.exists(RESUME_FILE_PATH):
        st.session_state.resume_context = load_resume_text(RESUME_FILE_PATH)
    else:
        st.session_state.resume_context = ""

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# System instructions using the hosted context
system_instruction = f"""
You are an AI assistant representing the candidate whose resume is provided below. 
Answer questions accurately based *only* on the provided resume context.

Candidate Resume Context:
\"\"\"
{st.session_state.resume_context}
\"\"\"
"""

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if user_input := st.chat_input("Ask me about my experience..."):
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