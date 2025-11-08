from google import generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import os

load_dotenv()

gemini_api_key = os.getenv('GEMINI_API_KEY') # giving the apikey stored in .env file

genai.configure(api_key = gemini_api_key)

model = genai.GenerativeModel('gemini-2.0-flash')

# fun to extract from pdf
def extract_text_from_pdf(upload):
    reader = PdfReader(upload)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(upload):
    doc = Document(upload)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text
st.set_page_config(page_title="AI Resume Reviewer", page_icon="💼", layout="centered")
import streamlit as st

# Custom CSS for better UI
st.markdown("""
    <style>
    .stFileUploader label div {
        color: white !important;
        font-weight: bold;
        background-color: #222222;
        border-radius: 10px;
        padding: 12px;
        border: 2px solid #FF69B4;
    }
    .stFileUploader button {
        background-color: #FF69B4 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 8px !important;
        border: none !important;
    }
    .stFileUploader button:hover {
        background-color: #FF1493 !important;
    }
    h1 {
        color: #2E2E3A;
        text-align: center;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)


st.title('AI RESUME REVIEWER')
st.write('By Trishita')
st.write('Upload your Resume in PDF or DOCx format')
upload = st.file_uploader('Upload your file', type = ['pdf','docx'])
if upload is not None:
    if upload.type == 'application/pdf':
        text = extract_text_from_pdf(upload)
    else:
        text = extract_text_from_docx(upload)

    with st.spinner('Analyzing Your Resume...'):
        prompt = f'''
        You are an expert Resume reviwer and a Recruiter.
        Your taks is to Review the Following Resume
        and give suggestions based on the improvements for the job applying for
        1. give a short summary of the candidate
        2. Identify the key skills the candidate has and suggest some improvements in the weak sections.
        3. See any missing details are there and suggest them.
        4. Mainly check for the key details that arecruiter will see in a candidate for the role.
        5. provide an overall rating based on the ATS resume checker. 
        6. ive a rewritten version of the resume based on the improvements and suggestions you have given.

        Resume text:
        {text}
        '''

        response = model.generate_content(prompt)
        st.header('Resume Analysis')
        st.markdown(response.text)
