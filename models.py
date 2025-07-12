from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, validator
from typing import Optional, List

Base = declarative_base()

class Hotel(Base):
    __tablename__ = 'hotels'

    id = Column(String, primary_key=True)
    destination_id = Column(Integer)
    name = Column(String)
    description = Column(String)
    image = Column(String)
    location = Column(JSON)
    amenities = Column(JSON)
    booking_conditions = Column(JSON)


class HotelAttribute(Base):
    __tablename__ = 'hotel_attributes'

    id = Column(Integer, primary_key=True)
    hotel_id = Column(String, ForeignKey('hotels.id'))
    source = Column(String)
    attributes = Column(JSON)


class ImageNestedSerializer(BaseModel):
    link: str
    description: str


class ImageSerializer(BaseModel):
    rooms: List[ImageNestedSerializer] = []
    site: List[ImageNestedSerializer] = []
    amenities: List[ImageNestedSerializer] = []


class LocationSerializer(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None # can beginning with 0

    @validator("lat", "lng", pre=True)
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class AmenitiesSerializer(BaseModel):
    general: List = []
    room: List = []
