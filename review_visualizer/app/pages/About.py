import os
import streamlit as st

st.set_page_config(layout="wide")


st.title("About")

with open(os.path.join(os.getcwd(), "about.md"), "r") as f:
    st.markdown(f.read())
