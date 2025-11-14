"""Security regression tests for bearer authentication."""

from fastapi.testclient import TestClient


def test_missing_authorization_header_is_rejected(client: TestClient):
    response = client.post("/ingredients", json={"name": "Salt"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing"


def test_invalid_token_is_rejected(client: TestClient):
    headers = {"Authorization": "Bearer not-a-token"}
    response = client.post("/ingredients", json={"name": "Salt"}, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_non_bearer_scheme_is_rejected(client: TestClient):
    headers = {"Authorization": "Basic abc"}
    response = client.post("/ingredients", json={"name": "Salt"}, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing"
