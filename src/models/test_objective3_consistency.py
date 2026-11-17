"""
src/models/test_objective3_consistency.py
Explicitly validates all situations A through H required by Objective 3:
A. HAM email + legitimate URL = normally SAFE (subject to intent analysis)
B. HAM email + phishing URL = MALICIOUS
C. SPAM email + legitimate URL = not automatically MALICIOUS (SUSPICIOUS)
D. HAM email + suspicious BEC indicators = at least SUSPICIOUS (or MALICIOUS when sufficient evidence)
E. Email without URLs + strong credential theft indicators = appropriate phishing-intent verdict (MALICIOUS)
F. Email with multiple URLs, including one phishing URL = overall verdict accounts for the malicious URL (MALICIOUS)
G. Legitimate password notifications, payroll emails, newsletters, and invoices = not automatically MALICIOUS
H. No extracted URLs must NOT be interpreted as proof that an email is safe (e.g. linkless BEC/phish)
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import SecurityAnalysisPipeline

pipeline = SecurityAnalysisPipeline()

def test_situation(code, description, subject, body, sender=None):
    res = pipeline.analyze_email(subject=subject, message=body, sender=sender)
    verdict = res["overall_security_verdict"]
    threat = res["threat_level"]
    risk = res["risk_score"]
    action = res["recommended_action"]
    exp = res["verdict_explanation"]
    email_label = res["email_analysis"]["label"]
    p_spam = res["email_analysis"]["spam_probability"]
    intent = res["phishing_intent_analysis"]["primary_intent"]
    intent_level = res["phishing_intent_analysis"]["intent_risk_level"]
    urls = [u["url"] + f" (phish_p={u['phishing_probability']:.2f})" for u in res["url_details"]]

    print("=" * 90)
    print(f"SITUATION {code}: {description}")
    print("-" * 90)
    print(f"Subject: {subject}")
    print(f"Sender:  {sender or 'None'}")
    print(f"Body:    {body[:120]}...")
    print(f"URLs:    {urls if urls else '[]'}")
    print(f"Email Classifier: {email_label} (p_spam={p_spam:.4f})")
    print(f"Phishing Intent:  {intent} (risk_level={intent_level})")
    print(f"Overall Verdict:  {verdict} | Threat: {threat} | Risk: {risk:.1f}% | Action: {action}")
    print(f"Explanation:      {exp}")
    return res

def run_objective_3_validation():
    # A. HAM email + legitimate URL = normally SAFE
    res_a = test_situation(
        "A", "HAM email + legitimate URL = normally SAFE",
        subject="Quarterly Engineering Roadmap and Documentation",
        body="Hi team, please find our Q4 technical documentation here: https://en.wikipedia.org/wiki/Software_engineering. See you at tomorrow's sync.",
        sender="lead@company.example"
    )
    assert res_a["overall_security_verdict"] == "SAFE", f"Expected SAFE, got {res_a['overall_security_verdict']}"
    assert res_a["recommended_action"] == "ALLOW"
    print(">>> PASS: Situation A verified.\n")

    # B. HAM email + phishing URL = MALICIOUS
    res_b = test_situation(
        "B", "HAM email + phishing URL = MALICIOUS",
        subject="Quarterly budget spreadsheet shared",
        body="Hi Alex, please find the updated expenditure model here: http://secure-update-paypal-login.com/verify-account. Thanks!",
        sender="colleague@company.example"
    )
    assert res_b["overall_security_verdict"] == "MALICIOUS", f"Expected MALICIOUS, got {res_b['overall_security_verdict']}"
    assert res_b["threat_level"] == "CRITICAL"
    print(">>> PASS: Situation B verified.\n")

    # C. SPAM email + legitimate URL = not automatically MALICIOUS (SUSPICIOUS)
    res_c = test_situation(
        "C", "SPAM email + legitimate URL = not automatically MALICIOUS (SUSPICIOUS)",
        subject="CONGRATULATIONS! Claim your free sweepstakes gift card now!",
        body="You have won the mega reward! Review our public rules at https://en.wikipedia.org/wiki/Lottery and claim your prize today!",
        sender="promo@rewards-club.example"
    )
    assert res_c["overall_security_verdict"] == "SUSPICIOUS", f"Expected SUSPICIOUS, got {res_c['overall_security_verdict']}"
    assert res_c["recommended_action"] == "MOVE_TO_JUNK"
    print(">>> PASS: Situation C verified.\n")

    # D. HAM email + suspicious BEC indicators = at least SUSPICIOUS when sufficient evidence exists
    res_d = test_situation(
        "D", "HAM email + suspicious BEC indicators = at least SUSPICIOUS / MALICIOUS",
        subject="Quick favor - are you at your desk?",
        body="Are you at your desk right now? I need you to handle a quick discreet acquisition wire. Keep this confidential.",
        sender="CEO Johnathan Smith <ceo.executive.urgent@gmail.com>"
    )
    assert res_d["overall_security_verdict"] in ["SUSPICIOUS", "MALICIOUS"], f"Expected SUSPICIOUS/MALICIOUS, got {res_d['overall_security_verdict']}"
    assert res_d["phishing_intent_analysis"]["primary_intent"] == "BUSINESS_EMAIL_COMPROMISE"
    print(">>> PASS: Situation D verified.\n")

    # E. Email without URLs + strong credential theft indicators = appropriate phishing-intent verdict
    res_e = test_situation(
        "E", "Email without URLs + strong credential theft indicators = appropriate phishing-intent verdict",
        subject="URGENT: Password expired and account suspended",
        body="Your account access has been suspended. Reply directly with your current username and password to restore access immediately.",
        sender="it-admin@external-domain.example"
    )
    assert res_e["overall_security_verdict"] == "MALICIOUS", f"Expected MALICIOUS, got {res_e['overall_security_verdict']}"
    assert res_e["phishing_intent_analysis"]["primary_intent"] in ["CREDENTIAL_THEFT", "SOCIAL_ENGINEERING_IMPERSONATION"]
    print(">>> PASS: Situation E verified.\n")

    # F. Email with multiple URLs, including one phishing URL = accounts for malicious URL
    res_f = test_situation(
        "F", "Email with multiple URLs, including one phishing URL = accounts for malicious URL",
        subject="Resources for upcoming sprint",
        body="Hi team, check our wiki at https://wikipedia.org and verify your login at http://secure-update-paypal-login.com/verify-account before starting.",
        sender="pm@company.example"
    )
    assert res_f["overall_security_verdict"] == "MALICIOUS", f"Expected MALICIOUS, got {res_f['overall_security_verdict']}"
    assert res_f["threat_level"] == "CRITICAL"
    assert res_f["url_summary"]["phishing_urls_count"] >= 1
    print(">>> PASS: Situation F verified.\n")

    # G. Legitimate password notifications, payroll, newsletters, invoices = not automatically MALICIOUS
    res_g1 = test_situation(
        "G1", "Legitimate password changed notification",
        subject="Security Notice: Your password was successfully changed",
        body="This is an automated notification that your password was changed. If you made this change, no further action is needed.",
        sender="security@service.internal"
    )
    assert res_g1["overall_security_verdict"] == "SAFE", f"Expected SAFE, got {res_g1['overall_security_verdict']}"

    res_g2 = test_situation(
        "G2", "Legitimate payroll review with negative security advice",
        subject="Action required: confirm your payroll details",
        body="Our annual payroll records review is open. Confirm details by 30 Nov. Use your usual company bookmark. Payroll will never ask for your password or one-time code by email.",
        sender="payroll@company.example"
    )
    assert res_g2["overall_security_verdict"] == "SAFE", f"Expected SAFE, got {res_g2['overall_security_verdict']}"
    print(">>> PASS: Situation G verified.\n")

    # H. No extracted URLs must NOT be interpreted as proof that an email is safe
    res_h = test_situation(
        "H", "No extracted URLs must NOT be interpreted as proof that an email is safe",
        subject="Re: updated vendor bank details",
        body="We changed our settlement account due to an internal banking update. Ignore bank details on previous invoices and remit all pending amounts to the attached revised instructions. This change is confidential. Do not verify by calling our usual office number because the lines are being migrated. Proceed with invoice payments using the new routing code.",
        sender="accounts-payable@northwind-supplies.example"
    )
    assert len(res_h["url_details"]) == 0
    assert res_h["overall_security_verdict"] in ["SUSPICIOUS", "MALICIOUS"], f"Expected SUSPICIOUS/MALICIOUS, got {res_h['overall_security_verdict']}"
    assert res_h["overall_security_verdict"] != "SAFE", "Failed: Linkless vendor bank update was falsely marked SAFE!"
    print(">>> PASS: Situation H verified.\n")

    print("=" * 90)
    print("ALL OBJECTIVE 3 CONSISTENCY SITUATIONS (A THROUGH H) PASSED 100%!")
    print("=" * 90)

if __name__ == "__main__":
    run_objective_3_validation()
