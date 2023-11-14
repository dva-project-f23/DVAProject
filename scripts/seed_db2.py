import ast
import json
from contextlib import contextmanager

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

engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


with open("reviews_Electronics_5.json") as f:
    review_data = f.readlines()

with open("metadata.json") as f:
    product_data = f.readlines()


with get_db() as db:
    # Load and add product data
    for line in tqdm(product_data):
        # line = line.replace("'", '"')
        # # print(line)
        # # data = json.loads(line)
        data = ast.literal_eval(line)
        if not data.get("asin") or not data.get("title"):
            continue

        product = Product(
            asin=data["asin"],
            title=data["title"],
            price=data.get("price", None),  # Using get to handle missing data
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
        if data.get("related"):
            for relation_type, asins in data["related"].items():
                for related_asin in asins:
                    related_product = RelatedProduct(
                        asin=data["asin"],
                        related_asin=related_asin,
                        relation_type=relation_type,
                    )
                    product.related_products.append(related_product)

        db.add(product)

    # Load and add review data
    for line in tqdm(review_data):
        # line = line.replace("'", '"')
        # data = json.loads(line)
        data = ast.literal_eval(line)

        review = Review(
            reviewerID=data["reviewerID"],
            asin=data["asin"],
            reviewerName=data.get("reviewerName", None),
            helpfulCount=data["helpful"][0],
            totalHelpfulCount=data["helpful"][1],
            reviewText=data["reviewText"],
            overall=data["overall"],
            summary=data["summary"],
            unixReviewTime=data["unixReviewTime"],
            reviewTime=data["reviewTime"],
        )

        db.add(review)

    # Commit the session to save changes to the database
    db.commit()
