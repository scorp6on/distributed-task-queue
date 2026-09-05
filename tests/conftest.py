import os

os.environ["DATABASE_URL"] = "postgresql+psycopg2://taskq:taskq@localhost:5433/taskq_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.celery_app import celery_app
from app.db import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import Job

celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.query(Job).delete()
        session.commit()
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes():
    def _make(size=(800, 600), color="red", mode="RGB"):
        buf = io.BytesIO()
        Image.new(mode, size, color).save(buf, format="PNG")
        buf.seek(0)
        return buf

    return _make
