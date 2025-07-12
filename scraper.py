import httpx
import asyncio
from sqlalchemy import create_engine
import html
import json

from pprint import pprint

from models import *


class Scraper:
    def __init__(self):
        self.db_engine = create_engine("sqlite:///hotels.db", echo=True)
        self.sources = {
            'acme': 'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/acme',
            'patagonia': 'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/patagonia',
            'paperflies': 'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/paperflies'
        }
        self.scrapers = {
            'acme': self.acme_scraper,
            'patagonia': self.patagonia_scraper,
            'paperflies': self.paperflies_scraper
        }

    async def acme_scraper(self):
        data = await self.async_request('GET', self.sources['acme'])
        for record in data:
            record = self.sanitize_data(record) # Simple data cleaning

            # Data attribute mapping
            id = record['Id']
            destination_id = record['DestinationId']
            name = record['Name']
            description = record['Description']
            location = LocationSerializer(
                lat=record.get('Latitude'),
                lng=record.get('Longitude'),
                address=record.get('Address'),
                city=record.get('City'),
                country=record.get('Country'),
                postal_code=record.get('PostalCode')
            )
            amenities = AmenitiesSerializer(
                general=record.get('Facilities', [])
            )
            images = ImageSerializer()
            booking_conditions = []

            hotel_attributes = HotelAttribute(
                hotel_id=id,
                source='acme',
                attributes=json.dumps({
                    "id": id,
                    "destination_id": destination_id,
                    "name": name,
                    "description": description,
                    "location": location.model_dump(),
                    "amenities": amenities.model_dump(),
                    "images": images.model_dump(),
                    "booking_conditions": booking_conditions
                })
            )




            




    async def patagonia_scraper(self):
        pass

    async def paperflies_scraper(self):
        pass

    async def sensor(self):
        sources = []
        queries = []
        scrapers = []
        for source in self.sources:
            sources.append(source)
            queries.append(self.async_request('GET', self.sources[source]))
        results = await asyncio.gather(*queries)
        for i in range(len(sources)):
            if len(results[i]):
                scrapers.append(self.scrapers[sources[i]]())
        await asyncio.gather(*scrapers)

    async def async_request(self, method: str, url: str) -> httpx.Response:
        async with httpx.AsyncClient() as client:
             res = await client.request(method=method, url=url, timeout=300)
             res.raise_for_status()
             return res.json()

    def sanitize_string(self, s: str) -> str:
        return html.escape(s.strip())  # trim and escape HTML

    def sanitize_data(self, data):
        if isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self.sanitize_string(data)
        else:
            return data  # leave numbers, bools, None, etc. unchanged


if __name__ == "__main__":
    scraper = Scraper()
    asyncio.run(scraper.sensor())
