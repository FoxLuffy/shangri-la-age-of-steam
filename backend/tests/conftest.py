import os
import tempfile
import pytest

# Create a temporary file for the database
db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_PATH"] = db_path

@pytest.fixture(autouse=True, scope="session")
def setup_global_db():
    from backend.database import create_db_and_tables
    create_db_and_tables()
    yield
    os.close(db_fd)
    os.unlink(db_path)

