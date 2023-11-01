from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"

    reviewID = Column(Integer, primary_key=True, autoincrement=True)
    reviewerID = Column(String(255), nullable=False)
    asin = Column(String(255), nullable=False)
    reviewerName = Column(Text)
    helpful = Column(JSON)
    reviewText = Column(Text)
    overall = Column(Float)
    summary = Column(Text)
    unixReviewTime = Column(DateTime)
