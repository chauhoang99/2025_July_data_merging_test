import pytest
import json
from scraper import Scraper
from models import HotelAttribute
from models import Hotel
from sqlalchemy import select
import scraper as scraper_module  # Import the module to mock AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# Sample response data for each source
ACME_RESPONSE = [{
    "Id": "acme_1",
    "DestinationId": 1,
    "Name": "Acme Hotel",
    "Description": "A test hotel from Acme",
    "Latitude": "1.234",
    "Longitude": "4.567",
    "Address": "123 Acme St",
    "City": "Acme City",
    "Country": "Acme Country",
    "PostalCode": "12345",
    "Facilities": ["wifi", "pool"]
}]

PATAGONIA_RESPONSE = [{
    "id": "pat_1",
    "destination": 1,
    "name": "Patagonia Hotel",
    "info": "A test hotel from Patagonia",
    "lat": "1.234",
    "lng": "4.567",
    "address": "123 Pat St",
    "amenities": ["parking", "restaurant"],
    "images": {
        "rooms": [{"url": "room.jpg", "description": "Room"}],
        "site": [{"url": "site.jpg", "description": "Site"}]
    }
}]

PAPERFLIES_RESPONSE = [{
    "hotel_id": "pf_1",
    "destination_id": 1,
    "hotel_name": "Paperflies Hotel",
    "details": "A test hotel from Paperflies",
    "location": {
        "lat": "1.234",
        "lng": "4.567",
        "address": "123 PF St",
        "country": "PF Country"
    },
    "amenities": {
        "general": ["Pool", "Spa"],
        "room": ["TV", "Safe"]
    },
    "images": {
        "rooms": [{"link": "room.jpg", "caption": "Room"}],
        "site": [{"link": "site.jpg", "caption": "Site"}]
    },
    "booking_conditions": ["No smoking"]
}]

@pytest.fixture
def mock_scraper(test_engine, monkeypatch):
    # Create a session factory that will use our test engine
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Replace the AsyncSessionLocal in the scraper module
    monkeypatch.setattr(scraper_module, "AsyncSessionLocal", TestingSessionLocal)
    
    scraper = Scraper()
    # Replace the scraper's session_factory with our test session factory
    scraper.session_factory = TestingSessionLocal
    
    async def mock_async_request(method: str, url: str):
        if url.endswith('/acme'):
            return ACME_RESPONSE
        elif url.endswith('/patagonia'):
            return PATAGONIA_RESPONSE
        elif url.endswith('/paperflies'):
            return PAPERFLIES_RESPONSE
        raise ValueError(f"Unknown URL: {url}")
    
    scraper.async_request = mock_async_request
    return scraper

@pytest.mark.asyncio
async def test_acme_scraper(test_session, mock_scraper):
    """Test scraping from Acme source"""
    await mock_scraper.acme_scraper()

    # Verify the data was saved correctly
    result = await test_session.execute(
        select(HotelAttribute).where(HotelAttribute.source == 'acme')
    )
    hotel_attrs = result.scalars().all()
    
    assert len(hotel_attrs) == 1
    hotel_attr = hotel_attrs[0]
    assert hotel_attr.hotel_id == "acme_1"
    
    attributes = json.loads(hotel_attr.attributes)
    assert attributes["name"] == "Acme Hotel"
    assert attributes["destination_id"] == 1
    assert attributes["location"]["lat"] == 1.234
    assert "wifi" in attributes["amenities"]["general"]

@pytest.mark.asyncio
async def test_patagonia_scraper(test_session, mock_scraper):
    """Test scraping from Patagonia source"""
    await mock_scraper.patagonia_scraper()

    result = await test_session.execute(
        select(HotelAttribute).where(HotelAttribute.source == 'patagonia')
    )
    hotel_attrs = result.scalars().all()
    
    assert len(hotel_attrs) == 1
    hotel_attr = hotel_attrs[0]
    assert hotel_attr.hotel_id == "pat_1"
    
    attributes = json.loads(hotel_attr.attributes)
    assert attributes["name"] == "Patagonia Hotel"
    assert attributes["destination_id"] == 1
    assert len(attributes["images"]["rooms"]) == 1
    assert "parking" in attributes["amenities"]["general"]

@pytest.mark.asyncio
async def test_paperflies_scraper(test_session, mock_scraper):
    """Test scraping from Paperflies source"""
    await mock_scraper.paperflies_scraper()

    result = await test_session.execute(
        select(HotelAttribute).where(HotelAttribute.source == 'paperflies')
    )
    hotel_attrs = result.scalars().all()
    
    assert len(hotel_attrs) == 1
    hotel_attr = hotel_attrs[0]
    assert hotel_attr.hotel_id == "pf_1"
    
    attributes = json.loads(hotel_attr.attributes)
    assert attributes["name"] == "Paperflies Hotel"
    assert attributes["destination_id"] == 1
    assert attributes["booking_conditions"] == ["No smoking"]
    assert "pool" in attributes["amenities"]["general"]
    assert "tv" in attributes["amenities"]["room"]

@pytest.mark.asyncio
async def test_mapper_with_multiple_sources(test_session, mock_scraper):
    """Test mapping data from multiple sources"""
    # Scrape data from all sources
    await mock_scraper.acme_scraper()
    await mock_scraper.patagonia_scraper()
    await mock_scraper.paperflies_scraper()
    
    # Run the mapper
    await mock_scraper.mapper()
    
    # Verify the mapped data
    result = await test_session.execute(select(Hotel))
    hotels = result.scalars().all()
    
    # We should have 3 different hotels
    assert len(hotels) == 3
    
    # Verify each hotel has the correct data based on source priority
    hotel_ids = [h.id for h in hotels]
    assert "acme_1" in hotel_ids
    assert "pat_1" in hotel_ids
    assert "pf_1" in hotel_ids

@pytest.mark.asyncio
async def test_sanitize_data():
    """Test data sanitization"""
    scraper = Scraper()
    test_data = {
        "name": "Test &amp; Hotel",
        "description": "<script>alert('xss')</script>Description",
        "nested": {
            "text": "Nested &quot;quoted&quot; text"
        }
    }
    
    sanitized = scraper.sanitize_data(test_data)
    assert sanitized["name"] == "Test & Hotel"
    assert sanitized["description"] == "Description"
    assert sanitized["nested"]["text"] == 'Nested "quoted" text' 