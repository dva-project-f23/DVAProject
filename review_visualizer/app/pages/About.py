import os
import streamlit as st
from docx import Document

st.set_page_config(layout="wide")

st.title("About")

# Path to your .docx file
docx_file_path = os.path.join(os.path.dirname(__file__), "About.docx")

# Function to read .docx file
def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Display the contents of the .docx file
doc_content = read_docx(docx_file_path)
st.write(doc_content)
