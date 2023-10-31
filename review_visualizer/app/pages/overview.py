from typing import Any, List

import streamlit as st
from st_pages import add_page_title
from streamlit_searchbox import st_searchbox

add_page_title("Overview")


def search_results(query: str) -> List[Any]:
    # Use database to search for query
    pass


# Search bar
product = st_searchbox(
    search_results,
    placeholder="Search for a product",
    key="product_search",
)
