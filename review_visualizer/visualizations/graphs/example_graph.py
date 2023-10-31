import plotly.express as px
from pandas import DataFrame


def show(df: DataFrame) -> px.bar:
    """Show a bar chart of the given dataframe."""
    fig = px.bar(df, x="Rating", y="Count")
    fig.update_layout(
        title="Ratings",
        xaxis_title="Rating",
        yaxis_title="Count",
        font=dict(family="Courier New, monospace", size=18, color="#7f7f7f"),
    )
    return fig
