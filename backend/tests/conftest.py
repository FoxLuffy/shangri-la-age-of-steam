import os
import pytest

# Ensure all tests use an in-memory database to prevent modifying the checked-in saos.db
os.environ["DATABASE_PATH"] = ":memory:"
