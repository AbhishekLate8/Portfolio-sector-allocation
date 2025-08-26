from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from .config import settings
from typing import AsyncGenerator
from urllib.parse import quote_plus

SQLALCHEMY_DATABASE_URL = f'postgresql+asyncpg://{settings.database_username}:{quote_plus(settings.database_password)}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}?sslmode=require'


print(SQLALCHEMY_DATABASE_URL)

# Create the async engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Create the async session maker
AsyncSessionLocal = async_sessionmaker(bind = engine, expire_on_commit=False, class_=AsyncSession)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session