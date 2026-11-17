"""
backend/tests/conftest.py
Pytest fixtures for backend API integration and functional testing.
Uses an isolated test database (phishing_detection_test_db) to preserve production data.
"""

import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Ensure workspace root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
# Import all models to ensure metadata registration
import backend.app.db.models # noqa: F401
from backend.app.main import app

# Create isolated test engine using TEST_DATABASE_URL
test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=Session,
    expire_on_commit=False
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Sets up tables in the isolated test database."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    """Yields an isolated transaction for direct database assertions in tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def client():
    """Provides TestClient with get_db overridden to use test database."""
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_clean_email():
    return {
        "subject": "Quarterly Budget Review and Status Update",
        "message": "Hi team, please find attached the quarterly expenditure report for review before our Monday sync."
    }

@pytest.fixture
def sample_spam_email():
    return {
        "subject": "CONGRATULATIONS! You have won $1,000,000 in the Mega Lottery!",
        "message": "Dear lucky winner, claim your cash reward immediately! Send your full bank account numbers to release the wire transfer now!"
    }

@pytest.fixture
def sample_phishing_email():
    return {
        "subject": "URGENT: Unauthorized Security Access Detected On Your Account",
        "message": "Your account has been temporarily locked due to suspicious logins. Please verify your credentials immediately at http://secure-update-paypal-login.com/verify-account to prevent permanent termination."
    }

@pytest.fixture
def sample_legitimate_url():
    return "https://www.wikipedia.org"

@pytest.fixture
def sample_phishing_url():
    return "http://secure-update-paypal-login.com/verify-account"

@pytest.fixture
def sample_clean_eml_bytes():
    return (
        b"From: manager@company.com\r\n"
        b"To: employee@company.com\r\n"
        b"Subject: Team Sync Tomorrow\r\n"
        b"Date: Mon, 16 Nov 2026 09:00:00 +0000\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Hi everyone,\r\n"
        b"Just a reminder that our weekly standup will be at 10 AM tomorrow.\r\n"
    )

@pytest.fixture
def sample_phishing_eml_bytes():
    return (
        b"From: security-alert@bank-verification.com\r\n"
        b"To: victim@example.com\r\n"
        b"Subject: Critical: Update Your Password Immediately\r\n"
        b"Date: Mon, 16 Nov 2026 10:15:00 +0000\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b"<html><body>"
        b"<p>Your bank account is suspended.</p>"
        b"<p>Please click here: <a href=\"http://bank-account-security-alert.xyz/login\">Verify Identity</a></p>"
        b"</body></html>\r\n"
    )
