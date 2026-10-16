import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401
from app.db.base import Base, get_session
from app.main import app


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as s:
        yield s


@pytest.fixture()
def client(session: Session):
    def override():
        yield session

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
