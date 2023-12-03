import asyncio

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
from prisma.models import Product, RelatedProduct

from review_visualizer.db.prisma import PrismaClient


def titlize(s: str) -> str:
    return s.title().replace("_", " ")


async def get_related_products(product: Product) -> list[RelatedProduct]:
    async with PrismaClient() as client:
        related_products = await client.relatedproduct.find_many(
            where={"OR": [{"asin": product.asin}, {"related_asin": product.asin}]},
            include={"product": True},
        )
        related_asins = [rel_prod.related_asin for rel_prod in related_products]
        relation_types = [rel_prod.relation_type for rel_prod in related_products]
        related_products_products = await client.product.find_many(
            where={"asin": {"in": related_asins}},
            include={"reviews": True},
        )
        related_products_products_dict = {
            prod.asin: {
                "product": prod,
                "relation_type": relation_types[idx],
            }
            for idx, prod in enumerate(related_products_products)
        }

    return related_products_products_dict


def show(product: Product, avg_rating: float) -> go.Figure:
    G = nx.Graph()
    G.add_node(
        product.asin,
        title=product.title or "Current product",
        size=avg_rating or 5,
        price=product.price or 0,
    )

    related_products_products_dict: dict[str, Product] = asyncio.run(
        get_related_products(product)
    )

    for rel_prod_asin, rel_prod_value in related_products_products_dict.items():
        rel_prod = rel_prod_value["product"]
        try:
            rel_prod_avg_rating = sum(
                [
                    review.overall
                    for review in rel_prod.reviews
                    if review.overall and review.overall >= 0.0
                ]
            ) / len(rel_prod.reviews)
        except ZeroDivisionError:
            rel_prod_avg_rating = 5

        G.add_node(
            rel_prod_asin,
            title=rel_prod.title or "Unknown",
            size=rel_prod_avg_rating,
            price=rel_prod.price or 0,
        )
        relation_type = rel_prod_value["relation_type"]
        G.add_edge(product.asin, rel_prod_asin, relation_type=relation_type)

    # Generate positions for each node using a layout
    pos = nx.spring_layout(G)

    # Create edge trace
    edge_trace = go.Scatter(
        x=[], y=[], line=dict(width=0.5, color="#888"), hoverinfo="none", mode="lines"
    )

    relation_colors = px.colors.qualitative.Plotly

    edge_traces = {}
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        relation_type = edge[2].get("relation_type", "Unknown")

        # Get color for relation type
        edge_color = relation_colors[hash(relation_type) % len(relation_colors)]

        # Check if trace already exists for this relation type
        if relation_type not in edge_traces:
            edge_traces[relation_type] = go.Scatter(
                x=[],
                y=[],
                line=dict(width=0.5, color=edge_color),
                hoverinfo="text",
                mode="lines",
                text=[],
                name=titlize(relation_type),
            )

        # Add edge to the corresponding trace
        edge_traces[relation_type]["x"] += tuple([x0, x1, None])
        edge_traces[relation_type]["y"] += tuple([y0, y1, None])
        # Add relation type to hover text
        edge_traces[relation_type]["text"] += tuple([relation_type])

    # Create node trace
    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode="markers",
        hoverinfo="text",
        marker=dict(
            showscale=True, colorscale="YlGnBu", size=[], color=[], line_width=2
        ),
    )

    # Min and max prices for normalization
    min_price = min(node_info["price"] for node_info in G.nodes.values())
    max_price = max(node_info["price"] for node_info in G.nodes.values())

    for node in G.nodes():
        x, y = pos[node]
        node_info = G.nodes[node]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])
        node_trace["text"] += tuple([node_info["title"]])
        node_trace["marker"]["size"] += tuple(
            [node_info["size"] * 5]
        )  # Scale size for visibility
        # Normalize price to 0-1 range for color mapping
        normalized_price = (node_info["price"] - min_price) / (max_price - min_price)
        node_trace["marker"]["color"] += tuple([normalized_price])

    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace])

    for trace in edge_traces.values():
        fig.add_trace(trace)

    # fig.update_layout(
    #     showlegend=True,
    #     coloraxis_colorbar=dict(
    #         title="Your Title",
    #     ),
    #     coloraxis_colorbar_title_text="test",
    # )

    # Custom legend for price - assuming min_price and max_price are defined
    legend_entries = [
        {"price": min_price, "name": "Less Expensive"},
        {"price": max_price, "name": "More Expensive"},
    ]

    for entry in legend_entries:
        normalized_price = (entry["price"] - min_price) / (max_price - min_price)
        fig.add_trace(
            go.Scatter(
                x=[],
                y=[],
                mode="markers",
                marker=dict(
                    size=10,
                    color=[normalized_price],
                    colorscale=[(0, "green"), (1, "red")],
                ),
                legendgroup="Price",
                showlegend=True,
                name=f'{entry["name"]}: ${entry["price"]}',
                legend="legend2",
            )
        )

    # Layout adjustments to fix overlapping axes
    fig.update_layout(
        title="<br>Network graph of related products",
        titlefont_size=16,
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=0, t=40),  # Adjust margins if necessary
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        coloraxis_colorbar=dict(
            title="Your Title",
        ),
        coloraxis_colorbar_title_text="test",
        legend=dict(
            title="Legend",
        ),
    )

    return fig
