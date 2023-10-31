import streamlit as st
from st_pages import Page, show_pages

from review_visualizer.db.session import get_db, init_db

st.set_page_config(
    page_title="Review Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

show_pages(
    [
        Page("review_visualizer/app/pages/home.py", "Home", "🏠"),
        Page("review_visualizer/app/pages/overview.py", "Overview", "📊"),
        Page("review_visualizer/app/pages/example.py", "Example", "❕"),
    ]
)


def initialize_database():
    get_db()
    init_db()


def main():
    st.write("Please select a page from the sidebar to get started.")


if __name__ == "__main__":
    initialize_database()
    main()
