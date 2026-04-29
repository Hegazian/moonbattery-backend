"""pytest fixtures."""

import os
from collections.abc import Generator

# MUST set env vars BEFORE importing any app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import engine as test_engine, get_db
from app.main import app
from app.models import Base

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
