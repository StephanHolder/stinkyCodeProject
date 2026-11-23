import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def api_client(test_engine, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services import housing_auth, listings

    monkeypatch.setattr(housing_auth, "engine", test_engine)
    monkeypatch.setattr(listings, "engine", test_engine)
    return TestClient(app)
