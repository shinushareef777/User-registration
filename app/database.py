from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient, errors


try:
    MONGODB_CLIENT = MongoClient("mongodb://root:rootpassword@mongodb:27017")
    mongodb_db = MONGODB_CLIENT["user_registration"]
except errors.ConnectionFailure as e:
    print(f"Failed to connect to MongoDB: {e}")

DATABASE_URL = "postgresql://postgres:root123@postgres-db/fastapi"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
