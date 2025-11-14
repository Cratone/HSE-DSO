"""Integration tests for Recipe Box CRUD flows."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register_and_login(
    client: TestClient, email: str, password: str = "AnotherPass123"
) -> dict[str, str]:
    payload = {"email": email, "password": password}
    register = client.post("/auth/register", json=payload)
    assert register.status_code == 201, register.text
    login = client.post("/auth/login", json=payload)
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _current_user_id(client: TestClient, headers: dict[str, str]) -> int:
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _create_ingredient(
    client: TestClient, headers: dict[str, str], name: str = "Sugar"
) -> dict:
    response = client.post("/ingredients", json={"name": name}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _create_recipe(
    client: TestClient,
    headers: dict[str, str],
    ingredient_id: int,
    title: str = "Chocolate cake",
) -> dict:
    payload = {
        "title": title,
        "steps": "Mix and bake",
        "ingredients": [
            {
                "ingredient_id": ingredient_id,
                "amount": "100.5",
                "unit": "g",
            }
        ],
    }
    response = client.post("/recipes", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_recipe(client: TestClient, auth_headers: dict[str, str]):
    ingredient = _create_ingredient(client, auth_headers, name="Flour")
    created = _create_recipe(
        client, auth_headers, ingredient_id=ingredient["id"], title="Bread"
    )

    fetched = client.get(f"/recipes/{created['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["title"] == "Bread"
    assert body["owner_id"] == _current_user_id(client, auth_headers)
    assert len(body["ingredients"]) == 1
    assert body["ingredients"][0]["ingredient_id"] == ingredient["id"]


def test_recipe_filter_by_ingredient_name(
    client: TestClient, auth_headers: dict[str, str]
):
    sugar = _create_ingredient(client, auth_headers, name="Sugar")
    salt = _create_ingredient(client, auth_headers, name="Salt")
    _create_recipe(client, auth_headers, ingredient_id=sugar["id"], title="Cake")
    _create_recipe(client, auth_headers, ingredient_id=salt["id"], title="Soup")

    response = client.get(
        "/recipes", params={"ingredient": "sugar"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Cake"


def test_recipe_owner_isolation(client: TestClient, auth_headers: dict[str, str]):
    ingredient = _create_ingredient(client, auth_headers)
    created = _create_recipe(client, auth_headers, ingredient_id=ingredient["id"])

    other_headers = _register_and_login(client, email="second@example.com")

    response = client.get(f"/recipes/{created['id']}", headers=other_headers)
    assert response.status_code == 404


def test_recipe_update_and_delete(client: TestClient, auth_headers: dict[str, str]):
    flour = _create_ingredient(client, auth_headers, name="Flour")
    salt = _create_ingredient(client, auth_headers, name="Salt")
    created = _create_recipe(
        client, auth_headers, ingredient_id=flour["id"], title="Bread"
    )

    update_payload = {
        "title": "Salted Bread",
        "ingredients": [
            {
                "ingredient_id": salt["id"],
                "amount": "5",
                "unit": "g",
            }
        ],
    }
    update_resp = client.patch(
        f"/recipes/{created['id']}",
        json=update_payload,
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Salted Bread"
    assert update_resp.json()["ingredients"][0]["ingredient_id"] == salt["id"]

    delete_resp = client.delete(f"/recipes/{created['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204

    follow_up = client.get(f"/recipes/{created['id']}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_unknown_ingredient_rejected(client: TestClient, auth_headers: dict[str, str]):
    payload = {
        "title": "Ghost recipe",
        "steps": "N/A",
        "ingredients": [
            {
                "ingredient_id": 999,
                "amount": "10",
                "unit": "g",
            }
        ],
    }
    response = client.post("/recipes", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert "Unknown ingredient" in response.json()["detail"]


def test_duplicate_ingredient_name_denied(
    client: TestClient, auth_headers: dict[str, str]
):
    first = client.post("/ingredients", json={"name": "Butter"}, headers=auth_headers)
    assert first.status_code == 200

    second = client.post("/ingredients", json={"name": "Butter"}, headers=auth_headers)
    assert second.status_code == 409
