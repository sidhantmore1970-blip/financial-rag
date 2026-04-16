from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_URL = "sqlite:///./fin_docs.db"

db_engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

MySession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


class Base(DeclarativeBase):
    pass


def setup_db():
    from core import models
    Base.metadata.create_all(bind=db_engine)


def get_db():
    db = MySession()
    try:
        yield db
    finally:
        db.close()
