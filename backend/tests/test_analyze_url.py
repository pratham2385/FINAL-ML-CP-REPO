"""
backend/tests/test_analyze_url.py
Tests for POST /api/analyze/url endpoint.
"""

from fastapi.testclient import TestClient

def test_analyze_legitimate_url(client: TestClient, sample_legitimate_url):
    response = client.post("/api/analyze/url", json={"url": sample_legitimate_url})
    assert response.status_code == 200
    data = response.json()
    
    assert data["url"] == sample_legitimate_url
    assert data["classification"] == "Legitimate"
    assert data["is_phishing"] is False
    assert data["verdict"] == "Legitimate URL"
    assert data["recommended_action"] == "ALLOW"
    assert data["phishing_probability"] < 0.5
    assert len(data["features"]) == 18

def test_analyze_legitimate_deep_url(client: TestClient):
    deep_url = "https://github.com/torvalds/linux"
    response = client.post("/api/analyze/url", json={"url": deep_url})
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification"] == "Legitimate"
    assert data["is_phishing"] is False
    assert data["verdict"] == "Legitimate URL"

def test_analyze_phishing_url(client: TestClient, sample_phishing_url):
    response = client.post("/api/analyze/url", json={"url": sample_phishing_url})
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification"] == "Phishing"
    assert data["is_phishing"] is True
    assert data["verdict"] == "Phishing URL Detected"
    assert data["recommended_action"] == "BLOCK"
    assert data["phishing_probability"] >= 0.5
    assert data["risk_score"] >= 50.0

def test_analyze_url_empty(client: TestClient):
    response = client.post("/api/analyze/url", json={"url": ""})
    assert response.status_code == 422

def test_analyze_url_whitespace(client: TestClient):
    response = client.post("/api/analyze/url", json={"url": "    "})
    assert response.status_code == 422

def test_analyze_url_missing_field(client: TestClient):
    response = client.post("/api/analyze/url", json={})
    assert response.status_code == 422

def test_url_probability_calibration_and_separation(client: TestClient):
    """
    Regression test verifying that:
    1. Probabilities are mathematical and not hardcoded to 0.05 or 1.0.
    2. ML confidence, phishing probability, legitimate probability, risk score, and verdict are distinct.
    3. p_phish + p_legit == 1.0.
    4. confidence == max(p_phish, p_legit) * 100.
    """
    # Test on a legitimate deep URL
    resp_legit = client.post("/api/analyze/url", json={"url": "https://github.com/torvalds/linux"})
    assert resp_legit.status_code == 200
    d_legit = resp_legit.json()

    # Must NOT be hardcoded to 0.05 / 95%
    assert d_legit["phishing_probability"] != 0.05, "Phishing probability should not be hardcoded to 0.05"
    assert d_legit["confidence_percent"] != 95.0, "Confidence should not be pinned to 95.0%"
    assert d_legit["phishing_probability"] < 0.01
    assert d_legit["confidence_percent"] > 99.0
    assert abs(d_legit["phishing_probability"] + d_legit["legitimate_probability"] - 1.0) < 1e-3
    assert abs(d_legit["confidence_percent"] - d_legit["legitimate_probability"] * 100) < 0.1
    assert d_legit["verdict"] == "Legitimate URL"
    assert d_legit["recommended_action"] == "ALLOW"

    # Test on a phishing URL with sub-100% tree consensus
    resp_phish = client.post("/api/analyze/url", json={"url": "http://netflix-billing-update-account.com"})
    assert resp_phish.status_code == 200
    d_phish = resp_phish.json()

    assert d_phish["classification"] == "Phishing"
    assert d_phish["is_phishing"] is True
    # Must NOT be forced to 100% confidence
    assert d_phish["confidence_percent"] < 100.0, "Confidence should reflect true tree variance and not be forced to 100%"
    assert abs(d_phish["phishing_probability"] + d_phish["legitimate_probability"] - 1.0) < 1e-3
    assert abs(d_phish["confidence_percent"] - d_phish["phishing_probability"] * 100) < 0.1
    assert d_phish["verdict"] == "Phishing URL Detected"
    assert d_phish["recommended_action"] == "BLOCK"

def test_ten_legitimate_benchmark_urls(client: TestClient):
    """
    Validates 10 legitimate benchmark URLs including deep paths and subdomains.
    Ensures natural model probability distribution.
    """
    legit_urls = [
        "https://google.com",
        "https://www.wikipedia.org",
        "https://github.com",
        "https://github.com/torvalds/linux",
        "https://en.wikipedia.org/wiki/Phishing",
        "https://docs.python.org/3/library/urllib.parse.html",
        "https://www.amazon.com/dp/B08N5WRWNW",
        "https://support.google.com/mail/answer/8253",
        "https://stackoverflow.com/questions/12345/how-to-fix",
        "https://www.kaggle.com/datasets"
    ]

    confidences = []
    for u in legit_urls:
        res = client.post("/api/analyze/url", json={"url": u})
        assert res.status_code == 200
        data = res.json()
        assert data["classification"] == "Legitimate", f"Expected Legitimate for {u}, got {data['classification']}"
        assert data["is_phishing"] is False
        assert data["verdict"] == "Legitimate URL"
        assert data["recommended_action"] == "ALLOW"
        assert data["phishing_probability"] < 0.05
        assert data["confidence_percent"] > 95.0
        confidences.append(data["confidence_percent"])

    # Ensure confidences have actual natural variance
    assert len(set(confidences)) > 1, "Legitimate URLs should not all share an identical confidence score"

def test_ten_phishing_benchmark_urls(client: TestClient):
    """
    Validates 10 phishing benchmark URLs including credential harvesters, IP targets, and lures.
    Ensures natural model probability distribution.
    """
    phish_urls = [
        "http://secure-login-paypal.com",
        "http://apple-id-verify.com.au.account-login.net",
        "http://192.168.1.1/login",
        "http://paypal-verification-account.com/webscr/login.php?cmd=_login-run",
        "http://bankofamerica.update-billing.org",
        "http://dropbox-share-files.com/download/invoice.exe",
        "http://secure.chase.com.account-update.xyz/auth/signin.html",
        "http://login.microsoftonline.com.suspicious-domain.tk",
        "http://netflix-billing-update-account.com",
        "http://wellsfargo-verify-security.info/login.php"
    ]

    confidences = []
    for u in phish_urls:
        res = client.post("/api/analyze/url", json={"url": u})
        assert res.status_code == 200
        data = res.json()
        assert data["classification"] == "Phishing", f"Expected Phishing for {u}, got {data['classification']}"
        assert data["is_phishing"] is True
        assert data["verdict"] == "Phishing URL Detected"
        assert data["recommended_action"] == "BLOCK"
        assert data["phishing_probability"] >= 0.50
        assert data["risk_score"] >= 85.0
        confidences.append(data["confidence_percent"])

    # Ensure confidences are not all 100%
    assert any(c < 100.0 for c in confidences), "Phishing URLs should not all be artificially forced to 100% confidence"
