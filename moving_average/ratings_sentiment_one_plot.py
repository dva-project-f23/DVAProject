import requests
import json
import csv
from datetime import datetime
from dateutil import relativedelta
from collections import deque
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

frating = open('Electronics.csv')
reader = csv.reader(frating)

ratings = dict()
for line in frating:
	s = line.split(",")
	asin = s[0]
	rating = int(float(s[2]))
	unix_ts = int(s[3])
	dt = datetime.fromtimestamp(unix_ts)
	my = datetime(dt.year, dt.month, 1)
	if asin == "B003L1ZYYW":
		if my not in ratings:
			ratings[my] = [0, 0, 0, 0, 0]
		ratings[my][rating-1] += 1

smallest_key = min(ratings, key=lambda x: x)
largest_key = max(ratings, key=lambda x: x) + relativedelta.relativedelta(months=2)

moving_average = []
months_dq = deque()
sum_ratings = 0
num_ratings = 0
curr = smallest_key
for i in range(5):
	months_dq.append(curr)
	if curr in ratings:
		curr_rating = ratings[curr]
		sum_ratings += (1*curr_rating[0] + 2*curr_rating[1] + 3*curr_rating[2] + 4*curr_rating[3] + 5*curr_rating[4])
		num_ratings += curr_rating[0] + curr_rating[1] + curr_rating[2] + curr_rating[3] + curr_rating[4]
	curr = curr + relativedelta.relativedelta(months=1)

tup = (months_dq[2], sum_ratings / num_ratings)
moving_average.append(tup)

while (curr <= largest_key):
	removed_month = months_dq.popleft()
	if removed_month in ratings:
		removed_rating = ratings[removed_month]
		sum_ratings -= (1*removed_rating[0] + 2*removed_rating[1] + 3*removed_rating[2] + 4*removed_rating[3] + 5*removed_rating[4])
		num_ratings -= (removed_rating[0] + removed_rating[1] + removed_rating[2] + removed_rating[3] + removed_rating[4])
	months_dq.append(curr)
	if curr in ratings:
		curr_rating = ratings[curr]
		sum_ratings += (1*curr_rating[0] + 2*curr_rating[1] + 3*curr_rating[2] + 4*curr_rating[3] + 5*curr_rating[4])
		num_ratings += curr_rating[0] + curr_rating[1] + curr_rating[2] + curr_rating[3] + curr_rating[4]
	curr = curr + relativedelta.relativedelta(months=1)
	average_rating = 0
	if (num_ratings == 0):
		average_rating = moving_average[len(moving_average)-1][1]
	else:
		average_rating = sum_ratings / num_ratings
	tup = (months_dq[2], average_rating)
	moving_average.append(tup)

x_list = [t[0] for t in moving_average]
y_list = [t[1] for t in moving_average]

fsentiment = open('review_sentiment_preds.csv')
reader = csv.reader(fsentiment)
next(reader)

total_reviews = [0, 0]
sentiments = dict()
for line in fsentiment:
	s = line.split(",")
	sentiment = int(s[2])
	unix_ts = int(s[0])
	dt = datetime.fromtimestamp(unix_ts)
	my = datetime(dt.year, dt.month, 1)
	if my not in sentiments:
		sentiments[my] = [0, 0]
	sentiments[my][sentiment] += 1
	total_reviews[sentiment] += 1

smallest_key = min(sentiments, key=lambda x: x)
largest_key = max(sentiments, key=lambda x: x) + relativedelta.relativedelta(months=2)

moving_average = []
months_dq = deque()
pos_sentiments = 0
num_sentiments = 0
curr = smallest_key
for i in range(5):
	months_dq.append(curr)
	if curr in sentiments:
		curr_sentiment = sentiments[curr]
		pos_sentiments += curr_sentiment[1]
		num_sentiments += curr_sentiment[0] + curr_sentiment[1]
	curr = curr + relativedelta.relativedelta(months=1)

tup = (months_dq[2], pos_sentiments / num_sentiments)
moving_average.append(tup)

while (curr <= largest_key):
	removed_month = months_dq.popleft()
	if removed_month in sentiments:
		removed_sentiment = sentiments[removed_month]
		pos_sentiments -= removed_sentiment[1]
		num_sentiments -= (removed_sentiment[0] + removed_sentiment[1])
	months_dq.append(curr)
	if curr in sentiments:
		curr_sentiment = sentiments[curr]
		pos_sentiments += curr_sentiment[1]
		num_sentiments += curr_sentiment[0] + curr_sentiment[1]
	curr = curr + relativedelta.relativedelta(months=1)
	average_sentiment = 0
	if (num_sentiments == 0):
		average_sentiment = moving_average[len(moving_average)-1][1]
	else:
		average_sentiment = pos_sentiments / num_sentiments
	tup = (months_dq[2], average_sentiment)
	moving_average.append(tup)

x_list = [t[0] for t in moving_average]
y2_list = [t[1] for t in moving_average]
df = pd.DataFrame({'Date':x_list, 'Rating':y_list, 'Sentiment':y2_list})
fig = make_subplots(rows=2, cols=1, specs=[[{"type": "xy", "secondary_y": True}], [{'type':'pie'}]], subplot_titles=("Ratings and Sentiment", "Overall Sentiment"))
fig.add_trace(
    go.Scatter(x=df['Date'], y=df['Rating'], mode='lines', name="Ratings"),
    secondary_y=False, row=1, col=1)
fig.add_trace(
    go.Scatter(x=df['Date'], y=df['Sentiment'], mode='lines', name="Sentiment"),
    secondary_y=True, row=1, col=1)
fig.add_trace(go.Pie(
	labels = ["Negative", "Positive"], 
	values = total_reviews), row=2, col=1)
fig['layout']['xaxis'].update(title_text="Date")
fig['layout']['yaxis'].update(title_text="Rating", range=[1, 5])
fig['layout']['yaxis2'].update(title_text="Sentiment", range=[0, 1])
#fig.update_yaxes(title_text="Rating", range=[1, 5], secondary_y=False)
#fig.update_yaxes(title_text="Sentiment", range=[0, 1], secondary_y=True)
fig.show()

