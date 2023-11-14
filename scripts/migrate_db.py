import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

load_dotenv()

from review_visualizer.db.models import Base, Product, RelatedProduct, Review

USERNAME = os.getenv("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
MYSQL_DB_URL = (
    f"mysql+mysqlconnector://{USERNAME}:{PASSWORD}@aws.connect.psdb.cloud/dva-project"
)
SQLITE_DB_URL = "sqlite:///test.db"

# SQLite setup
sqlite_engine = create_engine(SQLITE_DB_URL, echo=False)
SQLiteSession = sessionmaker(bind=sqlite_engine)

# MySQL setup
mysql_engine = create_engine(MYSQL_DB_URL, echo=False)
MySQLSession = sessionmaker(bind=mysql_engine)

Base.metadata.create_all(bind=mysql_engine)

BATCH_SIZE = 100


def transfer_data_in_batches(query, mysql_session):
    offset = 0
    while True:
        batch = query.limit(BATCH_SIZE).offset(offset).all()
        if not batch:
            break

        for item in tqdm(batch):
            mysql_session.merge(item)

        mysql_session.commit()
        offset += BATCH_SIZE


def transfer_data():
    sqlite_session = SQLiteSession()
    mysql_session = MySQLSession()

    try:
        # Transfer Products in batches
        product_query = sqlite_session.query(Product)
        transfer_data_in_batches(product_query, mysql_session)

        # Transfer Reviews in batches
        review_query = sqlite_session.query(Review)
        transfer_data_in_batches(review_query, mysql_session)

        # Transfer RelatedProducts in batches
        related_product_query = sqlite_session.query(RelatedProduct)
        transfer_data_in_batches(related_product_query, mysql_session)

    except Exception as e:
        print(f"An error occurred: {e}")
        mysql_session.rollback()
    finally:
        sqlite_session.close()
        mysql_session.close()


# Run the data transfer
transfer_data()
