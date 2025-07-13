import httpx
import asyncio
import html
import json
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from config import *
from models import *
from api import engine, AsyncSessionLocal


class Scraper:
    def __init__(self):
        self.engine = engine
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
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
        self.source_priority = {
            'acme': 0,
            'patagonia': 4,
            'paperflies': 6
        }

    async def acme_scraper(self):
        data = await self.async_request('GET', self.sources['acme'])
        mapped_attributes = []
        hotel_ids = []
        for record in data:
            # Simple data cleaning
            record = self.sanitize_data(record) 

            # Data attribute mapping
            id = record['Id']
            hotel_ids.append(id)
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
                general=record['Facilities'] if record.get('Facilities') else []
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
            mapped_attributes.append(hotel_attributes)
        async with AsyncSessionLocal() as session:
            session.add_all(mapped_attributes)
            await session.commit()
        return hotel_ids

    async def patagonia_scraper(self):
        data = await self.async_request('GET', self.sources['patagonia'])
        mapped_attributes = []
        hotel_ids = []
        for record in data:
            record = self.sanitize_data(record) # Simple data cleaning
            # Data attribute mapping
            id = record['id']
            hotel_ids.append(id)
            destination_id = record['destination']
            name = record['name']
            description = record['info']
            location = LocationSerializer(
                lat=record.get('lat'),
                lng=record.get('lng'),
                address=record.get('address')
            )
            amenities = AmenitiesSerializer(
                general=record['amenities'] if record.get('amenities') else []
            )
            images = ImageSerializer(
                rooms=[
                    ImageNestedSerializer(
                        link=image.get('url'),
                        description=image.get('description')
                    ) for image in record.get('images', {}).get('rooms', [])
                ],
                site=[
                    ImageNestedSerializer(
                        link=image.get('url'),
                        description=image.get('description')
                    ) for image in record.get('images', {}).get('site', [])
                ],
                amenities=[
                    ImageNestedSerializer(
                        link=image.get('url'),
                        description=image.get('description')
                    ) for image in record.get('images', {}).get('amenities', [])
                ]
            )
            
            booking_conditions = []

            hotel_attributes = HotelAttribute(
                hotel_id=id,
                source='patagonia',
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
            mapped_attributes.append(hotel_attributes)
        async with AsyncSessionLocal() as session:
            session.add_all(mapped_attributes)
            await session.commit()
        return hotel_ids

    async def paperflies_scraper(self):
        data = await self.async_request('GET', self.sources['paperflies'])
        mapped_attributes = []
        hotel_ids = []
        for record in data:
            record = self.sanitize_data(record) # Simple data cleaning
            # Data attribute mapping
            id = record['hotel_id']
            hotel_ids.append(id)
            destination_id = record['destination_id']
            name = record['hotel_name']
            description = record['details']
            location = LocationSerializer(
                lat=record.get('location', {}).get('lat'),
                lng=record.get('location', {}).get('lng'),
                address=record.get('location', {}).get('address'),
                country=record.get('location', {}).get('country')
            )
            source_amenities = record.get('amenities')
            general_amenities = source_amenities['general'] if source_amenities.get('general') else []
            general_amenities = [amenity.title() for amenity in general_amenities]

            room_amenities = source_amenities['room'] if source_amenities.get('room') else []
            amenities = AmenitiesSerializer(
                general=general_amenities,
                room=room_amenities
            ) if source_amenities else None
            images = ImageSerializer(
                rooms=[
                    ImageNestedSerializer(
                        link=image.get('link'),
                        description=image.get('caption')
                    ) for image in record.get('images', {}).get('rooms', [])
                ],
                site=[
                    ImageNestedSerializer(
                        link=image.get('link'),
                        description=image.get('caption')
                    ) for image in record.get('images', {}).get('site', [])
                ],
                amenities=[
                    ImageNestedSerializer(
                        link=image.get('link'),
                        description=image.get('caption')
                    ) for image in record.get('images', {}).get('amenities', [])
                ]
            )
            
            booking_conditions = record.get('booking_conditions')

            hotel_attributes = HotelAttribute(
                hotel_id=id,
                source='paperflies',
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
            mapped_attributes.append(hotel_attributes)
        async with AsyncSessionLocal() as session:
            session.add_all(mapped_attributes)
            await session.commit()
        return hotel_ids

    async def data_merging(self, hotel_ids):
        async with AsyncSessionLocal() as session:
            hotels = []
            for id in hotel_ids:
                query = select(HotelAttribute).where(HotelAttribute.hotel_id == id)
                result = await session.execute(query)
                attributes = result.scalars().all()
                sorted_attributes = sorted(
                    attributes,
                    key=lambda x: self.source_priority.get(x.source, 0),
                    reverse=True
                )
                sorted_attributes = [json.loads(attributes.attributes) for attributes in sorted_attributes]

                id = id
                destination_id = self.get_attribute_value(sorted_attributes, 'destination_id')
                name = self.get_attribute_value(sorted_attributes, 'name')
                description = self.get_attribute_value(sorted_attributes, 'description')
                booking_conditions = self.get_attribute_value(sorted_attributes, 'booking_conditions')

                sorted_locations = [attributes.get('location') for attributes in sorted_attributes]
                location = {
                    'lat': self.get_attribute_value(sorted_locations, 'lat'),
                    'lng': self.get_attribute_value(sorted_locations, 'lng'),
                    'address': self.get_attribute_value(sorted_locations, 'address'),
                    'country': self.get_attribute_value(sorted_locations, 'country')
                }

                sorted_amenities = [attributes.get('amenities') for attributes in sorted_attributes]
                amenities = {
                    'general': self.get_attribute_value(sorted_amenities, 'general', []),
                    'room': self.get_attribute_value(sorted_amenities, 'room', [])
                }

                sorted_images = [attributes.get('images') for attributes in sorted_attributes]
                images = {
                    'rooms': self.get_attribute_value(sorted_images, 'rooms', []),
                    'site': self.get_attribute_value(sorted_images, 'site', []),
                    'amenities': self.get_attribute_value(sorted_images, 'amenities', [])
                }

                hotels.append(Hotel(
                    id=id,
                    destination_id=destination_id,
                    name=name,
                    description=description,
                    booking_conditions=booking_conditions,
                    location=location,
                    amenities=amenities,
                    images=images,
                ))
            async with self.session_factory() as session:
                session.add_all(hotels)
                await session.commit()

    async def sensor(self):
        sources = []
        queries = []
        scrapers = []
        all_hotel_ids = set()
        for source in self.sources:
            sources.append(source)
            queries.append(self.async_request('GET', self.sources[source]))
        results = await asyncio.gather(*queries)
        for i in range(len(sources)):
            if len(results[i]):
                scrapers.append(self.scrapers[sources[i]]())
        scraper_results = await asyncio.gather(*scrapers)

        # Collect all unique hotel IDs from scrapers
        for hotel_ids in scraper_results:
            all_hotel_ids.update(hotel_ids)

        # Mapping all clustered data with collected IDs
        await self.data_merging(list(all_hotel_ids))

    async def async_request(self, method: str, url: str) -> httpx.Response:
        async with httpx.AsyncClient() as client:
             res = await client.request(method=method, url=url, timeout=300)
             res.raise_for_status()
             return res.json()

    def sanitize_string(self, s: str) -> str:
        s = html.unescape(s.strip())  # First unescape any HTML entities
        s = re.sub(r'<script\b[^>]*>.*?</script>', '', s, flags=re.IGNORECASE | re.DOTALL)  # Remove script tags and their content
        s = re.sub(r'<[^>]+>', '', s)  # Remove other HTML tags
        return s

    def sanitize_data(self, data):
        if isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self.sanitize_string(data)
        else:
            return data  # leave numbers, bools, None, etc. unchanged
        
    def get_attribute_value(self, sorted_attributes: List[dict], attribute_name: str, default_data = None):
        for attributes in sorted_attributes:
            if attributes.get(attribute_name) not in [None, "", []]:
                return attributes[attribute_name]
        return default_data


if __name__ == "__main__":
    scraper = Scraper()
    asyncio.run(scraper.sensor())
