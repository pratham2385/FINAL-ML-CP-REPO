"""
backend/tests/test_health.py
Tests for system health check, documentation, and root endpoints.
"""

from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data
    assert data["docs"] == "/docs"

def test_docs_available(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "html" in response.text.lower()

def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Email Spam and Phishing Detection API"
    assert "/api/health" in schema["paths"]
    assert "/api/analyze/email" in schema["paths"]
    assert "/api/analyze/url" in schema["paths"]
    assert "/api/analyze/file" in schema["paths"]
    assert "/api/history" in schema["paths"]
    assert "/api/history/{id}" in schema["paths"]

def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "ml_pipeline" in data
    assert "database" in data
    
    ml = data["ml_pipeline"]
    assert ml["status"] == "operational"
    assert ml["email_model_loaded"] is True
    assert ml["email_tfidf_loaded"] is True
    assert ml["url_model_loaded"] is True
    assert ml["url_features_monitored"] == 18

    db = data["database"]
    assert db["status"] == "connected"
    assert "phishing_detection" in db["database_name"]
    assert db["dialect"] == "postgresql"
