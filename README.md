# How to run

- Make sure your Docker Desktop is up and running.
- Clone this repo to your local
- On your CMD go to the main repo where the docker-compose.yaml file is stored. Which should be the `2025_July_data_merging_test` folder.
- Run `docker compose up -d`
- Wait until all containers start.
- Call GET http://localhost:8000/hotels to see the outcome.

# Why Docker

- Docker is chosen as a deployment solution for this assignment to make sure all the environment variables and dependencies are static across all operation systems. It is to guarantee that the assignment can work on any computer as long as there is Docker installed on that computer.

# What do we have insider Docker

- A PostgreSQL database container
- A scraper container that only run once, you can restart it and it will scrape data then terminate.
- An API server container

# Assumption

- The sources:
  - Since this is a simplified version, I assume that the data returned by suppliers is completed, there is no pagination and there will be no subsequent batch of data after this batch.

# Data merging

- In this assignment I am allowed to merge data by hotel_id and destination_id

# Data cleaning

- String sanitization.
- Using Pydantic serializers to validate and transform the attributes.

# Data Selection

- Content quality control is a huge process involving multiple teams with different domain knowledges. I only can oversimplified it into this set of rules, each rule has its own amount of quality points and criteria. The higher the points the more dependent to the source, like, I'm not going to rewrite the descriptions so I rely on the descriptions come from the source. The lower the points, the easier for me to implement a data fix. If a source can pass 50% of the criteria, it pass the rule and receive the points:

  - **The more attractive the better: 3 points**
    - Has image links.
    - Has informative descriptions.

  - **The more complete the better: 2 points**
    - Has the most attributes that can be mapped to the final API response.
    - Has the least null or empty attributes.

  - **The cleaner data the better: 1 point**
    - Numbers in number format
    - String in good string format:
      - No extra spacing.
      - No broken encoding characters.

- The outcome of my data selection is as following:

  - **Source acme:**
    - 0 points for the first rule:
      - Does not have image links.
      - Has short, too summarised description.
    - 0 points for the second rule:
      - Does not have images and booking_conditions
      - Has null and empty lat and lng in 2 over 3 results.
    - 0 points for the third rule:
      - String has extra spacing.
    - **Total: 0 points**

  - **Source patagonia:**
    - 3 points for the first rule:
      - Has image links in both entries.
      - Has informative description in 1 out of 2 entries (50%).
    - 0 points for the second rule:
      - Has most attributes except booking_conditions.
      - Null attributes in 1 entry.
    - 1 point for the third rule:
      - Numbers are in number format.
      - Strings are clean with no extra spaces or broken characters.
    - **Total: 4 points**

  - **Source paperflies:**
    - 3 points for the first rule:
      - Has image links in both entries.
      - Has informative descriptions for all entries (long, detailed details fields).
    - 2 points for the second rule:
      - Entries have many attributes including nested objects like location, amenities, images, booking_conditions.
      - Very few null or empty attributes; most fields are filled across all entries. Extra: there is one hotel that are not returned by the other 2 sources.
    - 1 point for the third rule:
      - Numbers are correctly formatted where applicable.
      - Strings are clean with no extra spaces or broken characters detected.
    - **Total: 6 points**

- For each attribute, the one from the highest quality source will be selected, in case it is null or empty, the non empty one from the next in rank source will be selected.

# The database:

- PostgreSQL database running inside a docker container.

# Database schema:
```
+------------------------------+
|           hotels             |
+------------------------------+
| id (PK)                      |
| destination_id               |
| name                         |
| description                  |
| images (json)                |
| location (json)              |
| amenities (json)             |
| booking_conditions (json)    |
| created_at                   |
| updated_at                   |
+------------------------------+
         ▲
         │
         │
+-------------------+
| hotel_attributes  |
+-------------------+
| id (PK)           |
| hotel_id (FK)     |
| source            |
| attributes (json) |
| created_at        |
| updated_at        |
+-------------------+
```
- Query activities mainly happen on the table `hotels`.

- **Performance decision:**
  - Table indexing: `hotels.id`, `hotels.destination_id`.
  - All attributes from the sources can be stored in a `json` field.  
    **Reason:** We are not querying by `images`, `location`, `amenities` and `booking_conditions` in this exercise but we need to fetch them very often. By adding them in the table `hotels`, we can avoid writing join queries or subqueries, produce better execution plan for better query performance. In real life, if we need to run query on nested values of those attributes often, we can create columns for them to utilise indexing.

# The Scrapers

- The Scraper is a Python class that mimics the DAG architecture of Apache Airflow in a very simple way.
- One sensoring method to detect new data from the sources. If there is new data, the sensoring method will call the relevant scraper methods to procure data.
- Data cleaning will happen in each scraper; each scraper has its own attribute mapping.
- Each scraper will save its processed data to the `hotel_attributes` table. This is for data quality control later. If needed, I also can do data backfilling by using data in this table.
- About images, so far I don't see a need to treat them separately since we don't include image ranking or image processing in this assignment. The most simplest way to manage them is to keep them in `hotel_attributes`.
- At the end of this workflow, there will be one mapping method that will combine all the cleaned data from the scrapers, do attribute value selection based on source ranking, then save the selected attributes to the right hotel.id in the `hotels` table. Every time there is a new batch of data coming in, this mapping method will check and update the hotels table with attributes, images and location from the highest ranking source available at that time.

  ```
                        +----------------------+
                        |        sensor        |
                        +----------+-----------+
                                   |
                                   v
                  +-----------------------------+
                  |  trigger scraper decision   |
                  +----------------+------------+
                                   |
                                   v
        +------------------+   +--------------------+   +---------------------+
        |   acme_scraper   |   |  patagonia_scraper |   | paperflies_scraper  |
        +--------+---------+   +---------+----------+   +----------+----------+
                 \                     |                         /
                  \                    |                        /
                   \                   |                       /
                    \                  |                      /
                     v                 v                     v
                             +----------------+
                             |     mapper     |
                             +----------------+


- **Performance decision:**
  - The sensor is a lightweight task that will run first to check if there is data to process before spinning up the scrapers. We save resources by using this method.
  - Async scrapers to speed up scraping activity.
  - Each scraper is scalable depending on the amount of data.
  - Data can be processed in chuncks, but usually for data comes from APIs, we can request API with pagination so chunking is not always necessary.

# The API Server

- One simple FastAPI server with one only API: /hotels
- The API acceptps 2 parameters:
  - hotels: an array of strings, which are the hotel ids
  - destination: number, destination id

# Testing plan

- Unit tests that cover over 80% of the code.
- Manually test the scraper.
- Manually test the API call.

# What can be better

- Increase data quality control by implementing source priority for each attribute. For example we can say descriptions from patagonia are always better than the others so we will proritise descriptions from patagonia.
- In Airflow environment, the scrapers can pass the hotel ids to the mapper so the mapper does not need to get hotel ids from the database, saving one more API call.
