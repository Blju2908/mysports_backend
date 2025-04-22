from sqlmodel import create_engine, Session
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///sqlite.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session 