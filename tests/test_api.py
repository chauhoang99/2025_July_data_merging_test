import pytest
from fastapi import status
from models import Hotel

@pytest.mark.asyncio
async def test_get_hotels_empty(test_client):
    """Test getting hotels when database is empty"""
    response = test_client.get("/hotels")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_hotels_with_data(test_client, test_session, sample_hotel_data):
    """Test getting hotels with sample data"""
    # Create a test hotel
    hotel = Hotel(**sample_hotel_data)
    test_session.add(hotel)
    await test_session.commit()

    # Test getting all hotels
    response = test_client.get("/hotels")
    assert response.status_code == status.HTTP_200_OK
    hotels = response.json()
    assert len(hotels) == 1
    assert hotels[0]["id"] == sample_hotel_data["id"]
    assert hotels[0]["name"] == sample_hotel_data["name"]

@pytest.mark.asyncio
async def test_get_hotels_by_id(test_client, test_session, sample_hotel_data):
    """Test getting hotels by specific IDs"""
    # Create test hotels
    hotel1 = Hotel(**sample_hotel_data)
    hotel2 = Hotel(
        id="test_hotel_2",
        destination_id=2,
        name="Test Hotel 2",
        description="Another test hotel",
        location=sample_hotel_data["location"],
        amenities=sample_hotel_data["amenities"],
        images=sample_hotel_data["images"],
        booking_conditions=[]
    )
    
    test_session.add(hotel1)
    test_session.add(hotel2)
    await test_session.commit()

    # Test filtering by hotel IDs
    response = test_client.get("/hotels?hotels=test_hotel_1,test_hotel_2")
    assert response.status_code == status.HTTP_200_OK
    hotels = response.json()

    assert len(hotels) == 2
    hotel_ids = [h["id"] for h in hotels]
    assert "test_hotel_1" in hotel_ids
    assert "test_hotel_2" in hotel_ids

    # Test filtering by hotel IDs
    response = test_client.get("/hotels?hotels=test_hotel_1&hotels=test_hotel_2")
    assert response.status_code == status.HTTP_200_OK
    hotels = response.json()
    assert len(hotels) == 2


@pytest.mark.asyncio
async def test_get_hotels_by_destination(test_client, test_session, sample_hotel_data):
    """Test getting hotels by destination ID"""
    # Create test hotels with different destinations
    hotel1 = Hotel(**sample_hotel_data)  # destination_id = 1
    hotel2 = Hotel(
        id="test_hotel_2",
        destination_id=2,
        name="Test Hotel 2",
        description="Another test hotel",
        location=sample_hotel_data["location"],
        amenities=sample_hotel_data["amenities"],
        images=sample_hotel_data["images"],
        booking_conditions=[]
    )
    
    test_session.add(hotel1)
    test_session.add(hotel2)
    await test_session.commit()

    # Test filtering by destination
    response = test_client.get("/hotels?destination=1")
    assert response.status_code == status.HTTP_200_OK
    hotels = response.json()
    assert len(hotels) == 1
    assert hotels[0]["destination_id"] == 1

@pytest.mark.asyncio
async def test_get_hotels_invalid_params(test_client):
    """Test getting hotels with invalid parameters"""
    # Test with invalid destination ID format
    response = test_client.get("/hotels?destination=invalid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with non-existent hotel IDs
    response = test_client.get("/hotels?hotels=non_existent_1,non_existent_2")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [] 