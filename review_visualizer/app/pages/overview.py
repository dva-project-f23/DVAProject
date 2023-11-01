from typing import Any, List

import streamlit as st
from st_pages import add_page_title
from streamlit_searchbox import st_searchbox

from review_visualizer.db.models import Review
from review_visualizer.db.session import get_db

add_page_title("Overview")

from dataclasses import dataclass


@dataclass
class SearchResults:
    reviewID: int
    reviewerName: str

    def __repr__(self):
        return self.reviewerName


def search_results(query: str) -> List[Any]:
    # Use database to search for query
    with get_db() as db:
        # Use sql like to search for query
        # Return only reviewID and reviewerName
        # Limit to 10 results
        results = (
            db.query(Review.reviewID, Review.reviewerName)
            .filter(Review.reviewerName.like(f"%{query}%"))
            .limit(10)
        )

    return [
        SearchResults(reviewID=reviewID, reviewerName=reviewerName)
        for reviewID, reviewerName in results
    ]


# Search bar
product = st_searchbox(
    search_results,
    placeholder="Search for a product",
    key="product_search",
)
