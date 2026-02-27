from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.core.database import get_session
from app.main import app

settings = get_settings()
engine = create_engine(settings.test_database_url, echo=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None]:
    """Create all tables before the test session, drop them after."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session]:
    """Provide a transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient]:
    """Test client with the session dependency overridden."""

    def get_session_override() -> Session:
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()
