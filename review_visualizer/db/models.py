"""
Example Code
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    rating = Column(Float, nullable=False)
    title = Column(String, nullable=False)
    review_text = Column(String, nullable=False)
    review_date = Column(DateTime, nullable=False)
