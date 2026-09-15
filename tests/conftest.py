import pytest
from apps.api.src.db.models import Base
from apps.api.src.db.session import sync_engine


@pytest.fixture(scope="session", autouse=True)
def setup_database_schema():
    """Ensure all SQLAlchemy tables exist in PostgreSQL prior to running test suite."""
    Base.metadata.create_all(bind=sync_engine)
    yield
