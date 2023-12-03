import init_prisma  # Init Prisma Client
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from st_pages import Page, show_pages

st.set_page_config(
    layout="wide",
    page_title="Review Visualizer",
    page_icon="📊",
    initial_sidebar_state="auto",
)

show_pages(
    [
        Page("review_visualizer/app/pages/home.py", "Home", "🏠"),
        Page("review_visualizer/app/pages/about.py", "About", "i"),
        Page("review_visualizer/app/pages/readme.py", "ReadMe", "📖"),
        Page("review_visualizer/app/pages/overview.py", "Overview", "📊"),
        Page("review_visualizer/app/pages/survey.py", "Survey", "📝"),
    ]
)


def main():
    st.write("Please select a page from the sidebar to get started.")


if __name__ == "__main__":
    main()
