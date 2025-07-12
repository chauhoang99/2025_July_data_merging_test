#!/bin/bash
set -e

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL to start..."
    while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER
    do
        sleep 1
    done
    echo "PostgreSQL is ready!"
}

# Main startup sequence
if [ "$1" = "api" ]; then
    wait_for_postgres
    echo "Initializing database schema..."
    python create_schema.py
    echo "Starting API server..."
    exec uvicorn api:app --host 0.0.0.0 --port 8000 --reload

elif [ "$1" = "scraper" ]; then
    wait_for_postgres
    echo "Starting scraper..."
    exec python scraper.py

else
    exec "$@"
fi 