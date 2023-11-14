import ast
import json
from contextlib import contextmanager
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from review_visualizer.db.models import Base, Product, RelatedProduct, Review


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create a SQLLite database
DB_URL = "sqlite:///test.db"

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


with open("reviews_Electronics_5.json") as f:
    review_data = f.readlines()

    unique_asins = set([json.loads(line)["asin"] for line in review_data])

with open("metadata.json") as f:
    product_data = f.readlines()


def process_product_line(line):
    # Your existing logic to process a product line
    # Return the Product object instead of adding it to the db session
    data = ast.literal_eval(line)
    if (
        not data.get("asin")
        or not data.get("title")
        or data.get("asin") not in unique_asins
    ):
        return None

    product = Product(
        asin=data["asin"],
        title=data["title"],
        price=data.get("price", None),
        imUrl=data.get("imUrl", None),
        primaryCategory=list(data["salesRank"].keys())[0]
        if data.get("salesRank")
        else None,
        salesRank=list(data["salesRank"].values())[0]
        if data.get("salesRank")
        else None,
        brand=data.get("brand", None),
    )

    # Add related products
    related_products = []
    if data.get("related"):
        for relation_type, asins in data["related"].items():
            for related_asin in asins:
                related_product = RelatedProduct(
                    asin=data["asin"],
                    related_asin=related_asin,
                    relation_type=relation_type,
                )
                related_products.append(related_product)

    # Associate related products with the product
    product.related_products = related_products

    return product


def process_review_line(line):
    # Your existing logic to process a review line
    # Return the Review object instead of adding it to the db session
    data = ast.literal_eval(line)

    # Parse the unixReviewTime to a datetime object
    review_time = (
        datetime.fromtimestamp(data["unixReviewTime"])
        if data.get("unixReviewTime")
        else None
    )

    review = Review(
        reviewerID=data["reviewerID"],
        asin=data["asin"],
        reviewerName=data.get("reviewerName", None),
        helpfulCount=data["helpful"][0],
        totalHelpfulCount=data["helpful"][1],
        reviewText=data["reviewText"],
        overall=data["overall"],
        summary=data["summary"],
        unixReviewTime=review_time,
    )

    return review


BATCH_SIZE = 10_000

with get_db() as db:
    # Process product data in batches
    products = []
    for line in tqdm(product_data):
        product = process_product_line(line)
        if product:
            products.append(product)
            if len(products) >= BATCH_SIZE:
                db.add_all(products)
                db.commit()
                products = []

    # Don't forget to add the remaining products
    if products:
        db.add_all(products)
        db.commit()

    # Similar approach for reviews
    reviews = []
    for line in tqdm(review_data):
        review = process_review_line(line)
        if review:
            reviews.append(review)
            if len(reviews) >= BATCH_SIZE:
                db.add_all(reviews)
                db.commit()
                reviews = []

    if reviews:
        db.add_all(reviews)
        db.commit()
