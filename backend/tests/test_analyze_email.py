"""
backend/tests/test_analyze_email.py
Tests for POST /api/analyze/email endpoint.
"""

from fastapi.testclient import TestClient

def test_analyze_clean_email(client: TestClient, sample_clean_email):
    response = client.post("/api/analyze/email", json=sample_clean_email)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email_classification"] == "Ham"
    assert data["threat_level"] == "SAFE"
    assert data["verdict"] in ("SAFE", "Clean / Legitimate")
    assert data["overall_security_verdict"] == "SAFE"
    assert data["verdict_explanation"] is not None
    assert data["recommended_action"] == "ALLOW"
    assert data["risk_score"] < 40.0
    assert data["extracted_urls"] == []
    assert data["url_summary"]["total_urls_found"] == 0

def test_analyze_spam_email(client: TestClient, sample_spam_email):
    response = client.post("/api/analyze/email", json=sample_spam_email)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email_classification"] == "Spam"
    assert data["spam_probability"] > 0.5
    assert data["verdict"] in ("SUSPICIOUS", "Spam Email")
    assert data["overall_security_verdict"] == "SUSPICIOUS"
    assert data["verdict_explanation"] is not None
    assert data["recommended_action"] in ("MOVE_TO_JUNK", "WARN_USER")
    assert data["risk_score"] >= 45.0

def test_analyze_phishing_email(client: TestClient, sample_phishing_email):
    response = client.post("/api/analyze/email", json=sample_phishing_email)
    assert response.status_code == 200
    data = response.json()
    
    assert data["verdict"] in ("MALICIOUS", "Phishing Attack Detected")
    assert data["overall_security_verdict"] == "MALICIOUS"
    assert data["threat_level"] in ("CRITICAL", "HIGH")
    assert data["recommended_action"] == "QUARANTINE_AND_BLOCK"
    assert data["risk_score"] >= 80.0
    assert len(data["extracted_urls"]) >= 1
    assert data["url_summary"]["phishing_urls_count"] >= 1
    assert "http://secure-update-paypal-login.com/verify-account" in data["extracted_urls"]
    assert data["phishing_intent_analysis"] is not None

def test_analyze_email_body_alias(client: TestClient):
    payload = {
        "subject": "Weekly Team Update",
        "body": "Here are the updates for our project sprint."
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email_classification"] == "Ham"

def test_analyze_email_empty_payload(client: TestClient):
    payload = {"subject": "", "message": ""}
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data or "details" in data

def test_analyze_email_whitespace_payload(client: TestClient):
    payload = {"subject": "   ", "message": "   \n  "}
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 422
