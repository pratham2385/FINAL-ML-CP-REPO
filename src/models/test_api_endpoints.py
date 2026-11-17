"""
src/models/test_api_endpoints.py
Tests live FastAPI endpoints:
1. GET /api/health
2. POST /api/analyze/email (with 01_legitimate_meeting and 03_legitimate_password_notice content)
3. POST /api/analyze/email (with spam prize lure)
4. POST /api/analyze/file (.eml upload of 03_legitimate_password_notice.eml)
5. GET /api/history (verifying PostgreSQL persistence)
"""

import os
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_endpoints():
    print("=" * 70)
    print("TESTING FASTAPI BACKEND API ENDPOINTS")
    print("=" * 70)

    # 1. Health endpoint
    r = requests.get(f"{BASE_URL}/health")
    print(f"\n1. GET /api/health -> Status: {r.status_code}")
    print("   Response:", r.json())
    assert r.status_code == 200

    # 2. Analyze clean email (from 01_legitimate_meeting.eml)
    meeting_payload = {
        "subject": "Quick sync tomorrow",
        "message": "Hi team, Can we do a quick 15-minute sync tomorrow morning to review the slide deck? Let me know what time works best. Best, Alex"
    }
    r = requests.post(f"{BASE_URL}/analyze/email", json=meeting_payload)
    print(f"\n2a. POST /api/analyze/email (01 meeting) -> Status: {r.status_code}")
    email_res = r.json()
    print("   Verdict:", email_res.get("verdict"))
    print("   Classification:", email_res.get("email_classification"))
    print("   Spam Prob:", email_res.get("spam_probability"))
    print("   Confidence:", email_res.get("confidence_percent"))
    print("   Risk Score:", email_res.get("risk_score"))
    print("   DB ID:", email_res.get("id"))
    assert r.status_code == 200
    assert email_res["email_classification"] == "Ham"

    # 2b. Analyze clean password notice (from 03_legitimate_password_notice.eml)
    pw_payload = {
        "subject": "Password Updated Successfully",
        "message": "Hi, Your account password was changed successfully. If you made this change, no action is needed. If you did not, contact IT through the usual company channel. Regards, IT Support"
    }
    r = requests.post(f"{BASE_URL}/analyze/email", json=pw_payload)
    print(f"\n2b. POST /api/analyze/email (03 password notice) -> Status: {r.status_code}")
    pw_res = r.json()
    print("   Verdict:", pw_res.get("verdict"))
    print("   Classification:", pw_res.get("email_classification"))
    print("   Spam Prob:", pw_res.get("spam_probability"))
    print("   Confidence:", pw_res.get("confidence_percent"))
    print("   Risk Score:", pw_res.get("risk_score"))
    print("   DB ID:", pw_res.get("id"))
    assert r.status_code == 200
    assert pw_res["email_classification"] == "Ham"

    # 3. Analyze email (spam prize lure)
    spam_payload = {
        "subject": "CONGRATULATIONS! You won $1,000,000 cash prize!",
        "message": "Claim your guaranteed cash prize right now! Send your bank details to claim."
    }
    r = requests.post(f"{BASE_URL}/analyze/email", json=spam_payload)
    print(f"\n3. POST /api/analyze/email (spam lure) -> Status: {r.status_code}")
    spam_res = r.json()
    print("   Verdict:", spam_res.get("verdict"))
    print("   Classification:", spam_res.get("email_classification"))
    print("   Spam Prob:", spam_res.get("spam_probability"))
    print("   DB ID:", spam_res.get("id"))
    assert r.status_code == 200
    assert spam_res["email_classification"] == "Spam"

    # 4. Analyze .eml file upload
    eml_file_path = r"C:\Users\admin\Downloads\email_eml_test_samples\03_legitimate_password_notice.eml"
    with open(eml_file_path, "rb") as f:
        files = {"file": ("03_legitimate_password_notice.eml", f, "message/rfc822")}
        r = requests.post(f"{BASE_URL}/analyze/file", files=files)
    print(f"\n4. POST /api/analyze/file (03_legitimate_password_notice.eml) -> Status: {r.status_code}")
    file_res = r.json()
    print("   Filename:", file_res.get("filename"))
    print("   Verdict:", file_res.get("verdict"))
    print("   Classification:", file_res.get("email_classification"))
    print("   Spam Prob:", file_res.get("spam_probability"))
    print("   DB ID:", file_res.get("id"))
    assert r.status_code == 200
    assert file_res["email_classification"] == "Ham"

    # 5. Verify PostgreSQL History persistence
    r = requests.get(f"{BASE_URL}/history?limit=10")
    print(f"\n5. GET /api/history -> Status: {r.status_code}")
    hist = r.json()
    print(f"   Total History Items: {hist.get('total')}")
    items = hist.get("items", [])
    print(f"   Fetched {len(items)} items. Recent entries:")
    for it in items[:4]:
        print(f"     ID {it.get('id')}: type={it.get('analysis_type')}, verdict='{it.get('verdict')}', risk={it.get('overall_risk_score')}")

    print("\nALL API ENDPOINTS & POSTGRESQL PERSISTENCE VALIDATED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
