"""
backend/tests/test_analyze_file.py
Tests for POST /api/analyze/file endpoint (.eml upload).
"""

import io
from fastapi.testclient import TestClient

def test_analyze_clean_eml_file(client: TestClient, sample_clean_eml_bytes):
    file_payload = {
        "file": ("meeting_memo.eml", io.BytesIO(sample_clean_eml_bytes), "message/rfc822")
    }
    response = client.post("/api/analyze/file", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "eml_metadata" in data
    assert data["eml_metadata"]["filename"] == "meeting_memo.eml"
    assert data["eml_metadata"]["sender"] == "manager@company.com"
    assert data["eml_metadata"]["subject"] == "Team Sync Tomorrow"
    assert data["email_classification"] == "Ham"
    assert data["threat_level"] == "SAFE"
    assert data["verdict"] in ("SAFE", "Clean / Legitimate")
    assert data["overall_security_verdict"] == "SAFE"
    assert data["verdict_explanation"] is not None

def test_analyze_phishing_eml_file(client: TestClient, sample_phishing_eml_bytes):
    file_payload = {
        "file": ("urgent_security_alert.eml", io.BytesIO(sample_phishing_eml_bytes), "message/rfc822")
    }
    response = client.post("/api/analyze/file", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["eml_metadata"]["subject"] == "Critical: Update Your Password Immediately"
    assert "http://bank-account-security-alert.xyz/login" in data["extracted_urls"]
    assert data["url_summary"]["phishing_urls_count"] >= 1
    assert data["verdict"] in ("MALICIOUS", "Phishing Attack Detected")
    assert data["overall_security_verdict"] == "MALICIOUS"
    assert data["threat_level"] in ("CRITICAL", "HIGH")
    assert data["recommended_action"] == "QUARANTINE_AND_BLOCK"

def test_analyze_file_invalid_extension(client: TestClient):
    file_payload = {
        "file": ("malicious_script.pdf", io.BytesIO(b"dummy pdf bytes"), "application/pdf")
    }
    response = client.post("/api/analyze/file", files=file_payload)
    assert response.status_code == 400
    data = response.json()
    assert "Only .eml files are accepted" in data.get("error", "") or "Only .eml files are accepted" in data.get("details", "")

def test_analyze_file_empty(client: TestClient):
    file_payload = {
        "file": ("empty.eml", io.BytesIO(b""), "message/rfc822")
    }
    response = client.post("/api/analyze/file", files=file_payload)
    assert response.status_code == 400
    data = response.json()
    assert "empty" in (data.get("error") or data.get("details") or "").lower()


# ============================================================================
# BATCH FILE ANALYSIS TESTS: POST /api/analyze/files
# ============================================================================

def test_analyze_files_batch_success(client: TestClient, sample_clean_eml_bytes, sample_phishing_eml_bytes):
    """Test successful batch upload of multiple valid .eml files (mixed ham & spam)."""
    files = [
        ("files", ("clean_mail.eml", io.BytesIO(sample_clean_eml_bytes), "message/rfc822")),
        ("files", ("phish_mail.eml", io.BytesIO(sample_phishing_eml_bytes), "message/rfc822")),
    ]
    response = client.post("/api/analyze/files", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert "results" in data

    summary = data["summary"]
    assert summary["total_files"] == 2
    assert summary["successful_count"] == 2
    assert summary["failed_count"] == 0
    assert summary["ham_count"] == 1
    assert summary["spam_count"] == 1
    assert summary["total_size_bytes"] > 0
    assert summary["total_processing_time_ms"] >= 0

    results = data["results"]
    assert len(results) == 2

    # Verify first file (Ham)
    res0 = results[0]
    assert res0["filename"] == "clean_mail.eml"
    assert res0["status"] == "completed"
    assert res0["email_classification"] == "Ham"
    assert res0["threat_level"] == "SAFE"
    assert res0["id"] is not None

    # Verify second file (Spam)
    res1 = results[1]
    assert res1["filename"] == "phish_mail.eml"
    assert res1["status"] == "completed"
    assert res1["email_classification"] == "Spam"
    assert res1["threat_level"] == "CRITICAL"
    assert res1["id"] is not None


def test_analyze_files_batch_empty_list(client: TestClient):
    """Test batch upload with no files returns 400 Bad Request."""
    response = client.post("/api/analyze/files", files=[])
    # FastApi returns 400 or 422 if field is missing / empty
    assert response.status_code in (400, 422)


def test_analyze_files_batch_exceeds_max_files(client: TestClient, sample_clean_eml_bytes):
    """Test batch upload exceeding MAX_FILES_PER_BATCH (100) returns 400."""
    files = [
        ("files", (f"mail_{i}.eml", io.BytesIO(sample_clean_eml_bytes), "message/rfc822"))
        for i in range(101)
    ]
    response = client.post("/api/analyze/files", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "exceeds maximum allowed limit" in (data.get("error") or data.get("details") or "").lower()


def test_analyze_files_batch_mixed_valid_and_invalid(client: TestClient, sample_clean_eml_bytes):
    """Test batch with mixed valid and invalid files processes valid files and reports per-file errors."""
    files = [
        ("files", ("good.eml", io.BytesIO(sample_clean_eml_bytes), "message/rfc822")),
        ("files", ("bad_extension.txt", io.BytesIO(b"Hello world text file"), "text/plain")),
        ("files", ("empty_mail.eml", io.BytesIO(b""), "message/rfc822")),
        ("files", ("whitespace_mail.eml", io.BytesIO(b"   \r\n   \t  \r\n"), "message/rfc822")),
    ]
    response = client.post("/api/analyze/files", files=files)
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert summary["total_files"] == 4
    assert summary["successful_count"] == 1
    assert summary["failed_count"] == 3

    results = data["results"]
    assert len(results) == 4

    # File 0: good.eml
    assert results[0]["filename"] == "good.eml"
    assert results[0]["status"] == "completed"

    # File 1: bad_extension.txt
    assert results[1]["filename"] == "bad_extension.txt"
    assert results[1]["status"] == "failed"
    assert "Only .eml files are accepted" in results[1]["error_message"]

    # File 2: empty_mail.eml
    assert results[2]["filename"] == "empty_mail.eml"
    assert results[2]["status"] == "failed"
    assert "empty" in results[2]["error_message"].lower()

    # File 3: whitespace_mail.eml
    assert results[3]["filename"] == "whitespace_mail.eml"
    assert results[3]["status"] == "failed"
    assert "empty" in results[3]["error_message"].lower()


def test_analyze_files_batch_single_file_exceeds_limit(client: TestClient):
    """Test batch item exceeding 10MB limit is flagged as failed without breaking others."""
    # Create an oversized payload of 10.5 MB for one file
    oversized_bytes = b"X" * (10 * 1024 * 1024 + 512 * 1024)
    files = [
        ("files", ("oversized.eml", io.BytesIO(oversized_bytes), "message/rfc822")),
    ]
    response = client.post("/api/analyze/files", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_files"] == 1
    assert data["summary"]["successful_count"] == 0
    assert data["summary"]["failed_count"] == 1
    assert "exceeds maximum allowed size" in data["results"][0]["error_message"].lower()
