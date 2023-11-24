import asyncio
import html
from typing import Any, List

import streamlit as st
from st_pages import add_page_title
from streamlit_searchbox import st_searchbox

from review_visualizer.db.prisma import PrismaClient

add_page_title("Overview")

from dataclasses import dataclass


@dataclass
class SearchResults:
    asin: str
    title: str

    def __repr__(self):
        return html.unescape(self.title)


async def search_results(query: str) -> List[Any]:
    # Use database to search for query
    async with PrismaClient() as prisma:
        results = await prisma.product.find_many(
            where={
                "title": {
                    "contains": query,
                }
            },
            take=10,
        )

    return [
        SearchResults(
            asin=result.asin,
            title=result.title,
        )
        for result in results
    ]


def search_results_sync(query: str) -> List[Any]:
    return asyncio.run(search_results(query))


# Search bar
product = st_searchbox(
    search_results_sync,
    placeholder="Search for a product",
    key="product_search",
)
