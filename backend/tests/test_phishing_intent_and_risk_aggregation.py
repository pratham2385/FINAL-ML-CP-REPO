"""
backend/tests/test_phishing_intent_and_risk_aggregation.py
Dedicated test suite verifying the phishing intent detection layer and
the centralized security risk aggregation rules.
"""

from fastapi.testclient import TestClient


def test_phishing_url_with_ham_text_is_malicious(client: TestClient):
    """
    Requirement: A confirmed phishing URL must NEVER result in an overall SAFE verdict.
    Even when the email text is polite/clean and classified as HAM.
    """
    payload = {
        "subject": "Quick question regarding tomorrow's meeting agenda",
        "message": (
            "Hi team, please find the discussion notes for tomorrow at "
            "http://secure-update-paypal-login.com/verify-account. "
            "Looking forward to speaking with everyone."
        ),
        "sender": "colleague@company.com"
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Email text is polite / Ham
    assert data["email_classification"] == "Ham"
    # But URL is phishing
    assert data["url_summary"]["phishing_urls_count"] >= 1
    # Overall security verdict MUST be MALICIOUS
    assert data["overall_security_verdict"] == "MALICIOUS"
    assert data["verdict"] == "MALICIOUS"
    assert data["threat_level"] in ("CRITICAL", "HIGH")
    assert data["risk_score"] >= 85.0
    assert data["recommended_action"] == "QUARANTINE_AND_BLOCK"
    assert "phishing" in data["verdict_explanation"].lower()


def test_spam_with_legitimate_urls_is_not_malicious(client: TestClient):
    """
    Requirement: A SPAM email with legitimate URLs must NOT automatically be considered malicious.
    It should result in SUSPICIOUS / MOVE_TO_JUNK.
    """
    payload = {
        "subject": "EXCLUSIVE DISCOUNT 70% OFF WATCHES AND JEWELRY TODAY ONLY",
        "message": (
            "Massive warehouse clearance sale! Buy luxury watches now at huge discount prices! "
            "Hurry, limited stock remaining! Visit our store at https://google.com to view catalog. "
            "To unsubscribe, visit https://github.com"
        ),
        "sender": "promotions@blast-marketing.biz"
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["email_classification"] == "Spam"
    assert data["url_summary"]["phishing_urls_count"] == 0
    assert data["url_summary"]["total_urls_found"] >= 1

    # Overall verdict must be SUSPICIOUS, NOT MALICIOUS!
    assert data["overall_security_verdict"] == "SUSPICIOUS"
    assert data["verdict"] == "SUSPICIOUS"
    assert data["recommended_action"] in ("MOVE_TO_JUNK", "WARN_USER")
    assert data["risk_score"] < 80.0
    assert "spam" in data["verdict_explanation"].lower()


def test_linkless_bec_gift_card_fraud(client: TestClient):
    """
    Requirement: Emails without URLs must still undergo phishing-intent analysis.
    BEC gift card purchase scam from purported CEO.
    """
    payload = {
        "subject": "Urgent request from the CEO - keep confidential",
        "message": (
            "Are you at your desk right now? I am currently in a board meeting and cannot take calls. "
            "I need you to handle a quick favor for me discreetly. Please purchase 5 Apple gift cards "
            "of $100 each for a client presentation. Scratch the back and send me photos of the codes "
            "as soon as possible. Keep this confidential between us."
        ),
        "sender": "CEO John Smith <john.smith.ceo.board@gmail.com>"
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()

    # No URLs present in email
    assert data["extracted_urls"] == []
    assert data["url_summary"]["total_urls_found"] == 0

    # Phishing Intent Layer must detect BEC
    intent = data.get("phishing_intent_analysis")
    assert intent is not None
    assert intent["has_phishing_intent"] is True
    assert intent["primary_intent"] == "BUSINESS_EMAIL_COMPROMISE"
    assert intent["intent_risk_level"] == "HIGH"
    assert len(intent["evidence"]) >= 1

    # Overall security verdict MUST be MALICIOUS
    assert data["overall_security_verdict"] == "MALICIOUS"
    assert data["verdict"] == "MALICIOUS"
    assert data["recommended_action"] == "QUARANTINE_AND_BLOCK"
    assert data["risk_score"] >= 80.0
    assert "business email compromise" in data["verdict_explanation"].lower() or "bec" in data["verdict_explanation"].lower() or "intent" in data["verdict_explanation"].lower()


def test_credential_theft_intent(client: TestClient):
    """
    Requirement: Detects credential theft with account lockout threats.
    """
    payload = {
        "subject": "CRITICAL: Your Microsoft 365 Password Has Expired",
        "message": (
            "Your domain account password has expired. Immediate action is required. "
            "To prevent immediate suspension of all mailbox services, please click here to verify your credentials "
            "and confirm your username and password: http://mail-login-portal-verification.net/auth"
        ),
        "sender": "IT Helpdesk <support@it-services-domain.com>"
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()

    intent = data.get("phishing_intent_analysis")
    assert intent is not None
    assert intent["has_phishing_intent"] is True
    assert intent["primary_intent"] in ("CREDENTIAL_THEFT", "SOCIAL_ENGINEERING_IMPERSONATION")
    assert data["overall_security_verdict"] == "MALICIOUS"
    assert data["verdict"] == "MALICIOUS"


def test_legitimate_payroll_invoice_is_safe(client: TestClient):
    """
    Requirement: Avoid false positives on legitimate payroll emails, invoices, and business correspondence.
    """
    payload = {
        "subject": "Invoice #INV-2026-104 for Consulting Services - October 2026",
        "message": (
            "Hi Finance Team,\n\n"
            "Please find attached invoice #INV-2026-104 detailing the engineering consulting services "
            "completed during October 2026. Payment terms are Net 30 as agreed in our service contract. "
            "Thank you for your partnership."
        ),
        "sender": "accounting@verified-partner.com"
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["email_classification"] == "Ham"
    assert data["overall_security_verdict"] == "SAFE"
    assert data["verdict"] == "SAFE"
    assert data["threat_level"] == "SAFE"
    assert data["risk_score"] < 25.0
    assert data["recommended_action"] == "ALLOW"


def test_legitimate_password_changed_notification_is_safe(client: TestClient):
    """
    Requirement: Benign password notification ('if this was you, no action needed') should be SAFE.
    """
    payload = {
        "subject": "Security notice: Your password was updated",
        "message": (
            "This is an automated notification to let you know that your password was successfully changed. "
            "If you recently made this change, no action is required. "
            "If you did not request this, please visit your account settings."
        ),
        "sender": "notifications@account.google.com"
    }
    response = client.post("/api/analyze/email", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_security_verdict"] == "SAFE"
    assert data["verdict"] == "SAFE"
    assert data["threat_level"] == "SAFE"
    assert data["recommended_action"] == "ALLOW"
