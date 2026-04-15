from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/exportdb"
)

# 🔥 ENV MODE (dev vs prod)
ENV = os.getenv("ENV", "dev")

engine = create_async_engine(
    DATABASE_URL,
    echo=(ENV == "dev"),  # only log in dev
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()