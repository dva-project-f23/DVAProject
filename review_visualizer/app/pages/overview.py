import asyncio
import html
from dataclasses import dataclass
from typing import List

import pandas as pd
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

async def get_similar_products(asin: str) -> List[Product]:
    async with PrismaClient() as prisma:
        similar_products_asins = await prisma.product.find_unique(
            where={"asin": asin},
            select={"similar": True}
        )
        if similar_products_asins and similar_products_asins.similar:
            return await prisma.product.find_many(
                where={"asin": {"in": similar_products_asins.similar}}
            )
        return []

async def get_review_stats(asin: str) -> dict:
    async with PrismaClient() as prisma:
        tot_review_count = await prisma.review.count(where={"asin": asin})
        pos_review_count = await prisma.review.count(
            where={"AND": [{"asin": asin}, {"sentiment": "POSITIVE"}]}
        )
        neg_review_count = await prisma.review.count(
            where={"AND": [{"asin": asin}, {"sentiment": "NEGATIVE"}]}
        )
        avg_rating = await prisma.review.find_many(
            where={"AND": [{"asin": asin}, {"overall": {"gte": 0.0}}]},
        )
        avg_rating = sum([review.overall for review in avg_rating]) / len(avg_rating)

    return {
        "Total": tot_review_count,
        "Positive": pos_review_count,
        "Negative": neg_review_count,
        "Average": avg_rating,
    }


def search_results_sync(query: str) -> List[SearchResults]:
    return asyncio.run(search_results(query))

def create_network_graph(center_product, similar_products, average_ratings):
    edge_x = []
    edge_y = []
    node_x = []
    node_y = []
    node_text = []

    # Center node
    node_x.append(0)
    node_y.append(0)
    node_text.append(center_product.title)

    # Similar nodes
    for i, product in enumerate(similar_products):
        angle = (2 * 3.14159 / len(similar_products)) * i
        x, y = np.cos(angle), np.sin(angle)
        node_x.append(x)
        node_y.append(y)
        node_text.append(product.title)

        edge_x.extend([0, x, None])
        edge_y.extend([0, y, None])

    # Adjust node size based on average rating
    max_rating = max(average_ratings.values())
    node_size = [10 + 20 * (average_ratings[product.asin] / max_rating) if average_ratings[product.asin] else 10 for product in similar_products]
    
    # Adjust node color based on price
    max_price = max(product.price for product in similar_products if product.price)
    node_color = [np.interp(product.price, [0, max_price], [0.5, 1]) if product.price else 0.5 for product in similar_products]
    
    # Create Plotly trace for edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    # Create Plotly trace for nodes
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=['rgba(138, 43, 226, {})'.format(shade) for shade in node_color],
            size=node_size,
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    return fig

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

    if search_res.product.imUrl:
        st.image(search_res.product.imUrl, width=300)

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

    reviews = search_res.product.reviews

    reviews_data = asyncio.run(get_review_stats(search_res.asin))

    reviews_df = pd.DataFrame(reviews_data, index=["Value"])

    st.write("**Review Statistics**")
    st.table(reviews_df)

    # choice_date = st.selectbox(
    #     "Graph starting month", [d.strftime("%Y-%m") for d in df["Date"]]
    # )

    st.subheader("Product Review Analysis")

    # Add a slider to select the number of months to average over
    num_months = st.slider(
        "Select number of months to average over",
        min_value=1,
        max_value=5,
        value=5,
        step=1,
    )

    df, total_reviews = asyncio.run(ma_average.movingavg(search_res.asin, num_months))

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

    st.subheader("Similar Products")
    similar_products = asyncio.run(get_similar_products(search_res.asin))
    if similar_products:
        # Compute average ratings for similar products
        similar_products_asins = [product.asin for product in similar_products]
        average_ratings = asyncio.run(get_average_ratings(similar_products_asins))

        # Display a table of similar products with their prices
        similar_products_data = {
            "Title": [product.title for product in similar products],
            "Price": [product.price for product in similar products],
            "Average Rating": [average_ratings[asin] for asin in similar_products_asins]
        }
        similar_products_df = pd.DataFrame(similar_products_data)
        st.table(similar_products_df.head(3))  # Display top 3 similar products

        # Create and display the network graph
        network_graph = create_network_graph(search_res.product, similar_products, average_ratings)
        st.plotly_chart(network_graph, use_container_width=True)
    else:
        st.write("No similar products found.")