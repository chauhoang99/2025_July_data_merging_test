from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, validator
from typing import Any, Dict, Optional, List

Base = declarative_base()

class Hotel(Base):
    __tablename__ = 'hotels'

    id = Column(String, primary_key=True)
    destination_id = Column(Integer)
    name = Column(String)
    description = Column(String)
    images = Column(JSON)
    location = Column(JSON)
    amenities = Column(JSON)
    booking_conditions = Column(JSON)


class HotelAttribute(Base):
    __tablename__ = 'hotel_attributes'

    id = Column(Integer, primary_key=True)
    hotel_id = Column(String)
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

    @validator("general", "room", pre=True)
    def lower_case_amenities(cls, v):
        return [i.lower() for i in v]


class HotelSerializer(BaseModel):
    id: str
    destination_id: int
    name: str
    description: str
    images: dict
    location: dict
    amenities: dict
    booking_conditions: Optional[List]

    class Config:
        from_attributes = True
