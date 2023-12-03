import os

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text

# from review_visualizer.db.models import Product
# from review_visualizer.db.session import get_db, init_db


def test_placeholder():
    assert True


# def test_init_db():
#     # Ensure that init_db doesn't raise any exceptions
#     init_db()


# def test_get_db():
#     init_db()
#     with get_db() as db:
#         prod = db.query(Product).first()
#         assert prod is not None
#         assert db is not None
#         assert db.is_active is True
