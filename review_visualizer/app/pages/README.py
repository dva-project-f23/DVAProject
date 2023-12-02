import os
import streamlit as st

st.set_page_config(layout="wide")


st.title("README")

with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as f:
    st.markdown(about_file.read())
