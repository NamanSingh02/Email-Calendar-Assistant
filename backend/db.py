from sqlmodel import SQLModel, create_engine, Session
import os

DB_URL = os.getenv("DB_URL", "sqlite:///eca.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

def init_db():
    import models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
