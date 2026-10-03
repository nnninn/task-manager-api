import os

# Mesti ditetapkan SEBELUM import main (security.py perlukan SECRET_KEY)
os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-testing")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base
from main import app, get_db

# Database sementara dalam memori, asing dari database sebenar kau
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# Sebelum setiap test, cipta table baru. Selepas test, buang semua.
@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# Fungsi pembantu: register + login, pulangkan header untuk request
def register_and_login(email, password="password123"):
    client.post("/register", json={"email": email, "password": password})
    response = client.post("/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_success():
    response = client.post(
        "/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "a@example.com"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()


def test_register_duplicate_email():
    client.post("/register", json={"email": "a@example.com", "password": "password123"})
    response = client.post(
        "/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert response.status_code == 400


def test_login_wrong_password():
    client.post("/register", json={"email": "a@example.com", "password": "password123"})
    response = client.post(
        "/login", data={"username": "a@example.com", "password": "salah"}
    )
    assert response.status_code == 401


def test_tasks_require_login():
    response = client.get("/tasks")
    assert response.status_code == 401


def test_create_and_list_tasks():
    headers = register_and_login("a@example.com")
    created = client.post("/tasks", json={"title": "Belajar FastAPI"}, headers=headers)
    assert created.status_code == 200
    assert created.json()["title"] == "Belajar FastAPI"

    listed = client.get("/tasks", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_user_cannot_see_other_users_tasks():
    headers_a = register_and_login("a@example.com")
    headers_b = register_and_login("b@example.com")

    task = client.post("/tasks", json={"title": "Rahsia A"}, headers=headers_a).json()

    assert client.get("/tasks", headers=headers_b).json() == []
    assert client.get(f"/tasks/{task['id']}", headers=headers_b).status_code == 404


def test_update_task():
    headers = register_and_login("a@example.com")
    task = client.post("/tasks", json={"title": "Lama"}, headers=headers).json()

    response = client.put(
        f"/tasks/{task['id']}",
        json={"title": "Baru", "done": True},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Baru"
    assert response.json()["done"] is True


def test_delete_task():
    headers = register_and_login("a@example.com")
    task = client.post("/tasks", json={"title": "Padam saya"}, headers=headers).json()

    assert client.delete(f"/tasks/{task['id']}", headers=headers).status_code == 200
    assert client.get(f"/tasks/{task['id']}", headers=headers).status_code == 404