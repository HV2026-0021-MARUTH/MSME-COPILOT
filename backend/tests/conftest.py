import pytest
from app.db.database import init_sqlite_db_and_seed

@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """
    Ensure SQLite database tables are freshly initialized and seeded before each test function.
    """
    init_sqlite_db_and_seed()
