import pytest
from app.db.database import init_sqlite_db_and_seed, engine
from app.db.models import Base
from app.main import app
from app.api.deps import get_current_user

def mock_get_current_user():
    return {"id": "test-user-id", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """
    Ensure SQLite database tables are freshly initialized and seeded before each test function.
    """
    if engine.name == "sqlite":
        Base.metadata.drop_all(bind=engine)
    init_sqlite_db_and_seed()
