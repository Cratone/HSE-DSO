"""Tests for registration and login flows."""

from fastapi.testclient import TestClient


def test_user_can_register_and_login(client: TestClient):
    payload = {"email": "alice@example.com", "password": "Str0ngPass123"}
    register = client.post("/auth/register", json=payload)
    assert register.status_code == 201
    assert register.json()["email"] == payload["email"]

    login = client.post("/auth/login", json=payload)
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == payload["email"]


def test_duplicate_registration_rejected(client: TestClient):
    payload = {"email": "dup@example.com", "password": "DupPass123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_fails(client: TestClient):
    payload = {"email": "bob@example.com", "password": "Secure123"}
    client.post("/auth/register", json=payload)

    wrong = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "WrongPass123"},
    )
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == "Invalid credentials"


def test_password_policy_enforced(client: TestClient):
    payload = {"email": "weak@example.com", "password": "password"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    assert "password" in response.text
