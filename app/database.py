from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from .config import settings
from typing import AsyncGenerator
from urllib.parse import quote_plus
import ssl
from . config import BASE_URL
from pathlib import Path


# Load Supabase certificate
ssl_file_path =Path(settings.SSL_CERT_PATH)  
print(Path(ssl_file_path))
ssl_context = ssl.create_default_context(cafile=ssl_file_path)

SQLALCHEMY_DATABASE_URL = f'postgresql+asyncpg://{settings.database_username}:{quote_plus(settings.database_password)}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}'


print(SQLALCHEMY_DATABASE_URL)

# Create the async engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL,
                             echo=False,
                             poolclass=NullPool,                                                         
                            connect_args={
                                        "ssl": ssl_context  # use the loaded certificate                                  
                                        }
                            )

# Create the async session maker
AsyncSessionLocal = async_sessionmaker(bind = engine, expire_on_commit=False, class_=AsyncSession)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session