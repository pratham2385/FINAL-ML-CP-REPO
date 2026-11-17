"""
Inspect the 8 specific emails in detail:
Suite B: email_02, email_04, email_15, email_16, email_18, email_21, email_22, email_24
Suite A: 18_mixed_sale.eml
"""
import os
import sys
import email
from email.header import decode_header
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import SecurityAnalysisPipeline
from src.models.audit_test_suites import parse_eml, SUITE_A_DIR, SUITE_B_DIR

pipeline = SecurityAnalysisPipeline()

def inspect_file(path, label, exp):
    print("=" * 80)
    print(f"FILE: {label} | Expected: {exp}")
    print("=" * 80)
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f)
    print("FROM:", msg.get("From"))
    print("SUBJECT:", msg.get("Subject"))
    print("DATE:", msg.get("Date"))
    subj, body, sender = parse_eml(path)
    print("BODY (preview):")
    print(body[:300])
    print("---")
    
    res = pipeline.analyze_email(subject=subj, message=body, sender=sender)
    print("EMAIL CLASSIFIER:")
    print("  Label:", res["email_analysis"]["label"])
    print("  P(spam):", res["email_analysis"]["spam_probability"])
    print("URL ANALYSIS:")
    print("  Extracted URLs:", [u["url"] for u in res["url_details"]])
    for u in res["url_details"]:
        print(f"    {u['url']} -> p_phish={u['phishing_probability']:.4f}, is_phish={u['is_phishing']}")
    print("PHISHING INTENT:")
    pi = res["phishing_intent_analysis"]
    print("  Has intent:", pi["has_phishing_intent"])
    print("  Primary intent:", pi["primary_intent"])
    print("  Risk level:", pi["intent_risk_level"])
    print("  Score:", pi["intent_score"])
    print("  Detected signals:", pi["detected_signals"])
    print("  Evidence:", pi["evidence"])
    print("  Mitigating factors:", pi.get("mitigating_factors", []))
    print("  Sender indicators:", pi.get("sender_indicators", {}))
    print("OVERALL VERDICT:")
    print("  Verdict:", res["overall_security_verdict"])
    print("  Threat level:", res["threat_level"])
    print("  Risk score:", res["risk_score"])
    print("  Explanation:", res["verdict_explanation"])

for fn, exp in [
    ("email_02.eml", "HAM"),
    ("email_04.eml", "HAM"),
    ("email_15.eml", "SPAM"),
    ("email_16.eml", "SPAM"),
    ("email_18.eml", "SPAM"),
    ("email_21.eml", "SPAM"),
    ("email_22.eml", "SPAM"),
    ("email_24.eml", "SPAM"),
]:
    fp = os.path.join(SUITE_B_DIR, fn)
    inspect_file(fp, f"Suite B: {fn}", exp)

fp_a = os.path.join(SUITE_A_DIR, "18_mixed_sale.eml")
inspect_file(fp_a, "Suite A: 18_mixed_sale.eml", "HAM")
