import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def _fresh_schema():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def _no_redis_cache(monkeypatch):
    # Unit tests must not depend on (or be polluted by) a real Redis instance --
    # e.g. two tests reusing the same Steam appid would otherwise read back
    # whichever payload the first test cached, instead of their own mock.
    monkeypatch.setattr("app.steam_client.cached", lambda key, loader, ttl_seconds=None: loader())


@pytest.fixture(autouse=True)
def _no_itad_backfill(monkeypatch):
    # Tests must not depend on a real ITAD API key or network call -- even
    # though backend/.env has a real key for local/manual testing, unit tests
    # pretend it's unset so `_backfill_history` takes its no-op path. Tests
    # that specifically exercise the backfill override this.
    monkeypatch.setattr("app.routers.games.settings.itad_api_key", "")


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    # Intentionally not using TestClient as a context manager: that would
    # trigger the app's lifespan, which opens a Redis pub/sub connection we
    # don't want (or need) for plain HTTP endpoint tests.
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
