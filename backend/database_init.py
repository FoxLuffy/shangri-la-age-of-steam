import os
from sqlmodel import SQLModel, create_engine
from backend.database import create_db_and_tables
from sqlalchemy import Column, String, JSON

# This script is for manual database initialization and seeding
def seed_data():
    create_db_and_tables()
    print("Tables created successfully.")
    # Add seeding logic here if needed
    # For now, just ensuring tables are created.

if __name__ == "__main__":
    seed_data()
