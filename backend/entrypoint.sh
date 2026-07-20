#!/bin/bash
set -e

# Initialize the database and tables
echo "Initializing database..."
python3 -m backend.database_init

# Execute the command passed as CMD
echo "Starting application..."
exec "$@"
