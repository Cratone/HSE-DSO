"""Shared pytest fixtures and environment hooks."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import STORE, app  # noqa: E402  (import after sys.path tweak)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    STORE.reset()
    yield
    STORE.reset()


@pytest.fixture
def user_credentials() -> dict[str, str]:
    return {"email": "user@example.com", "password": "Str0ngPass123"}


@pytest.fixture
def auth_headers(
    client: TestClient, user_credentials: dict[str, str]
) -> dict[str, str]:
    register = client.post("/auth/register", json=user_credentials)
    assert register.status_code == 201, register.text
    login = client.post("/auth/login", json=user_credentials)
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
