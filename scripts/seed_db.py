import ast
import asyncio
import json
import os
import pickle
from datetime import datetime
from pprint import pprint
from typing import Awaitable

from dotenv import load_dotenv
from tqdm import tqdm as tqdm_sync
from tqdm.asyncio import tqdm as tqdm_async

load_dotenv()

from prisma.types import (
    ProductCreateWithoutRelationsInput,
    RelatedProductCreateWithoutRelationsInput,
    ReviewCreateWithoutRelationsInput,
)

from review_visualizer.db.prisma import PrismaClient

BATCH_SIZE = 1000
CONCURRENCY = 20


# Function to check and load data from pickle file
def load_pickle(file_name):
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            return pickle.load(f)
    return None


# Load data from pickle files if they exist
asins = load_pickle("asins.pkl")
product_map = load_pickle("product_map.pkl")
review_data = load_pickle("review_data.pkl")

# Process and save data only if not already loaded from pickle
if review_data is None:
    with open("reviews_Electronics_5.json") as f:
        review_data = f.readlines()
        asins = set()
        for line in tqdm_sync(review_data, desc="Processing review data"):
            asins.add(json.loads(line)["asin"])

    # Save processed review data
    with open("review_data.pkl", "wb") as f:
        pickle.dump(review_data, f)

if product_map is None:
    with open("metadata.json") as f:
        product_data = f.readlines()
        product_map = {}
        for line in tqdm_sync(product_data, desc="Reading product data"):
            d = ast.literal_eval(line)
            product_map[d["asin"]] = d

    # Updating ASINs to include related products
    for product in tqdm_sync(
        product_map.values(), desc="Updating ASINs with related products"
    ):
        if "related" in product:
            for related_asins in product["related"].values():
                asins.update(related_asins)

    # Save processed product map
    with open("product_map.pkl", "wb") as f:
        pickle.dump(product_map, f)

if asins is not None and isinstance(asins, set):
    with open("asins.pkl", "wb") as f:
        pickle.dump(asins, f)


async def process_product_line(asin, prisma: PrismaClient):
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

    product = await prisma.product.create(
        data={
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
            "related_products": {"create": related_products},
        }
    )

    return product


async def process_review_line(line, prisma: PrismaClient):
    # Your existing logic to process a review line
    # Return the Review object instead of adding it to the db session
    data = ast.literal_eval(line)

    # Parse the unixReviewTime to a datetime object
    review_time = (
        datetime.fromtimestamp(data["unixReviewTime"])
        if data.get("unixReviewTime")
        else None
    )

    review = await prisma.review.create(
        data={
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
    )

    return review


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def main():
    async with PrismaClient() as prisma:
        try:
            # Process Products
            print("Processing products...")
            for i in tqdm_sync(range(0, len(asins), BATCH_SIZE)):
                batch_asins = list(asins)[i : i + BATCH_SIZE]
                tasks = [process_product_line(asin, prisma) for asin in batch_asins]
                for chunk in tqdm_async(
                    chunks(tasks, CONCURRENCY), total=len(tasks) // CONCURRENCY
                ):
                    await asyncio.gather(*chunk)  # Correctly await the coroutine

            # Process Reviews
            print("Processing reviews...")
            for i in tqdm_sync(range(0, len(review_data), BATCH_SIZE)):
                batch_reviews = review_data[i : i + BATCH_SIZE]
                tasks = [process_review_line(line, prisma) for line in batch_reviews]
                for chunk in tqdm_async(
                    chunks(tasks, CONCURRENCY), total=len(tasks) // CONCURRENCY
                ):
                    await asyncio.gather(*chunk)  # Correctly await the coroutine

        except Exception as e:
            print(e)

        # current_product_batch = []
        # current_related_product_batch = []

        # # Read product map and filter out products that are not in asins
        # for p_asin, p_data in tqdm_sync(product_map.items()):
        #     if p_asin not in asins:
        #         continue
        #     product = process_product_line(p_asin)
        #     if product:
        #         product, related_products = product
        #         current_product_batch.append(product)
        #         current_related_product_batch.extend(related_products)
        #         if len(current_product_batch) >= BATCH_SIZE:
        #             await prisma.product.create_many(
        #                 data=current_product_batch, skip_duplicates=True
        #             )
        #             await prisma.relatedproduct.create_many(
        #                 data=current_related_product_batch, skip_duplicates=True
        #             )
        #             current_related_product_batch = []
        #             current_product_batch = []

        # # Add any remaining products to the batches
        # if current_product_batch:
        #     await prisma.product.create_many(
        #         data=current_product_batch, skip_duplicates=True
        #     )

        # if current_related_product_batch:
        #     await prisma.relatedproduct.create_many(
        #         data=current_related_product_batch, skip_duplicates=True
        #     )

        # # # Process review data
        # current_review_batch = []

        # for line in tqdm_sync(review_data):
        #     review = process_review_line(line)
        #     if review:
        #         current_review_batch.append(review)
        #         if len(current_review_batch) >= BATCH_SIZE:
        #             await prisma.review.create_many(
        #                 data=current_review_batch, skip_duplicates=True
        #             )
        #             current_review_batch = []

        # # Add any remaining reviews to the batches
        # if current_review_batch:
        #     await prisma.review.create_many(
        #         data=current_review_batch, skip_duplicates=True
        #     )


if __name__ == "__main__":
    asyncio.run(main())
