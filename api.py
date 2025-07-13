from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from fastapi import FastAPI, Query, Depends
from itertools import chain

from config import *
from models import *


engine = create_async_engine(DATABASE_URL, echo=True, pool_size=2)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency: get async DB session
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


app = FastAPI()


@app.get("/hotels", response_model=List[HotelSerializer])
async def get_hotels(
    hotel_ids: Optional[List[str]] = Query(None, alias='hotels'),
    destination_id: Optional[int] = Query(None, alias='destination'),
    session: AsyncSession = Depends(get_session)
):
    if hotel_ids:
        hotel_ids = [h.split(',') for h in hotel_ids]
        hotel_ids = list(chain.from_iterable(hotel_ids))

    query = select(Hotel)
    if hotel_ids:
        query = query.where(Hotel.id.in_(hotel_ids))
    if destination_id:
        query = query.where(Hotel.destination_id == destination_id)

    result = await session.execute(query)
    return result.scalars().all()
