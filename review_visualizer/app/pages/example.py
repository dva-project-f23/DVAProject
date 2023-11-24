import pandas as pd
import streamlit as st
from st_pages import add_page_title

from review_visualizer.db.session2 import get_db
from review_visualizer.visualizations.graphs import example_graph

add_page_title("Example")

st.write("This is an example problem visualization")

# Example way to load data
# with st.spinner("Loading data..."):
#     db = get_db()
#     df = db.get_dataframe("reviews")

# For now, generate dummy data.
with st.spinner("Loading data..."):
    df = pd.DataFrame(
        {
            "Rating": [1, 2, 3, 4, 5],
            "Count": [10, 20, 30, 40, 50],
        }
    )

st.plotly_chart(example_graph.show(df))
