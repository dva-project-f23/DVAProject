from collections import deque
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil import relativedelta
from plotly.subplots import make_subplots

from review_visualizer.db.prisma import PrismaClient

COMMON_FONT = dict(family="Arial, sans-serif", size=14, color="black")
T10 = px.colors.qualitative.T10


async def movingavg(asinId, num_months):
    async with PrismaClient() as db:
        curr_reviews = await db.review.find_many(where={"asin": asinId})
        ratings = dict()
        sentiments = dict()
        total_reviews = []
        for rew in curr_reviews:
            rating = int(rew.overall)
            sentiment = rew.sentiment
            dt = rew.unixReviewTime
            my = datetime(dt.year, dt.month, 1)
            if my not in ratings:
                ratings[my] = [0, 0, 0, 0, 0]
            ratings[my][rating - 1] += 1
            if my not in sentiments:
                sentiments[my] = [0, 0]
            if sentiment == "POSITIVE":
                sentiments[my][1] += 1
            elif sentiment == "NEGATIVE":
                sentiments[my][0] += 1

        smallest_key = min(sentiments, key=lambda x: x)
        largest_key = max(sentiments, key=lambda x: x) + relativedelta.relativedelta(
            months= num_months//2
        )

        moving_average = []
        months_dq = deque()
        sum_ratings = 0
        num_ratings = 0
        curr = smallest_key
        for i in range(num_months):
            months_dq.append(curr)
            if curr in ratings:
                curr_rating = ratings[curr]
                sum_ratings += (
                    1 * curr_rating[0]
                    + 2 * curr_rating[1]
                    + 3 * curr_rating[2]
                    + 4 * curr_rating[3]
                    + 5 * curr_rating[4]
                )
                num_ratings += (
                    curr_rating[0]
                    + curr_rating[1]
                    + curr_rating[2]
                    + curr_rating[3]
                    + curr_rating[4]
                )
            curr = curr + relativedelta.relativedelta(months=1)

        tup = (months_dq[num_months//2], sum_ratings / num_ratings)
        moving_average.append(tup)

        while curr <= largest_key:
            removed_month = months_dq.popleft()
            if removed_month in ratings:
                removed_rating = ratings[removed_month]
                sum_ratings -= (
                    1 * removed_rating[0]
                    + 2 * removed_rating[1]
                    + 3 * removed_rating[2]
                    + 4 * removed_rating[3]
                    + 5 * removed_rating[4]
                )
                num_ratings -= (
                    removed_rating[0]
                    + removed_rating[1]
                    + removed_rating[2]
                    + removed_rating[3]
                    + removed_rating[4]
                )
            months_dq.append(curr)
            if curr in ratings:
                curr_rating = ratings[curr]
                sum_ratings += (
                    1 * curr_rating[0]
                    + 2 * curr_rating[1]
                    + 3 * curr_rating[2]
                    + 4 * curr_rating[3]
                    + 5 * curr_rating[4]
                )
                num_ratings += (
                    curr_rating[0]
                    + curr_rating[1]
                    + curr_rating[2]
                    + curr_rating[3]
                    + curr_rating[4]
                )
            curr = curr + relativedelta.relativedelta(months=1)
            average_rating = 0
            if num_ratings == 0:
                average_rating = moving_average[len(moving_average) - 1][1]
            else:
                average_rating = sum_ratings / num_ratings
            tup = (months_dq[num_months//2], average_rating)
            moving_average.append(tup)

        x_list = [t[0] for t in moving_average]
        y_list = [t[1] for t in moving_average]

        moving_average = []
        months_dq = deque()
        neg_sentiments = 0
        pos_sentiments = 0
        num_sentiments = 0
        curr = smallest_key
        for i in range(num_months):
            months_dq.append(curr)
            if curr in sentiments:
                curr_sentiment = sentiments[curr]
                neg_sentiments += curr_sentiment[0]
                pos_sentiments += curr_sentiment[1]
                num_sentiments += curr_sentiment[0] + curr_sentiment[1]
            curr = curr + relativedelta.relativedelta(months=1)

        tup = (months_dq[num_months//2], (pos_sentiments - neg_sentiments) / num_sentiments)
        moving_average.append(tup)

        while curr <= largest_key:
            removed_month = months_dq.popleft()
            if removed_month in sentiments:
                removed_sentiment = sentiments[removed_month]
                neg_sentiments -= removed_sentiment[0]
                pos_sentiments -= removed_sentiment[1]
                num_sentiments -= removed_sentiment[0] + removed_sentiment[1]
            months_dq.append(curr)
            if curr in sentiments:
                curr_sentiment = sentiments[curr]
                neg_sentiments += curr_sentiment[0]
                pos_sentiments += curr_sentiment[1]
                num_sentiments += curr_sentiment[0] + curr_sentiment[1]
            curr = curr + relativedelta.relativedelta(months=1)
            average_sentiment = 0
            if num_sentiments == 0:
                average_sentiment = moving_average[len(moving_average) - 1][1]
            else:
                average_sentiment = (pos_sentiments - neg_sentiments) / num_sentiments
            tup = (months_dq[num_months//2], average_sentiment)
            moving_average.append(tup)

        curr = largest_key
        last = [0, 0]
        while curr >= smallest_key:
            if (len(total_reviews) != 0):
                last = total_reviews[len(total_reviews) - 1]
            if curr in sentiments:
                curr_sentiment = sentiments[curr]
                curr_sentiment[0] += last[0]
                curr_sentiment[1] += last[1]
                total_reviews.append(curr_sentiment)
            else:
                total_reviews.append(last)
            curr = curr - relativedelta.relativedelta(months=1)

        total_reviews.reverse()
        x_list = [t[0] for t in moving_average]
        y2_list = [t[1] for t in moving_average]

        df = pd.DataFrame({"Date": x_list, "Rating": y_list, "Sentiment": y2_list})
        return df, total_reviews


def make_graph(df, total_reviews):
    fig1 = make_subplots(
        specs=[[{"type": "xy", "secondary_y": True}]],
    )
    fig1.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Rating"],
            mode="lines",
            name="Ratings",
            line_color=T10[2],
        ),
        secondary_y=False,
    )
    fig1.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Sentiment"],
            mode="lines",
            name="Sentiment",
            line_color=T10[6],
        ),
        secondary_y=True,
    )
    fig1.update_layout(
        title_text="Ratings and Sentiment",
        title_font_size=20,  # Increase title font size
        xaxis_title="Date",
        xaxis_title_font_size=16,  # Increase x-axis label font size
        yaxis_title="Rating",
        yaxis_range=[1, 5],
        yaxis_title_font_size=16,  # Increase y-axis label font size
        yaxis2_title="Sentiment",
        yaxis2_title_font_size=16,  # Increase secondary y-axis label font size
        yaxis_range=[-1, 1],
        legend_font_size=14,  # Increase legend font size
        # ... [other layout properties] ...
    )
    fig2 = make_subplots(
        specs=[[{"type": "pie"}]],
    )
    fig2.add_trace(
        go.Pie(
            labels=["Negative", "Positive"],
            values=total_reviews,
            textinfo="percent",  # Choose what info to display (label, percent, value)
            insidetextfont=dict(size=18),  # Increase the font size for inside text
            marker_colors=[T10[1], T10[0]],
        )
    )
    fig2.update_layout(
        title_font_size=20,  # Increase title font size
        legend_font_size=14,  # Increase legend font size
        margin=dict(t=50, b=50, l=50, r=50),
        title_text="Overall Sentiment",
    )

    return fig1, fig2
