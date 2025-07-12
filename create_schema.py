import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import DATABASE_URL
from models import Base

# Define indexes separately
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_hotels_id ON hotels(id)",
    "CREATE INDEX IF NOT EXISTS idx_hotels_destination_id ON hotels(destination_id)",
    "CREATE INDEX IF NOT EXISTS idx_hotel_attributes_hotel_id ON hotel_attributes(hotel_id)",
    "CREATE INDEX IF NOT EXISTS idx_hotel_attributes_source ON hotel_attributes(source)"
]

async def create_database():
    """Create database schema using SQLAlchemy models"""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)

        # Create all tables from models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Drop existing tables
            await conn.run_sync(Base.metadata.create_all)  # Create tables

            # Create indexes one by one
            for index_sql in INDEXES:
                await conn.execute(text(index_sql))

            await conn.commit()

        print("Database schema created successfully!")

        # Close engine
        await engine.dispose()

    except Exception as e:
        print(f"Error creating database schema: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(create_database())
