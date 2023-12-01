import asyncio
import html
from dataclasses import dataclass
from typing import List

import streamlit as st

st.set_page_config(layout="wide")

from dateutil import relativedelta
from prisma.models import Product
from st_pages import add_page_title
from streamlit_searchbox import st_searchbox

from moving_average import ma_average
from review_visualizer.db.prisma import PrismaClient

add_page_title("Overview")


@dataclass
class SearchResults:
    asin: str
    title: str
    product: Product

    def __repr__(self):
        return html.unescape(self.title)


async def search_results(query: str) -> List[SearchResults]:
    # Use database to search for query
    async with PrismaClient() as prisma:
        results = await prisma.product.find_many(
            where={
                "AND": [
                    {
                        "title": {
                            "contains": query,
                        },
                    },
                    {"reviews": {"some": {"overall": {"gte": 0.0}}}},
                ]
            },
            take=5,
        )

    return [
        SearchResults(
            asin=result.asin,
            title=result.title,
            product=result,
        )
        for result in results
    ]


def search_results_sync(query: str) -> List[SearchResults]:
    return asyncio.run(search_results(query))


# Search bar
search_res: SearchResults = st_searchbox(
    search_results_sync,
    placeholder="Search for a product",
    key="product_search",
)

if search_res:
    st.subheader("Product Information")
    st.write("**Amazon Standard Identification Number:** " + search_res.asin)
    st.write(
        f"**Brand:** {search_res.product.brand}" if search_res.product.brand else ""
    )
    st.write(
        f"**Price:** ${search_res.product.price:.2f}"
        if search_res.product.price
        else ""
    )
    st.write(
        f"**Product Category:** {search_res.product.primaryCategory}"
        if search_res.product.primaryCategory
        else ""
    )
    st.write(
        f"**Product Sales Rank:** {search_res.product.salesRank}"
        if search_res.product.salesRank
        else ""
    )

    if search_res.product.imUrl:
        st.image(search_res.product.imUrl, width=300)

    # choice_date = st.selectbox(
    #     "Graph starting month", [d.strftime("%Y-%m") for d in df["Date"]]
    # )

    # Add a slider to select the number of months to average over
    num_months = st.slider(
        "Select number of months to average over",
        min_value=1,
        max_value=5,
        value=1,
        step=1,
    )

    df, total_reviews = asyncio.run(ma_average.movingavg(search_res.asin, num_months))

    st.subheader("Product Review Analysis")
    choice_date = df["Date"][0].strftime("%Y-%m")
    earliest = df["Date"][0]
    oldest_review_date = df["Date"].min()
    latest_review_date = df["Date"].max()

    choice_date = st.date_input(
        "Select start date for the graph",
        value=oldest_review_date,
        min_value=oldest_review_date,
        max_value=latest_review_date,
    )

    if choice_date:
        # curr = datetime.strptime(choice_date, "%Y-%m")
        curr = choice_date
        diff = relativedelta.relativedelta(curr, earliest)
        fig1, fig2 = ma_average.make_graph(
            df[(diff.months + 12 * diff.years) :],
            total_reviews[diff.months + 12 * diff.years],
        )

        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
