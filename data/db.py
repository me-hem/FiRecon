from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data.entities import Base


DATABASE_URL = "sqlite:///./firecon.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
