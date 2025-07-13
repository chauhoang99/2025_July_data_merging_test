import pytest
from models import (
    Hotel,
    HotelAttribute,
    ImageNestedSerializer,
    ImageSerializer,
    LocationSerializer,
    AmenitiesSerializer,
    HotelSerializer
)

def test_location_serializer():
    """Test LocationSerializer validation and conversion"""
    # Test valid data
    location_data = {
        "lat": 1.234,
        "lng": 4.567,
        "address": "123 Test St",
        "city": "Test City",
        "country": "Test Country",
        "postal_code": "12345"
    }
    location = LocationSerializer(**location_data)
    assert location.lat == 1.234
    assert location.address == "123 Test St"

    # Test empty string conversion to None
    empty_location = LocationSerializer(lat="", lng=4.567)
    assert empty_location.lat is None
    assert empty_location.lng == 4.567

def test_amenities_serializer():
    """Test AmenitiesSerializer validation and conversion"""
    amenities_data = {
        "general": ["WiFi", "PARKING", "Pool"],
        "room": ["TV", "Safe", "Mini-Bar"]
    }
    amenities = AmenitiesSerializer(**amenities_data)
    
    # Test lowercase conversion
    assert "wifi" in amenities.general
    assert "parking" in amenities.general
    assert "tv" in amenities.room
    assert "safe" in amenities.room

    # Test empty lists
    empty_amenities = AmenitiesSerializer(general=[], room=[])
    assert empty_amenities.general == []
    assert empty_amenities.room == []

def test_image_nested_serializer():
    """Test ImageNestedSerializer validation"""
    image_data = {
        "link": "https://example.com/image.jpg",
        "description": "Test image"
    }
    image = ImageNestedSerializer(**image_data)
    assert image.link == image_data["link"]
    assert image.description == image_data["description"]

def test_image_serializer():
    """Test ImageSerializer validation"""
    image_data = {
        "rooms": [
            {"link": "room1.jpg", "description": "Room 1"},
            {"link": "room2.jpg", "description": "Room 2"}
        ],
        "site": [
            {"link": "site1.jpg", "description": "Site 1"}
        ],
        "amenities": []
    }
    images = ImageSerializer(**image_data)
    assert len(images.rooms) == 2
    assert len(images.site) == 1
    assert len(images.amenities) == 0
    assert images.rooms[0].link == "room1.jpg"

@pytest.mark.asyncio
async def test_hotel_model(test_session, sample_hotel_data):
    """Test Hotel model database operations"""
    # Create a test hotel
    hotel = Hotel(
        id=sample_hotel_data["id"],
        destination_id=sample_hotel_data["destination_id"],
        name=sample_hotel_data["name"],
        description=sample_hotel_data["description"],
        location=sample_hotel_data["location"],
        amenities=sample_hotel_data["amenities"],
        images=sample_hotel_data["images"],
        booking_conditions=sample_hotel_data["booking_conditions"]
    )
    
    test_session.add(hotel)
    await test_session.commit()
    await test_session.refresh(hotel)

    # Verify the hotel was saved correctly
    assert hotel.id == sample_hotel_data["id"]
    assert hotel.name == sample_hotel_data["name"]
    assert hotel.destination_id == sample_hotel_data["destination_id"]

@pytest.mark.asyncio
async def test_hotel_attribute_model(test_session, sample_hotel_data):
    """Test HotelAttribute model database operations"""
    # Create a test hotel attribute
    hotel_attr = HotelAttribute(
        hotel_id=sample_hotel_data["id"],
        source="test_source",
        attributes=sample_hotel_data
    )
    
    test_session.add(hotel_attr)
    await test_session.commit()
    await test_session.refresh(hotel_attr)

    # Verify the hotel attribute was saved correctly
    assert hotel_attr.hotel_id == sample_hotel_data["id"]
    assert hotel_attr.source == "test_source"
    assert isinstance(hotel_attr.attributes, dict)

def test_hotel_serializer(sample_hotel_data):
    """Test HotelSerializer validation"""
    hotel = HotelSerializer(**sample_hotel_data)
    assert hotel.id == sample_hotel_data["id"]
    assert hotel.name == sample_hotel_data["name"]
    assert hotel.destination_id == sample_hotel_data["destination_id"]
    assert isinstance(hotel.images, dict)
    assert isinstance(hotel.location, dict)
    assert isinstance(hotel.amenities, dict) 