"""
backend/tests/test_database_history.py
Integration and unit tests for PostgreSQL database persistence, retrieval,
pagination, filtering, deletion, and connection failure handling.
"""

import io
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from backend.app.db.session import check_db_connection
from backend.app.db.models.history import AnalysisHistory

def test_email_analysis_persistence(client: TestClient, sample_clean_email):
    """Verifies that an email analysis is automatically persisted to PostgreSQL."""
    response = client.post("/api/analyze/email", json=sample_clean_email)
    assert response.status_code == 200
    data = response.json()
    
    record_id = data.get("id")
    assert record_id is not None
    assert isinstance(record_id, int)

    # Fetch via history detail endpoint to verify persistence
    detail_res = client.get(f"/api/history/{record_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == record_id
    assert detail["analysis_type"] == "email"
    assert detail["subject"] == sample_clean_email["subject"]
    assert detail["email_prediction"] == "Ham"
    assert "complete_analysis_result" in detail

def test_url_analysis_persistence(client: TestClient, sample_phishing_url):
    """Verifies that standalone URL analysis is automatically persisted to PostgreSQL."""
    response = client.post("/api/analyze/url", json={"url": sample_phishing_url})
    assert response.status_code == 200
    data = response.json()
    
    record_id = data.get("id")
    assert record_id is not None
    assert isinstance(record_id, int)

    detail_res = client.get(f"/api/history/{record_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == record_id
    assert detail["analysis_type"] == "url"
    assert detail["submitted_url"] == sample_phishing_url
    assert detail["threat_level"] == "CRITICAL"
    assert detail["recommended_action"] == "BLOCK"

def test_file_analysis_persistence(client: TestClient, sample_clean_eml_bytes):
    """Verifies that .eml file analysis is automatically persisted to PostgreSQL."""
    file_payload = {
        "file": ("audit_memo.eml", io.BytesIO(sample_clean_eml_bytes), "message/rfc822")
    }
    response = client.post("/api/analyze/file", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    
    record_id = data.get("id")
    assert record_id is not None
    assert isinstance(record_id, int)

    detail_res = client.get(f"/api/history/{record_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == record_id
    assert detail["analysis_type"] == "file"
    assert detail["subject"] == "Team Sync Tomorrow"

def test_history_pagination(client: TestClient):
    """Verifies offset/limit pagination on GET /api/history."""
    # Ensure at least 3 records exist
    client.post("/api/analyze/email", json={"subject": "Page test 1", "message": "hello"})
    client.post("/api/analyze/email", json={"subject": "Page test 2", "message": "hello"})
    client.post("/api/analyze/email", json={"subject": "Page test 3", "message": "hello"})

    response = client.get("/api/history?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    # Query next offset
    response2 = client.get("/api/history?limit=2&offset=2")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["offset"] == 2
    assert len(data2["items"]) >= 1

def test_history_type_filtering(client: TestClient):
    """Verifies filtering history records by analysis_type."""
    # Query email records
    res_email = client.get("/api/history?analysis_type=email")
    assert res_email.status_code == 200
    data_email = res_email.json()
    for item in data_email["items"]:
        assert item["analysis_type"] == "email"

    # Query url records
    res_url = client.get("/api/history?analysis_type=url")
    assert res_url.status_code == 200
    data_url = res_url.json()
    for item in data_url["items"]:
        assert item["analysis_type"] == "url"

    # Query file records
    res_file = client.get("/api/history?analysis_type=file")
    assert res_file.status_code == 200
    data_file = res_file.json()
    for item in data_file["items"]:
        assert item["analysis_type"] == "file"

def test_history_invalid_type_filter(client: TestClient):
    """Verifies 400 Bad Request for unrecognized analysis_type filter."""
    response = client.get("/api/history?analysis_type=unsupported_type")
    assert response.status_code == 400
    data = response.json()
    assert "Invalid analysis_type filter" in (data.get("error") or data.get("detail") or "")

def test_history_detail_not_found(client: TestClient):
    """Verifies 404 Not Found for nonexistent ID."""
    response = client.get("/api/history/99999999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in (data.get("error") or data.get("detail") or "").lower()

def test_delete_history_record(client: TestClient):
    """Verifies deleting a record by ID from PostgreSQL."""
    create_res = client.post("/api/analyze/url", json={"url": "https://www.wikipedia.org"})
    record_id = create_res.json()["id"]

    # Delete
    del_res = client.delete(f"/api/history/{record_id}")
    assert del_res.status_code == 200
    data = del_res.json()
    assert data["id"] == record_id
    assert "deleted successfully" in data["message"]

    # Verify subsequent GET returns 404
    verify_res = client.get(f"/api/history/{record_id}")
    assert verify_res.status_code == 404

def test_delete_history_not_found(client: TestClient):
    """Verifies 404 when deleting a nonexistent record."""
    response = client.delete("/api/history/99999999")
    assert response.status_code == 404

def test_database_connection_failure_handling():
    """Verifies graceful handling and reporting when database is unreachable."""
    bad_engine = create_engine(
        "postgresql+psycopg://postgres:invalid_pass@127.0.0.1:5439/nonexistent_db",
        connect_args={"connect_timeout": 1}
    )
    status = check_db_connection(target_engine=bad_engine)
    assert status["status"] == "disconnected"
    assert "error" in status


def test_history_stats_endpoint(client: TestClient):
    """Verifies aggregated metrics on GET /api/history/stats."""
    response = client.get("/api/history/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_analyses" in data
    assert "spam_count" in data
    assert "phishing_count" in data
    assert "safe_count" in data
    assert "threat_percentage" in data
    assert "threat_distribution" in data
    assert "type_distribution" in data
