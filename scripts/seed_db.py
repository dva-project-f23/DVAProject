import json
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime
from review_visualizer.db.session import get_db, init_db
from review_visualizer.db.models import Review

init_db()
with open("reviews_Electronics_5.json") as f:
    data = f.readlines()

batch_size = 10_000
count_written = 0
count_rejected = 0

with get_db() as db:
    reviews_array = []
    print("Gathering reviews...")
    for curr_review in data:
        curr_review = json.loads(curr_review)
        if not curr_review.get("reviewerID"):
            count_rejected += 1
            continue
        curr_review["reviewerName"] = curr_review.get("reviewerName")
        curr_review["helpful"] = curr_review.get("helpful")
        curr_review["reviewText"] = curr_review.get("reviewText")
        curr_review["overall"] = curr_review.get("overall")
        curr_review["summary"] = curr_review.get("summary")
        curr_review["unixReviewTime"] = curr_review.get("unixReviewTime")

        unix_time = curr_review.get("unixReviewTime")
        if unix_time:
            review_time = datetime.utcfromtimestamp(unix_time)
        else:
            review_time = None

        review = Review(
            reviewerID=curr_review["reviewerID"],
            asin=curr_review["asin"],
            reviewerName=curr_review["reviewerName"],
            helpful=curr_review["helpful"],
            reviewText=curr_review["reviewText"],
            overall=curr_review["overall"],
            summary=curr_review["summary"],
            unixReviewTime=review_time,
        )

        reviews_array.append(review)
        if len(reviews_array) == batch_size:
            db.bulk_save_objects(reviews_array)
            db.commit()
            reviews_array = []
            print(f"Commiting {batch_size} reviews to database...")

        count_written += 1

    if reviews_array:
        db.bulk_save_objects(reviews_array)
        db.commit()

print(f"Number of reviews written: {count_written}")
print(f"Number of reviews rejected: {count_rejected}")
print(f"Total Number of reviews: {len(data)}")
