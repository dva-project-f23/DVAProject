import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text
from review_visualizer.db.session import get_db, init_db


def test_db_connection():
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.environ.get("PASSWORD")
    DATABASE_URL = f"mysql+mysqlconnector://{USERNAME}:{PASSWORD}@aws.connect.psdb.cloud/dva-project"

    # Test that the database connection is working
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    query = text("SELECT 1;")
    result = connection.execute(query)
    assert result.scalar() == 1


def test_init_db():
    # Ensure that init_db doesn't raise any exceptions
    init_db()


def test_get_db():
    init_db()
    with get_db() as db:
        assert db is not None
        assert db.is_active is True
