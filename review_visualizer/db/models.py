from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    asin = Column(String, unique=True)
    title = Column(String)
    price = Column(Float)
    imUrl = Column(String)
    primaryCategory = Column(String)  # Key of JSON field - Sales Rank
    salesRank = Column(Integer)  # Value of JSON field - Sales Rank
    brand = Column(String)

    categories = relationship("Category", secondary="product_category_link")
    reviews = relationship("Review", backref="product")
    related_products = relationship("RelatedProduct", backref="product")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    reviewerID = Column(String)
    asin = Column(String, ForeignKey("products.asin"))
    reviewerName = Column(String)
    helpfulCount = Column(Integer)  # Number of people who found the review helpful
    totalHelpfulCount = Column(
        Integer
    )  # Total number of people who rated the review for helpfulness
    reviewText = Column(Text)
    overall = Column(Float)
    summary = Column(Text)
    unixReviewTime = Column(DateTime)


class RelatedProduct(Base):
    __tablename__ = "related_products"

    id = Column(Integer, primary_key=True)
    asin = Column(String, ForeignKey("products.asin"))
    related_asin = Column(String)  # ASIN of the related product
    relation_type = Column(String)  # e.g., also_bought, also_viewed, etc.


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String)
