import os

# Database configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hotels")

# SQLAlchemy URL
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Pool configuration
POOL_SIZE = int(os.getenv("POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "30"))
POOL_TIMEOUT = int(os.getenv("POOL_TIMEOUT", "30"))
