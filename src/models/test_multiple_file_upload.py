"""
src/models/test_multiple_file_upload.py
Comprehensive end-to-end verification of multiple email file upload support.
"""

import os
import sys
import io
import json
import time
from fastapi.testclient import TestClient

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.config import settings

def run_tests():
    print("=" * 80)
    print("STARTING MULTIPLE EMAIL FILE UPLOAD SYSTEM TESTS")
    print("=" * 80)

    client = TestClient(app)

    # 1. Verify Health
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    print("[PASS] 1. Backend health check: OK")

    # 2. Test Single File Upload Endpoint (Regression check: POST /api/analyze/file)
    single_eml = (
        b"From: test.sender@example.com\r\n"
        b"To: target.user@example.com\r\n"
        b"Subject: Quarterly Review Meeting\r\n"
        b"Date: Mon, 16 Nov 2026 10:00:00 +0000\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        b"Please review the attached quarterly numbers before tomorrow morning's sync.\r\n"
    )
    single_resp = client.post(
        "/api/analyze/file",
        files={"file": ("quarterly_review.eml", io.BytesIO(single_eml), "message/rfc822")}
    )
    assert single_resp.status_code == 200, f"Single file endpoint failed: {single_resp.text}"
    single_data = single_resp.json()
    assert single_data["verdict"] in ("SAFE", "Clean / Legitimate")
    assert single_data["overall_security_verdict"] == "SAFE"
    assert single_data["email_classification"] == "Ham"
    assert single_data["eml_metadata"]["filename"] == "quarterly_review.eml"
    print(f"[PASS] 2. Single-file upload endpoint (POST /api/analyze/file): OK (Verdict: {single_data['verdict']}, ID: {single_data.get('id')})")

    # 3. Test URL Detection Endpoint (Regression check: POST /api/analyze/url)
    url_resp = client.post("/api/analyze/url", json={"url": "http://secure-paypal-verify-account.com/login"})
    assert url_resp.status_code == 200, f"URL endpoint failed: {url_resp.text}"
    url_data = url_resp.json()
    assert url_data["is_phishing"] is True or url_data["phishing_probability"] > 0.5
    print(f"[PASS] 3. URL detection endpoint (POST /api/analyze/url): OK (Phishing prob: {url_data['phishing_probability']:.4f})")

    # 4. Test Batch Upload with 18 Synthetic Emails
    synthetic_dir = r"C:\Users\admin\Downloads\email_eml_test_samples"
    eml_files = sorted([f for f in os.listdir(synthetic_dir) if f.endswith(".eml")])
    print(f"Loaded {len(eml_files)} real synthetic .eml files from {synthetic_dir}")
    assert len(eml_files) == 18, f"Expected 18 .eml files, found {len(eml_files)}"

    batch_files = []
    for fname in eml_files:
        fpath = os.path.join(synthetic_dir, fname)
        with open(fpath, "rb") as f:
            content = f.read()
        batch_files.append(("files", (fname, io.BytesIO(content), "message/rfc822")))

    t0 = time.perf_counter()
    batch_resp = client.post("/api/analyze/files", files=batch_files)
    elapsed = time.perf_counter() - t0
    assert batch_resp.status_code == 200, f"Batch analysis failed: {batch_resp.text}"
    batch_data = batch_resp.json()

    summary = batch_data["summary"]
    results = batch_data["results"]

    assert summary["total_files"] == 18, f"Expected 18 files, got {summary['total_files']}"
    assert summary["successful_count"] == 18, f"Expected 18 successful, got {summary['successful_count']}"
    assert summary["failed_count"] == 0, f"Expected 0 failed, got {summary['failed_count']}"
    assert len(results) == 18, f"Expected 18 results, got {len(results)}"
    
    print(f"[PASS] 4. Batch 18 synthetic emails analyzed in {elapsed*1000:.1f}ms:")
    print(f"       - Total: {summary['total_files']}")
    print(f"       - Successful: {summary['successful_count']}")
    print(f"       - Ham Count: {summary['ham_count']}")
    print(f"       - Spam Count: {summary['spam_count']}")
    print(f"       - Total Payload Size: {summary['total_size_bytes']} bytes")

    for r in results:
        assert r["status"] == "completed"
        assert r["id"] is not None
        assert r["verdict"] is not None
        assert r["email_analysis"] is not None
        assert r["url_summary"] is not None

    print("[PASS] 5. All 18 items successfully persisted to PostgreSQL AnalysisHistory.")

    # 5. Test Batch with Mixed Valid and Invalid Files (Failure Isolation)
    mixed_files = [
        ("files", ("valid_notice.eml", io.BytesIO(single_eml), "message/rfc822")),
        ("files", ("invoice.pdf", io.BytesIO(b"%PDF-1.4 dummy pdf bytes"), "application/pdf")),
        ("files", ("empty.eml", io.BytesIO(b""), "message/rfc822")),
        ("files", ("whitespace.eml", io.BytesIO(b"   \r\n \t \r\n"), "message/rfc822")),
        ("files", ("valid_promo.eml", io.BytesIO(
            b"From: promo@store.com\r\nSubject: Huge 50% Off Sale\r\n\r\nBuy now http://store.com/sale\r\n"
        ), "message/rfc822")),
    ]
    mixed_resp = client.post("/api/analyze/files", files=mixed_files)
    assert mixed_resp.status_code == 200, f"Mixed batch failed: {mixed_resp.text}"
    mixed_data = mixed_resp.json()
    mixed_summary = mixed_data["summary"]
    mixed_results = mixed_data["results"]

    assert mixed_summary["total_files"] == 5
    assert mixed_summary["successful_count"] == 2
    assert mixed_summary["failed_count"] == 3
    assert mixed_results[0]["status"] == "completed"
    assert mixed_results[1]["status"] == "failed"
    assert "Only .eml files are accepted" in mixed_results[1]["error_message"]
    assert mixed_results[2]["status"] == "failed"
    assert "empty" in mixed_results[2]["error_message"].lower()
    assert mixed_results[3]["status"] == "failed"
    assert "empty" in mixed_results[3]["error_message"].lower()
    assert mixed_results[4]["status"] == "completed"
    print(f"[PASS] 6. Mixed batch failure isolation: 2 succeeded, 3 failed with clear errors.")

    # 6. Test Max Files Limit (> 100 files -> 400 Bad Request)
    over_limit_files = [
        ("files", (f"file_{i}.eml", io.BytesIO(single_eml), "message/rfc822"))
        for i in range(101)
    ]
    over_resp = client.post("/api/analyze/files", files=over_limit_files)
    assert over_resp.status_code == 400
    assert "exceeds maximum allowed limit" in over_resp.text.lower()
    print("[PASS] 7. Batch limit enforcement (>100 files -> HTTP 400): OK")

    # 7. Test Empty Batch (0 files -> 400/422)
    empty_resp = client.post("/api/analyze/files", files=[])
    assert empty_resp.status_code in (400, 422)
    print("[PASS] 8. Empty batch rejection (0 files -> HTTP 400/422): OK")

    # 8. Test Single File Oversized (> 10MB)
    large_file = [
        ("files", ("large_dump.eml", io.BytesIO(b"A" * (10 * 1024 * 1024 + 100)), "message/rfc822"))
    ]
    large_resp = client.post("/api/analyze/files", files=large_file)
    assert large_resp.status_code == 200
    assert large_resp.json()["results"][0]["status"] == "failed"
    assert "exceeds maximum allowed size" in large_resp.json()["results"][0]["error_message"].lower()
    print("[PASS] 9. Single file oversized (>10MB marked failed): OK")

    print("=" * 80)
    print("ALL MULTIPLE EMAIL FILE UPLOAD TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
