#!/bin/bash
set -e

# Initialize the database and tables
echo "Initializing database..."
python3 -m backend.database_init

# Start the FastAPI server
echo "Starting backend server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
