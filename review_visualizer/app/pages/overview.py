import asyncio
import html
from typing import Any, List
import pandas as pd

import streamlit as st
from st_pages import add_page_title
from streamlit_searchbox import st_searchbox

from review_visualizer.db.prisma import PrismaClient
from review_visualizer.visualizations.graphs import example_graph
from moving_average import ma_average
from datetime import datetime
from dateutil import relativedelta

add_page_title("Overview")

from dataclasses import dataclass


@dataclass
class SearchResults:
    asin: str
    title: str
    price: float
    brand: str

    def __repr__(self):
        return html.unescape(self.title)


async def search_results(query: str) -> List[Any]:
    # Use database to search for query
    async with PrismaClient() as prisma:
        results = await prisma.product.find_many(
            where={
                'AND': [
                    {
                        "title": {
                            "contains": query,
                        },
                    },
                    {
                        "reviews": {
                            "some": {
                                "overall": {
                                    'gte': 0.0
                                }
                            }
                        }
                    }
                ]
            },
            take=5,
        )

    return [
        SearchResults(
            asin=result.asin,
            title=result.title,
            price=result.price,
            brand=result.brand,
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

if product:
    st.write("Amazon Standard Identification Number: " + product.asin)
    if (product.brand == None):
        st.write("Brand: n/a")
    else:
        st.write("Brand: " + product.brand)
    if (product.price == None):
        st.write("Price: n/a")
    else:
        st.write("Price: " + str(round(product.price, 2)) + " $")
    df, total_reviews = asyncio.run(ma_average.movingavg(product.asin))
    choice_date = df["Date"][0].strftime('%Y-%m')
    earliest = df["Date"][0]
    choice_date = st.selectbox("Graph starting month", [d.strftime('%Y-%m') for d in df["Date"]])
    if choice_date:
        curr = datetime.strptime(choice_date, '%Y-%m')
        diff = relativedelta.relativedelta(curr, earliest)
        fig = ma_average.make_graph(df[(diff.months + 12*diff.years):], total_reviews)
        fig.update_layout(height=600)
        st.plotly_chart(fig,use_container_width=True,height=600)