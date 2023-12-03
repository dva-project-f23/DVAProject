import os

import streamlit as st

st.set_page_config(layout="wide")


st.title("README")

with open(os.path.join(os.getcwd(), "README.md"), "r") as f:
    st.markdown(f.read())
