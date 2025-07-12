import sqlite3
from config import DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS hotels (
    id TEXT PRIMARY KEY,
    destination_id INTEGER,
    name TEXT,
    description TEXT,
    images JSON,
    location JSON,
    attributes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hotel_attributes (
    id INTEGER PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    source TEXT,
    attributes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_hotels_id ON hotels(id);
CREATE INDEX IF NOT EXISTS idx_hotels_destination_id ON hotels(destination_id);
"""

def create_database(db_path: str, schema: str):
    # Connect to the SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute the schema
    cursor.executescript(schema)

    # Commit and close
    conn.commit()
    conn.close()
    print(f"Database schema created at: {db_path}")

if __name__ == "__main__":
    create_database(DB_PATH, SCHEMA_SQL)
