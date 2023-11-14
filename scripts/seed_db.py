import ast
import asyncio
import json
from datetime import datetime
from pprint import pprint
from typing import Awaitable

from dotenv import load_dotenv
from tqdm import tqdm as tqdm_sync
from tqdm.asyncio import tqdm

load_dotenv()

from prisma.types import (
    ProductCreateWithoutRelationsInput,
    RelatedProductCreateWithoutRelationsInput,
    ReviewCreateWithoutRelationsInput,
)

from review_visualizer.db.prisma import PrismaClient

BATCH_SIZE = 1000
CONCURRENCY = 20


with open("reviews_Electronics_5.json") as f:
    review_data = f.readlines()
    asins = set([json.loads(line)["asin"] for line in review_data])

with open("metadata.json") as f:
    product_data = f.readlines()
    product_map = {(d := ast.literal_eval(line))["asin"]: d for line in product_data}

# Update asins to include related products of all products in the dataset
for product in product_map.values():
    if "related" in product:
        for relation_type, related_asins in product["related"].items():
            asins.update(related_asins)


def process_product_line(asin):
    # Your existing logic to process a product line
    # Return the Product object instead of adding it to the db session
    data = product_map[asin]
    if (
        not data.get("asin")
        or not data.get("title")
        or not data.get("price")
        or data.get("asin") not in asins
    ):
        return None

    # Add related products
    related_products: list[RelatedProductCreateWithoutRelationsInput] = []
    if data.get("related"):
        for relation_type, asins in data["related"].items():
            for related_asin in asins:
                related_product = {
                    "asin": data["asin"],  # Assuming 'asin' is the product's ASIN
                    "related_asin": related_asin,
                    "relation_type": relation_type,
                }
                related_products.append(related_product)

    product: ProductCreateWithoutRelationsInput = {
        "asin": data["asin"],
        "title": data["title"],
        "price": data["price"],
        "imUrl": data.get("imUrl", None),
        "primaryCategory": list(data["salesRank"].keys())[0]
        if data.get("salesRank")
        else None,
        "salesRank": list(data["salesRank"].values())[0]
        if data.get("salesRank")
        else None,
        "brand": data.get("brand", None),
    }

    return product, related_products


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

    review: ReviewCreateWithoutRelationsInput = {
        "reviewerID": data["reviewerID"],
        "asin": data["asin"],
        "reviewerName": data.get("reviewerName", None),
        "helpfulCount": data["helpful"][0],
        "totalHelpful": data["helpful"][1],
        "reviewText": data["reviewText"],
        "overall": data["overall"],
        "summary": data["summary"],
        "unixReviewTime": review_time,
    }

    return review


async def main():
    # Process product data
    async with PrismaClient() as prisma:
        current_product_batch = []
        current_related_product_batch = []

        # Read product map and filter out products that are not in asins
        for p_asin, p_data in tqdm_sync(product_map.items()):
            if p_asin not in asins:
                continue
            product = process_product_line(p_asin)
            if product:
                product, related_products = product
                current_product_batch.append(product)
                current_related_product_batch.extend(related_products)
                if len(current_product_batch) >= BATCH_SIZE:
                    await prisma.product.create_many(
                        data=current_product_batch, skip_duplicates=True
                    )
                    await prisma.relatedproduct.create_many(
                        data=current_related_product_batch, skip_duplicates=True
                    )
                    current_related_product_batch = []
                    current_product_batch = []

        # Add any remaining products to the batches
        if current_product_batch:
            await prisma.product.create_many(
                data=current_product_batch, skip_duplicates=True
            )

        if current_related_product_batch:
            await prisma.relatedproduct.create_many(
                data=current_related_product_batch, skip_duplicates=True
            )

        # # Process review data
        current_review_batch = []

        for line in tqdm_sync(review_data):
            review = process_review_line(line)
            if review:
                current_review_batch.append(review)
                if len(current_review_batch) >= BATCH_SIZE:
                    await prisma.review.create_many(
                        data=current_review_batch, skip_duplicates=True
                    )
                    current_review_batch = []

        # Add any remaining reviews to the batches
        if current_review_batch:
            await prisma.review.create_many(
                data=current_review_batch, skip_duplicates=True
            )


if __name__ == "__main__":
    asyncio.run(main())
