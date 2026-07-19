#!/bin/bash
set -e

# Initialize the database and tables
echo "Initializing database..."
python3 -m backend.database_init

# Start the server command (CMD)
echo "Starting server..."
exec "$@"
