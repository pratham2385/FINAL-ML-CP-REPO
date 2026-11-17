import os
import sys
import time
import json
import requests

API_BASE = "http://127.0.0.1:8000/api"
SYNTHETIC_DIR = r"C:\Users\admin\Downloads\email_eml_test_samples"
OUTPUT_REPORT = os.path.join("outputs", "reports", "final_system_test_results.json")

def run_tests():
    print("=" * 75)
    print("PHASE 8: FINAL SYSTEM VALIDATION & FUNCTIONAL TESTING")
    print("=" * 75)

    results = {}
    all_passed = True

    # 1. Health Endpoint
    print("\n--- [Test 1] Health Endpoint (GET /api/health) ---")
    r = requests.get(f"{API_BASE}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health_data = r.json()
    print(f"  Status: {health_data.get('status')} | Pipeline: {health_data.get('ml_pipeline', {}).get('status')} | DB: {health_data.get('database', {}).get('status')}")
    results["health_check"] = {
        "status_code": r.status_code,
        "payload": health_data,
        "passed": health_data.get("status") == "healthy" and health_data.get("ml_pipeline", {}).get("email_model_loaded") is True
    }

    # 2. Plain-Text Email Analysis
    print("\n--- [Test 2] Plain-Text Email Analysis (POST /api/analyze/email) ---")
    payload = {
        "subject": "Sprint Planning Agenda",
        "message": "Hi everyone, please review the backlog items for our sprint planning on Thursday morning at 10 AM. See you there."
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"  Verdict: {data['verdict']} | Threat: {data['threat_level']} | Risk: {data['risk_score']} | Spam Prob: {data['email_analysis']['spam_probability']}")
    t2_passed = (data["verdict"] == "Clean / Legitimate" and data["threat_level"] == "SAFE" and data["email_analysis"]["is_spam"] is False)
    results["plain_text_email"] = {"status_code": r.status_code, "response": data, "passed": t2_passed}
    all_passed = all_passed and t2_passed

    # 3. HTML Email Analysis
    print("\n--- [Test 3] HTML Email Analysis (POST /api/analyze/email) ---")
    payload = {
        "subject": "System Maintenance Notice",
        "message": "<html><body><h2>Scheduled Maintenance</h2><p>Our database servers will undergo routine upgrades on Saturday from 2 AM to 4 AM UTC.</p><table border='1'><tr><td>Service</td><td>Impact</td></tr><tr><td>API</td><td>Read-only</td></tr></table></body></html>"
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"  Verdict: {data['verdict']} | Threat: {data['threat_level']} | Risk: {data['risk_score']} | Spam Prob: {data['email_analysis']['spam_probability']}")
    t3_passed = (data["verdict"] == "Clean / Legitimate" and data["threat_level"] == "SAFE")
    results["html_email"] = {"status_code": r.status_code, "response": data, "passed": t3_passed}
    all_passed = all_passed and t3_passed

    # 4. Legitimate Commercial Newsletter Test
    print("\n--- [Test 4] Legitimate Commercial Newsletter with CSS & Footer (POST /api/analyze/email) ---")
    payload = {
        "subject": "O'Reilly Programming Newsletter - Weekly Edition",
        "message": """
        <html>
        <head>
          <style>body { font-family: Helvetica, Arial; color: #333333; background: #ffffff; }</style>
          <script>var x = 100;</script>
        </head>
        <body>
          <h1>O'Reilly Programming</h1>
          <p>Here are the latest architectural deep dives &nbsp; in distributed systems, Rust memory safety, and cloud scalability.</p>
          <hr/>
          <p style="font-size: 11px;">You are receiving this email because you subscribed to O'Reilly newsletters. To unsubscribe click here or manage your subscription preferences. All rights reserved copyright 2026.</p>
        </body>
        </html>
        """
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"  Verdict: {data['verdict']} | Threat: {data['threat_level']} | Risk: {data['risk_score']} | Spam Prob: {data['email_analysis']['spam_probability']}")
    t4_passed = (data["verdict"] == "Clean / Legitimate" and data["email_analysis"]["is_spam"] is False)
    results["legitimate_newsletter"] = {"status_code": r.status_code, "response": data, "passed": t4_passed}
    all_passed = all_passed and t4_passed

    # 5. Spam Email Analysis
    print("\n--- [Test 5] Spam Email Analysis (POST /api/analyze/email) ---")
    payload = {
        "subject": "CONGRATULATIONS! You have won $2,500,000 USD in the International Lottery",
        "message": "Dear Winner, Your email address was selected in our computer balloting draw. To claim your prize funds, submit your full banking credentials and passport copy immediately."
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"  Verdict: {data['verdict']} | Threat: {data['threat_level']} | Risk: {data['risk_score']} | Spam Prob: {data['email_analysis']['spam_probability']}")
    t5_passed = (data["verdict"] == "Spam Email" and data["email_analysis"]["is_spam"] is True and data["risk_score"] >= 80.0)
    results["spam_email"] = {"status_code": r.status_code, "response": data, "passed": t5_passed}
    all_passed = all_passed and t5_passed

    # 6. Phishing Email with Malicious Link
    print("\n--- [Test 6] Phishing Email Analysis (POST /api/analyze/email) ---")
    payload = {
        "subject": "URGENT: Suspicious activity on your account - Verify within 24 hours",
        "message": "We detected unauthorized attempts to access your account. Please confirm your credentials immediately to avoid permanent deactivation: http://paypal-verification-account-update.com/login"
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    print(f"  Verdict: {data['verdict']} | Threat: {data['threat_level']} | Risk: {data['risk_score']} | Action: {data['recommended_action']}")
    t6_passed = (data["verdict"] == "Phishing Attack Detected" and data["threat_level"] == "CRITICAL" and data["recommended_action"] == "QUARANTINE_AND_BLOCK")
    results["phishing_email"] = {"status_code": r.status_code, "response": data, "passed": t6_passed}
    all_passed = all_passed and t6_passed

    # 7. Email Containing Multiple URLs (Legitimate + Phishing)
    print("\n--- [Test 7] Email Containing Multiple URLs (POST /api/analyze/email) ---")
    payload = {
        "subject": "Security Advisory and Verification",
        "message": "Refer to official documentation at https://google.com or https://github.com. However, verify your credentials here: http://paypal-verification-account-update.com/login"
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    url_sum = data["url_summary"]
    print(f"  Total URLs: {url_sum['total_urls_found']} | Phishing URLs: {url_sum['phishing_urls_count']} | Verdict: {data['verdict']}")
    t7_passed = (url_sum["total_urls_found"] == 3 and url_sum["phishing_urls_count"] == 1 and data["verdict"] == "Phishing Attack Detected")
    results["multiple_urls_email"] = {"status_code": r.status_code, "response": data, "passed": t7_passed}
    all_passed = all_passed and t7_passed

    # 8. URL-Only Analysis
    print("\n--- [Test 8] URL-Only Analysis (POST /api/analyze/url) ---")
    r_legit = requests.post(f"{API_BASE}/analyze/url", json={"url": "https://microsoft.com"})
    r_phish = requests.post(f"{API_BASE}/analyze/url", json={"url": "http://paypal-verification-account-update.com/login"})
    data_legit = r_legit.json()
    data_phish = r_phish.json()
    print(f"  Legitimate URL: {data_legit['verdict']} | Risk: {data_legit['risk_score']} | Phish Prob: {data_legit['phishing_probability']}")
    print(f"  Phishing URL:   {data_phish['verdict']} | Risk: {data_phish['risk_score']} | Phish Prob: {data_phish['phishing_probability']}")
    t8_passed = (data_legit["is_phishing"] is False and data_phish["is_phishing"] is True)
    results["url_only_analysis"] = {"legitimate": data_legit, "phishing": data_phish, "passed": t8_passed}
    all_passed = all_passed and t8_passed

    # 9. Empty and Malformed Inputs
    print("\n--- [Test 9] Malformed and Boundary Inputs ---")
    # A. Empty JSON
    r_empty = requests.post(f"{API_BASE}/analyze/email", json={})
    print(f"  Empty email JSON status: {r_empty.status_code}")
    # B. Whitespace email
    r_ws = requests.post(f"{API_BASE}/analyze/email", json={"subject": "   ", "message": "   "})
    print(f"  Whitespace email status: {r_ws.status_code}")
    # C. Missing URL field
    r_bad_url = requests.post(f"{API_BASE}/analyze/url", json={})
    print(f"  Missing URL field status: {r_bad_url.status_code}")
    # D. Invalid file format upload (.txt)
    r_bad_file = requests.post(f"{API_BASE}/analyze/file", files={"file": ("test.txt", b"plain text", "text/plain")})
    print(f"  Non-eml file upload status: {r_bad_file.status_code}")
    # E. 0-byte file upload (.eml)
    r_zero_file = requests.post(f"{API_BASE}/analyze/file", files={"file": ("empty.eml", b"", "message/rfc822")})
    print(f"  0-byte file upload status: {r_zero_file.status_code}")

    t9_passed = (r_empty.status_code in [400, 422] and r_ws.status_code in [400, 422] and r_bad_url.status_code == 422 and r_bad_file.status_code == 400 and r_zero_file.status_code == 400)
    results["malformed_inputs"] = {
        "empty_email_status": r_empty.status_code,
        "whitespace_email_status": r_ws.status_code,
        "missing_url_status": r_bad_url.status_code,
        "invalid_ext_status": r_bad_file.status_code,
        "empty_file_status": r_zero_file.status_code,
        "passed": t9_passed
    }
    all_passed = all_passed and t9_passed

    # 10. .eml File Upload Analysis
    print("\n--- [Test 10] .eml File Upload Analysis (POST /api/analyze/file) ---")
    eml_file = os.path.join(SYNTHETIC_DIR, "04_legitimate_newsletter.eml")
    with open(eml_file, "rb") as f:
        r_eml = requests.post(f"{API_BASE}/analyze/file", files={"file": ("04_legitimate_newsletter.eml", f, "message/rfc822")})
    assert r_eml.status_code == 200
    data_eml = r_eml.json()
    print(f"  .eml Upload -> Verdict: {data_eml['verdict']} | Threat: {data_eml['threat_level']} | Risk: {data_eml['overall_risk_score']} | From: {data_eml['eml_metadata']['sender']}")
    t10_passed = (data_eml["email_analysis"]["is_spam"] is False and data_eml["verdict"] == "Clean / Legitimate")
    results["eml_upload"] = {"status_code": r_eml.status_code, "response": data_eml, "passed": t10_passed}
    all_passed = all_passed and t10_passed

    # 11. Database Persistence and History Listing
    print("\n--- [Test 11] Database Audit History (GET /api/history) ---")
    r_hist = requests.get(f"{API_BASE}/history?limit=10")
    assert r_hist.status_code == 200
    data_hist = r_hist.json()
    items = data_hist.get("items", [])
    print(f"  Total records in DB: {data_hist['total']} | Retrieved in page: {len(items)}")
    assert len(items) > 0
    top = items[0]
    print(f"  Most recent record: ID={top['id']}, Type={top['analysis_type']}, Verdict={top['overall_verdict']}, Threat={top['threat_level']}, Risk={top['risk_score']}")
    t11_passed = len(items) > 0 and "overall_verdict" in top and "threat_level" in top
    results["database_history"] = {"total": data_hist["total"], "latest_record": top, "passed": t11_passed}
    all_passed = all_passed and t11_passed

    # 12. Database Aggregated Stats
    print("\n--- [Test 12] Database Statistics Dashboard (GET /api/history/stats) ---")
    r_stats = requests.get(f"{API_BASE}/history/stats")
    assert r_stats.status_code == 200
    stats = r_stats.json()
    print(f"  Stats -> Total: {stats['total_analyses']} | Spam: {stats['spam_count']} | Phishing: {stats['phishing_count']} | Safe: {stats['safe_count']}")
    t12_passed = stats["total_analyses"] > 0
    results["database_stats"] = {"stats": stats, "passed": t12_passed}
    all_passed = all_passed and t12_passed

    # Save summary
    results["overall_passed"] = all_passed
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved final system test results to: {OUTPUT_REPORT}")
    print(f"All 12 functional system tests passed: {all_passed}")

if __name__ == "__main__":
    run_tests()
