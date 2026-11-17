import os
import sys
import requests
import json

API_BASE = "http://127.0.0.1:8000/api"
SYNTHETIC_DIR = r"C:\Users\admin\Downloads\email_eml_test_samples"

def test_integration():
    print("=" * 70)
    print("PHASE 7: INTEGRATION AND REGRESSION TESTING AGAINST LIVE API")
    print("=" * 70)

    # 1. Health Endpoint
    print("\n[1] Testing Health Endpoint...")
    r = requests.get(f"{API_BASE}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health_data = r.json()
    print("  Status:", health_data.get("status"))
    print("  ML Pipeline:", health_data.get("ml_pipeline", {}).get("status"))
    print("  Database:", health_data.get("database", {}).get("status"))
    assert health_data.get("ml_pipeline", {}).get("email_model_loaded") is True

    # 2. Plain-Text Email Analysis
    print("\n[2] Testing Plain-Text Email Analysis...")
    payload_plain = {
        "subject": "Quarterly Planning Sync",
        "message": "Hi everyone, let's schedule our quarterly planning session next Tuesday at 2 PM in conference room B. Thanks!"
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload_plain)
    assert r.status_code == 200, f"Plain text email analysis failed: {r.status_code} - {r.text}"
    data_plain = r.json()
    risk_plain = data_plain.get("risk_score", data_plain.get("overall_risk_score", 0.0))
    print(f"  Plain Email -> Verdict: {data_plain['verdict']} | Risk Score: {risk_plain} | Spam Prob: {data_plain['email_analysis']['spam_probability']}")
    assert data_plain["email_analysis"]["is_spam"] is False

    # 3. HTML Email with CSS, Scripts, Entities, and Footers (Legitimate Newsletter Test)
    print("\n[3] Testing HTML Email with CSS, Script blocks, Entities, & Opt-out Footers...")
    payload_html = {
        "subject": "Tech Weekly Digest #128",
        "message": """
        <html>
        <head>
          <style>
            body { font-family: 'Verdana', sans-serif; background-color: #ffffff; color: #333333; }
            .header-banner { background: #004488; padding: 20px; color: #ffffff; }
            .card { border: 1px solid #e0e0e0; margin: 15px 0; padding: 15px; }
          </style>
          <script>
            var analyticsTracker = function() { return 42; };
          </script>
        </head>
        <body>
          <div class="header-banner">
            <h1>Tech &amp; Developer Weekly Digest</h1>
          </div>
          <p>Welcome to this week's edition &nbsp; featuring new open-source releases, framework benchmarks, and architecture best practices.</p>
          <div class="card">
            <h3>Python 3.12 Release Notes</h3>
            <p>Highlights include faster comprehension execution and improved error diagnostics.</p>
          </div>
          <hr/>
          <p style="font-size: 11px; color: #777777;">
            You received this email because you subscribed to Tech Weekly. To unsubscribe click here or manage your subscription preferences. All rights reserved copyright 2026.
          </p>
        </body>
        </html>
        """
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload_html)
    assert r.status_code == 200, f"HTML email analysis failed: {r.status_code} - {r.text}"
    data_html = r.json()
    risk_html = data_html.get("risk_score", data_html.get("overall_risk_score", 0.0))
    print(f"  HTML Newsletter -> Verdict: {data_html['verdict']} | Risk Score: {risk_html} | Spam Prob: {data_html['email_analysis']['spam_probability']} | Threat: {data_html['threat_level']}")
    assert data_html["email_analysis"]["is_spam"] is False, "HTML newsletter should be classified as Ham!"
    print(f"  Newsletter spam probability: {data_html['email_analysis']['spam_probability']:.4f} (Safe!)")

    # 4. High-Threat Spam & Phishing Detection
    print("\n[4] Testing Malicious Phishing Lure...")
    payload_phish = {
        "subject": "URGENT: Your account access has been suspended!",
        "message": "Dear customer, abnormal transactions were detected on your card. Click immediately to restore access: http://secure-banking-verification-update.com/login. Failure to verify within 24 hours will result in permanent closure."
    }
    r = requests.post(f"{API_BASE}/analyze/email", json=payload_phish)
    assert r.status_code == 200
    data_phish = r.json()
    risk_phish = data_phish.get("risk_score", data_phish.get("overall_risk_score", 0.0))
    print(f"  Phishing Lure -> Verdict: {data_phish['verdict']} | Threat Level: {data_phish['threat_level']} | Risk Score: {risk_phish} | Recommended Action: {data_phish['recommended_action']}")
    assert risk_phish >= 80.0
    assert data_phish["verdict"] in ["Phishing Attack Detected", "Spam Email"]

    # 5. Database History Persistence Verification
    print("\n[5] Testing Database Audit Persistence...")
    r = requests.get(f"{API_BASE}/history?limit=5")
    assert r.status_code == 200
    history_items = r.json().get("items", [])
    print(f"  Retrieved {len(history_items)} history items from PostgreSQL.")
    assert len(history_items) > 0
    latest = history_items[0]
    print(f"  Latest Log -> ID: {latest.get('id')} | Type: {latest.get('analysis_type')} | Verdict: {latest.get('verdict')} | Risk: {latest.get('risk_score')}")

    # 6. Test All 18 Synthetic Emails via .eml Upload Endpoint
    print("\n[6] Testing All 18 Synthetic .eml Files via /analyze/file Endpoint...")
    expected_mapping = {
        "01_legitimate_meeting.eml": ("Ham", False),
        "02_legitimate_invoice.eml": ("Ham", False),
        "03_legitimate_password_notice.eml": ("Ham", False),
        "04_legitimate_newsletter.eml": ("Ham", False),
        "05_legitimate_assignment.eml": ("Ham", False),
        "06_spam_prize.eml": ("Spam", True),
        "07_spam_weight_loss.eml": ("Spam", True),
        "08_spam_crypto.eml": ("Spam", True),
        "09_spam_lottery.eml": ("Spam", True),
        "10_spam_free_gift.eml": ("Spam", True),
        "11_phishing_account.eml": ("Spam", True),
        "12_phishing_bank.eml": ("Spam", True),
        "13_phishing_delivery.eml": ("Spam", True),
        "14_phishing_mailbox.eml": ("Spam", True),
        "15_phishing_otp.eml": ("Spam", True),
        "16_mixed_work_offer.eml": ("Ham", False),
        "17_mixed_account_alert.eml": ("Ham", False),
        "18_mixed_sale.eml": ("Ham", False),
    }

    synthetic_results = []
    correct_count = 0
    fp_count = 0
    fn_count = 0

    for fname in sorted(os.listdir(SYNTHETIC_DIR)):
        if not fname.endswith(".eml"):
            continue
        fpath = os.path.join(SYNTHETIC_DIR, fname)
        exp_label, exp_is_spam = expected_mapping.get(fname, ("Ham", False))

        with open(fpath, "rb") as f:
            files = {"file": (fname, f, "message/rfc822")}
            r = requests.post(f"{API_BASE}/analyze/file", files=files)

        assert r.status_code == 200, f"Failed on {fname}: {r.status_code} - {r.text}"
        res = r.json()
        email_eval = res.get("email_analysis", {})
        pred_label = email_eval.get("label", "Unknown")
        p_spam = email_eval.get("spam_probability", 0.0)
        overall_risk = res.get("overall_risk_score", res.get("risk_score", 0.0))
        verdict = res.get("verdict", "")
        action = res.get("recommended_action", "")

        is_correct = (pred_label == exp_label)
        if is_correct:
            correct_count += 1
        elif exp_is_spam and not email_eval.get("is_spam", False):
            fn_count += 1
        elif not exp_is_spam and email_eval.get("is_spam", False):
            fp_count += 1

        synthetic_results.append({
            "filename": fname,
            "expected_label": exp_label,
            "predicted_label": pred_label,
            "spam_probability": p_spam,
            "overall_risk_score": overall_risk,
            "verdict": verdict,
            "recommended_action": action,
            "is_correct": is_correct
        })

        match_str = "MATCH" if is_correct else "MISMATCH"
        print(f"  [{match_str}] {fname:<34} | Expected: {exp_label:<4} | Pred: {pred_label:<4} | P(spam): {p_spam:.4f} | Risk: {overall_risk:5.1f} | Action: {action}")

    print(f"\nSynthetic Suite Summary: {correct_count}/18 Correct ({correct_count/18*100:.1f}%) | FPs: {fp_count} | FNs: {fn_count}")
    assert fn_count == 0, f"Critical failure: {fn_count} phishing/spam emails were missed!"
    assert correct_count >= 17, f"Expected at least 17/18 correct, got {correct_count}"

    # Save integration test results for final report
    out_path = os.path.join("outputs", "reports", "phase7_integration_test_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "plain_email_test": data_plain,
            "html_newsletter_test": data_html,
            "phishing_test": data_phish,
            "synthetic_suite": synthetic_results,
            "accuracy": round(correct_count / 18, 4),
            "false_positives": fp_count,
            "false_negatives": fn_count
        }, f, indent=2)
    print(f"\nSaved integration test results to: {out_path}")
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_integration()
