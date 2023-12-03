import streamlit as st

st.set_page_config(layout="wide")

from st_pages import add_page_title
from streamlit.components.v1 import iframe

SURVEY_URL = "https://gatech.co1.qualtrics.com/jfe/form/SV_0DSIOw3KU4UbYMu"


add_page_title("Survey")

st.markdown(
    """\
We would like to invite you to participate in our survey.
The survey will take about 2 minutes to complete.
Your participation in this study is completely voluntary.

We appreciate your time and thank you for your participation.
"""
)

iframe(SURVEY_URL, height=800, scrolling=True)
