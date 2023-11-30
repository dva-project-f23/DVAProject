from collections import deque
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dateutil import relativedelta
from plotly.subplots import make_subplots

from review_visualizer.db.prisma import PrismaClient


async def movingavg(asinId):
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
            months=2
        )

        moving_average = []
        months_dq = deque()
        sum_ratings = 0
        num_ratings = 0
        curr = smallest_key
        for i in range(5):
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

        tup = (months_dq[2], sum_ratings / num_ratings)
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
            tup = (months_dq[2], average_rating)
            moving_average.append(tup)

        x_list = [t[0] for t in moving_average]
        y_list = [t[1] for t in moving_average]

        moving_average = []
        months_dq = deque()
        neg_sentiments = 0
        pos_sentiments = 0
        num_sentiments = 0
        curr = smallest_key
        for i in range(5):
            months_dq.append(curr)
            if curr in sentiments:
                curr_sentiment = sentiments[curr]
                neg_sentiments += curr_sentiment[0]
                pos_sentiments += curr_sentiment[1]
                num_sentiments += curr_sentiment[0] + curr_sentiment[1]
            curr = curr + relativedelta.relativedelta(months=1)

        tup = (months_dq[2], (pos_sentiments - neg_sentiments) / num_sentiments)
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
            tup = (months_dq[2], average_sentiment)
            moving_average.append(tup)

        total_reviews.append([0, 0])
        curr = largest_key - relativedelta.relativedelta(months=1)
        while curr >= smallest_key:
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
            line_color="purple",
        ),
        secondary_y=False,
    )
    fig1.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Sentiment"],
            mode="lines",
            name="Sentiment",
            line_color="green",
        ),
        secondary_y=True,
    )
    fig1.update_layout(title_text="Ratings and Sentiment")
    fig1["layout"]["xaxis"].update(title_text="Date")
    fig1["layout"]["yaxis"].update(title_text="Rating", range=[1, 5])
    fig1["layout"]["yaxis2"].update(title_text="Sentiment", range=[-1, 1])
    fig2 = make_subplots(
        specs=[[{"type": "pie"}]],
    )
    fig2.add_trace(
        go.Pie(
            labels=["Negative", "Positive"],
            values=total_reviews,
            marker_colors=["red", "blue"],
            title="Overall Sentiment",
        )
    )
    fig2.update_layout(margin=dict(t=50, b=50, l=50, r=50))

    # use the pastel discrete color scheme
    fig1.update_layout(
        colorway=px.colors.qualitative.Pastel,
    )
    fig2.update_layout(
        colorway=px.colors.qualitative.Pastel,
    )

    return fig1, fig2
