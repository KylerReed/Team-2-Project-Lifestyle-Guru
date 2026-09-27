from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Database Configuration

DATABASE_URL = "sqlite:///./lifestyle.db"


# Database Engine


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# Database Session 


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base Class


Base = declarative_base()


# Database Dependency


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
