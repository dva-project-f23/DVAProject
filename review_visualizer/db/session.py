import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


USERNAME = os.getenv("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
DATABASE_URL = (
    f"mysql+mysqlconnector://{USERNAME}:{PASSWORD}@aws.connect.psdb.cloud/dva-project"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
