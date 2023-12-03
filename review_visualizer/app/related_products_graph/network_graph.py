import numpy as np
import plotly.graph_objects as go


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
    node_size = [
        10 + 20 * (average_ratings[product.asin] / max_rating)
        if average_ratings[product.asin]
        else 10
        for product in similar_products
    ]

    # Adjust node color based on price
    max_price = max(product.price for product in similar_products if product.price)
    node_color = [
        np.interp(product.price, [0, max_price], [0.5, 1]) if product.price else 0.5
        for product in similar_products
    ]

    # Create Plotly trace for edges
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Create Plotly trace for nodes
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        marker=dict(
            showscale=False,
            color=["rgba(138, 43, 226, {})".format(shade) for shade in node_color],
            size=node_size,
            line_width=2,
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    return fig
