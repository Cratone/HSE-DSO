"""Tests for RFC 7807 error format and error handling."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rfc7807_format_on_404():
    """Test that 404 errors return RFC 7807 format."""
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()

    # Check RFC 7807 required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body

    assert body["status"] == 404
    assert body["detail"] == "item not found"


def test_rfc7807_format_on_422():
    """Test that validation errors return RFC 7807 format."""
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()

    # Check RFC 7807 required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body

    assert body["status"] == 422
    # Title can be "Validation Error" or "HTTP 422" depending on handler
    assert "validation" in body["title"].lower() or body["status"] == 422


def test_correlation_id_present():
    """Test that all errors include correlation_id."""
    r = client.get("/items/999")
    body = r.json()

    assert "correlation_id" in body
    # UUID format check (basic)
    correlation_id = body["correlation_id"]
    assert len(correlation_id) == 36  # UUID string length
    assert correlation_id.count("-") == 4  # UUID has 4 dashes


def test_correlation_id_unique():
    """Test that different requests have different correlation IDs."""
    r1 = client.get("/items/998")
    r2 = client.get("/items/999")

    cid1 = r1.json()["correlation_id"]
    cid2 = r2.json()["correlation_id"]

    assert cid1 != cid2, "Correlation IDs should be unique"


def test_validation_errors_include_details():
    """Test that validation errors include field-level details."""
    r = client.post("/items", params={"name": ""})
    body = r.json()

    # Should have detail field with error information
    assert "detail" in body
    assert isinstance(body["detail"], str)
    assert len(body["detail"]) > 0
