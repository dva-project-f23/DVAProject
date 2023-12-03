import ast
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm as tqdm_sync
from tqdm.asyncio import tqdm as tqdm_async

load_dotenv()

from generated.prisma.errors import UniqueViolationError
from generated.prisma.types import RelatedProductCreateWithoutRelationsInput
from review_visualizer.db.prisma import PrismaClient

BATCH_SIZE = 10000
CONCURRENCY = 32

with open("reviews_Electronics_5.json") as f:
    review_data = f.readlines()


with open("metadata.json") as f:
    product_data = f.readlines()


async def process_product_line(line, prisma: PrismaClient):
    data = ast.literal_eval(line)
    if not data.get("asin"):
        return None

    # Add related products
    related_products: list[RelatedProductCreateWithoutRelationsInput] = []
    if data.get("related"):
        for relation_type, asins in data["related"].items():
            for related_asin in asins:
                related_product = {
                    "asin": data["asin"],
                    "related_asin": related_asin,
                    "relation_type": relation_type,
                }
                related_products.append(related_product)

    product = await prisma.product.create(
        data={
            "asin": data["asin"],
            "title": data.get("title", None),
            "price": data.get("price", None),
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

    return product


async def process_review_line(line, prisma: PrismaClient):
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
            for i in tqdm_sync(range(0, len(product_data), BATCH_SIZE)):
                batch_products = product_data[i : i + BATCH_SIZE]
                tasks = [process_product_line(line, prisma) for line in batch_products]

                for chunk in tqdm_async(
                    chunks(tasks, CONCURRENCY), total=len(tasks) // CONCURRENCY
                ):
                    try:
                        res = await asyncio.gather(*chunk, return_exceptions=True)
                        for r in res:
                            if isinstance(r, Exception):
                                print(r)
                    except UniqueViolationError:
                        pass
                    except Exception as e:
                        print(e)
                    finally:
                        continue

            # Process Reviews
            print("Processing reviews...")
            for i in tqdm_sync(range(0, len(review_data), BATCH_SIZE)):
                batch_reviews = review_data[i : i + BATCH_SIZE]
                tasks = [process_review_line(line, prisma) for line in batch_reviews]

                for chunk in tqdm_async(
                    chunks(tasks, CONCURRENCY), total=len(tasks) // CONCURRENCY
                ):
                    try:
                        res = await asyncio.gather(*chunk, return_exceptions=True)
                        for r in res:
                            if isinstance(r, Exception):
                                print(r)
                    except UniqueViolationError:
                        pass
                    except Exception as e:
                        print(e)
                    finally:
                        continue

        except Exception as e:
            print(e)


if __name__ == "__main__":
    asyncio.run(main())
