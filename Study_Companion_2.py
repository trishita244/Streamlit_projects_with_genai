import google.generativeai as genai
import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

# Load environment variables
load_dotenv()

# Configure Gemini API
# Ensure 'GENAI_API_KEY' is set in your .env file
genai.configure(api_key=os.getenv('GENAI_API_KEY'))
# Use 'gemini-2.5-flash' for faster and cost-effective text generation
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- Streamlit UI ---
st.set_page_config(layout="wide") # Optional: Use wide layout
st.title('📘 STUDY COMPANION')
st.header('The Ultimate Study Partner 🤖')
st.subheader('Upload your study materials and let your AI companion help you revise, summarize, and practice!')

# --- Functions ---
def extract_text_from_pdf(upload):
    """Extracts text from a PyPDF2 FileObject."""
    reader = PdfReader(upload)
    text = ""
    for page in reader.pages:
        try:
            text += page.extract_text() or ""
        except:
            continue
    return text

def extract_text_from_docx(upload):
    """Extracts text from a docx FileObject."""
    doc = Document(upload)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# --- Initialize session state ---
# Initialize all necessary keys in session state for predictable behavior
for key, default in {
    'text': '',
    'summary': '',
    'mcqs': '',
    'answers': '',
    'show_answers': False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- File Upload ---
# Added 'key' to maintain component identity across reruns
upload = st.file_uploader('📂 Upload your Study Material', type=['pdf', 'docx'], key="file_uploader_widget")

# Extract and save text immediately after upload
if upload is not None:
    extracted_text = ""
    
    # Check if a new file has been uploaded or if the session state text is empty
    # This prevents redundant extraction on every rerun
    try:
        if upload.name.endswith('.pdf'):
            extracted_text = extract_text_from_pdf(upload)
        elif upload.name.endswith('.docx'):
            extracted_text = extract_text_from_docx(upload)

        # Store text persistently only if extraction was successful AND the text has changed
        if extracted_text.strip():
            # Only update if the content has changed to prevent unnecessary re-runs/messages
            if st.session_state.text != extracted_text:
                st.session_state.text = extracted_text
                st.session_state.mcqs = '' # Clear MCQs if new file is uploaded
                st.session_state.summary = '' # Clear summary
                st.success(f"✅ File '{upload.name}' uploaded and text stored! You can now generate content.")
            # Important: Set the file pointer back to the beginning for safe reuse in functions
            upload.seek(0)
        else:
            st.error("❌ Could not extract text from the file. Please try a different document.")
            st.session_state.text = '' # Clear state if extraction fails
    except Exception as e:
        st.error(f"An error occurred during file processing: {e}")
        st.session_state.text = ''

# --- Buttons ---
# Layout buttons side-by-side
col1, col2 = st.columns(2)
with col1:
    summary_btn = st.button('📝 Generate Summary', use_container_width=True)
with col2:
    mcq_btn = st.button('🧠 Generate MCQs for Practice', use_container_width=True)

# --- SUMMARY SECTION ---
if summary_btn:
    # **Crucial Check:** Rely only on the session state text
    if st.session_state.text: 
        prompt = f"""
        Summarize the following study material in a concise, easy-to-understand way.
        Keep key points, definitions, and explanations suitable for revision.

        MATERIAL TO SUMMARIZE:
        {st.session_state.text[:15000]} # Limit text length for prompt safety
        """
        with st.spinner("✨ Generating summary..."):
            response = model.generate_content(prompt)
            st.session_state.summary = response.text
        
        st.header('📄 Summary:')
        st.markdown(st.session_state.summary)
    else:
        st.warning("⚠️ Please upload a study material first!")

# --- Q&A Section (Only appears if a summary has been generated) ---
if st.session_state.summary or st.session_state.text: # Allow Q&A even without explicit summary
    st.markdown("---")
    st.subheader('❓ Ask a Question:')
    
    # Use a form or dedicated button if you want to prevent a rerun on every keystroke
    with st.form("qa_form"):
        ques = st.text_input('Type your question here', key="qa_input")
        ask_btn = st.form_submit_button('Get Answer')
        
    if ask_btn and ques and st.session_state.text:
        q_prompt = f"""
        Based *only* on the uploaded study material provided below, answer the question clearly and concisely.

        Study Material:
        {st.session_state.text[:15000]}

        Question: {ques}
        """
        with st.spinner("💭 Thinking..."):
            q_res = model.generate_content(q_prompt)
        
        st.header('💬 Answer:')
        st.info(q_res.text)

# --- MCQ SECTION ---
if mcq_btn:
    # **Crucial Check:** Rely only on the session state text
    if st.session_state.text: 
        mcq_prompt = f"""
        You are a helpful study companion.
        Create 10 multiple choice questions (MCQs) from the following material.
        format:
        1. question?
        a. option A
        b. option B
        c. option C
        d. option D
        give the question and options on separate lines.
        Each question should have 4 options (A, B, C, D) on separate lines.
        Use Markdown formatting (e.g., **bold**) for the questions.
        Do NOT include the answers yet.

        MATERIAL TO CREATE MCQs FROM:
        {st.session_state.text[:15000]}
        """
        with st.spinner("🧠 Generating MCQs..."):
            res = model.generate_content(mcq_prompt)
            st.session_state.mcqs = res.text
            # Clear answers state so they are regenerated if the MCQs change
            st.session_state.answers = '' 
            st.session_state.show_answers = False
    else:
        st.error("⚠️ Please upload a study material first.")

# --- DISPLAY MCQs ---
if st.session_state.mcqs:
    st.markdown("---")
    st.header("🧩 MCQs for Practice:")
    # Using st.markdown with a slightly modified text to improve display spacing
    st.markdown(st.session_state.mcqs) 

    # --- Show Answers Section ---
    if st.session_state.mcqs: # Check again to ensure MCQs exist
        if not st.session_state.show_answers:
            if st.button("Show Answers", key="show_ans_btn"):
                st.session_state.show_answers = True
                st.experimental_rerun() # Force a rerun to immediately display answers logic
        
        if st.session_state.show_answers:
            if not st.session_state.answers:
                ans_prompt = f"""
                From the following MCQs, give only the correct option letter (A/B/C/D) for each question.
                Format clearly as a Markdown list:
                
                MCQs:
                {st.session_state.mcqs}

                Example Format:
                1. A
                2. B
                3. C
                ...
                """
                with st.spinner("🔍 Fetching answers..."):
                    ans_res = model.generate_content(ans_prompt)
                    st.session_state.answers = ans_res.text

            st.header("✅ Correct Answers:")
            st.info(st.session_state.answers)

            if st.button("Hide Answers", key="hide_ans_btn"):
                st.session_state.show_answers = False
                