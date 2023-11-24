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

from prisma.errors import UniqueViolationError
from prisma.types import (
    ProductCreateWithoutRelationsInput,
    RelatedProductCreateWithoutRelationsInput,
    ReviewCreateWithoutRelationsInput,
)

from review_visualizer.db.prisma import PrismaClient

BATCH_SIZE = 10000
CONCURRENCY = 32

# Process and save data only if not already loaded from pickle
with open("reviews_Electronics_5.json") as f:
    review_data = f.readlines()


with open("metadata.json") as f:
    product_data = f.readlines()


def process_product_line(line, prisma: PrismaClient):
    # Your existing logic to process a product line
    # Return the Product object instead of adding it to the db session
    data = ast.literal_eval(line)
    # print(data.get('asin'))
    # asin_to_look_for = '0594481813'
    # if data["asin"] == asin_to_look_for:
    #     print("-----------")
    #     print("CSER")
    #     print("-----------")
    
    if not data.get("asin"):
        # print(data.get('asin'), data.get("title"), data.get("price"))
        print('here1')
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

    product = prisma.product.create(
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
            "relatedProducts": {"create": related_products},
        }
    )
    print('here2')

    return product


def process_review_line(line, prisma: PrismaClient):
    # Your existing logic to process a review line
    # Return the Review object instead of adding it to the db session
    data = ast.literal_eval(line)

    # Parse the unixReviewTime to a datetime object
    review_time = (
        datetime.fromtimestamp(data["unixReviewTime"])
        if data.get("unixReviewTime")
        else None
    )

    review = prisma.review.create(
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


def main():
    with PrismaClient() as prisma:
        try:
            # Process Products
            tqdm_sync.write("Processing products...")
            for i in tqdm_sync(range(0, len(product_data), BATCH_SIZE), desc="Processing Products"):
                try:
                    batch_products = product_data[i : i + BATCH_SIZE]
                    for asin in batch_products:
                        print(process_product_line(asin, prisma))
                    
                    # a = [process_product_line(asin, prisma) for asin in batch_products]
                    
                except UniqueViolationError:
                    # tqdm_sync.write("Skipping duplicate product...")
                    continue
                except Exception as e:
                    print(e)
                    continue

            # Process Reviews
            # tqdm_sync.write("Processing reviews...")
            # for i in tqdm_sync(range(0, len(review_data), BATCH_SIZE), desc="Processing Reviews"):
            #     try:
            #         batch_reviews = review_data[i : i + BATCH_SIZE]
            #         tasks = [
            #             process_review_line(line, prisma) for line in batch_reviews
            #         ]
            #         for chunk in tqdm_async(
            #             chunks(tasks, CONCURRENCY), total=len(tasks) // CONCURRENCY
            #         ):
            #             res = await asyncio.gather(*chunk, return_exceptions=True)  # Correctly await the coroutine
            #             for i, e in enumerate(res):
            #                 if isinstance(e, Exception):
            #                     # print(batch_reviews[i])
            #                     # raise e
            #     except UniqueViolationError:
            #         tqdm_sync.write("Skipping duplicate review...")
            #         continue
            #     except Exception as e:
            #         # print(e)
            #         # print(batch_reviews)
            #         continue

        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
