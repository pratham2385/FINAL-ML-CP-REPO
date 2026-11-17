"""
src/models/audit_test_suites.py
Audits Suite A (18 emails) and Suite B (24 emails) across all three detection layers:
1. Email Text Classifier (MultinomialNB)
2. URL Classifier (Random Forest)
3. Phishing Intent Layer (PhishingIntentDetector)
4. Overall Security Verdict & Risk Aggregator (SecurityRiskAggregator)
"""

import os
import sys
import email
from email.header import decode_header
import pandas as pd
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import SecurityAnalysisPipeline

SUITE_A_DIR = r"C:\Users\admin\Downloads\email_eml_test_samples"
SUITE_B_DIR = r"C:\Users\admin\Downloads\hard_email_test_suite\hard_email_test_suite\emails"
SUITE_B_KEY = r"C:\Users\admin\Downloads\hard_email_test_suite\hard_email_test_suite\ANSWER_KEY.csv"

def decode_mime(val):
    if not val:
        return ""
    try:
        parts = decode_header(str(val))
        res = []
        for content, enc in parts:
            if isinstance(content, bytes):
                res.append(content.decode(enc or "utf-8", errors="replace"))
            else:
                res.append(str(content))
        return " ".join(res).strip()
    except Exception:
        return str(val).strip()

def parse_eml(filepath):
    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f)
    subject = decode_mime(msg.get("Subject", ""))
    sender = decode_mime(msg.get("From", ""))
    parts = []
    if msg.is_multipart():
        for p in msg.walk():
            if "attachment" in str(p.get("Content-Disposition", "")):
                continue
            if p.get_content_type() in ["text/plain", "text/html"]:
                payload = p.get_payload(decode=True)
                if payload:
                    charset = p.get_content_charset() or "utf-8"
                    try:
                        parts.append(payload.decode(charset, errors="replace"))
                    except Exception:
                        parts.append(payload.decode("latin-1", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                parts.append(payload.decode(charset, errors="replace"))
            except Exception:
                parts.append(payload.decode("latin-1", errors="replace"))
        else:
            parts.append(msg.get_payload() or "")
    body = "\n".join(parts)
    return subject, body, sender

def run_audit():
    pipeline = SecurityAnalysisPipeline()

    print("=" * 100)
    print("AUDITING SUITE A: 18-EMAIL TEST SUITE")
    print("=" * 100)

    suite_a_expected = {
        "01_legitimate_meeting.eml": "HAM",
        "02_legitimate_invoice.eml": "HAM",
        "03_legitimate_password_notice.eml": "HAM",
        "04_legitimate_newsletter.eml": "HAM",
        "05_legitimate_assignment.eml": "HAM",
        "06_spam_prize.eml": "SPAM",
        "07_spam_weight_loss.eml": "SPAM",
        "08_spam_crypto.eml": "SPAM",
        "09_spam_lottery.eml": "SPAM",
        "10_spam_free_gift.eml": "SPAM",
        "11_phishing_account.eml": "SPAM",
        "12_phishing_bank.eml": "SPAM",
        "13_phishing_delivery.eml": "SPAM",
        "14_phishing_mailbox.eml": "SPAM",
        "15_phishing_otp.eml": "SPAM",
        "16_mixed_work_offer.eml": "HAM",
        "17_mixed_account_alert.eml": "HAM",
        "18_mixed_sale.eml": "HAM",
    }

    results_a = []
    for fn in sorted(os.listdir(SUITE_A_DIR)):
        if not fn.endswith(".eml"):
            continue
        fp = os.path.join(SUITE_A_DIR, fn)
        subject, body, sender = parse_eml(fp)
        exp = suite_a_expected.get(fn, "UNKNOWN")
        res = pipeline.analyze_email(subject=subject, message=body, sender=sender)
        
        email_pred = res["email_analysis"]["label"].upper() # HAM or SPAM
        spam_prob = res["email_analysis"]["spam_probability"]
        urls = res.get("url_details", [])
        url_cnt = len(urls)
        phish_urls = res["url_summary"]["phishing_urls_count"]
        max_phish_p = res["url_summary"]["max_phishing_probability"]
        intent_cat = res["phishing_intent_analysis"]["primary_intent"]
        intent_risk = res["phishing_intent_analysis"]["intent_risk_level"]
        intent_score = res["phishing_intent_analysis"]["intent_score"]
        signals = res["phishing_intent_analysis"]["detected_signals"]
        verdict = res["overall_security_verdict"]
        risk_score = res["risk_score"]
        
        # In terms of security verdict correctness:
        # If expected is HAM: verdict should be SAFE (or SUSPICIOUS if borderline marketing).
        # If expected is SPAM: verdict should be SUSPICIOUS or MALICIOUS.
        # Email classifier match:
        email_match = (email_pred == exp)
        
        results_a.append({
            "filename": fn,
            "expected": exp,
            "subject": subject,
            "email_pred": email_pred,
            "spam_prob": spam_prob,
            "email_match": email_match,
            "url_count": url_cnt,
            "phish_urls": phish_urls,
            "max_phish_prob": max_phish_p,
            "intent_cat": intent_cat,
            "intent_risk": intent_risk,
            "intent_score": intent_score,
            "signals": signals,
            "verdict": verdict,
            "risk_score": risk_score,
        })

    df_a = pd.DataFrame(results_a)
    print(df_a[["filename", "expected", "email_pred", "spam_prob", "url_count", "intent_cat", "intent_risk", "verdict", "risk_score"]].to_string())
    print("\nSuite A Email Text Classifier Accuracy:", f"{(df_a['email_match'].sum())} / {len(df_a)} ({df_a['email_match'].mean()*100:.1f}%)")

    print("\n" + "=" * 100)
    print("AUDITING SUITE B: 24-EMAIL HARD TEST SUITE")
    print("=" * 100)

    key_df = pd.read_csv(SUITE_B_KEY)
    results_b = []
    for _, row in key_df.iterrows():
        fn = row["filename"]
        exp = row["expected_class"].strip().upper()
        meaning = row["meaning"]
        fp = os.path.join(SUITE_B_DIR, fn)
        if not os.path.exists(fp):
            print(f"File not found: {fp}")
            continue
        subject, body, sender = parse_eml(fp)
        res = pipeline.analyze_email(subject=subject, message=body, sender=sender)
        
        email_pred = res["email_analysis"]["label"].upper() # HAM or SPAM
        spam_prob = res["email_analysis"]["spam_probability"]
        urls = res.get("url_details", [])
        url_cnt = len(urls)
        phish_urls = res["url_summary"]["phishing_urls_count"]
        max_phish_p = res["url_summary"]["max_phishing_probability"]
        intent_cat = res["phishing_intent_analysis"]["primary_intent"]
        intent_risk = res["phishing_intent_analysis"]["intent_risk_level"]
        intent_score = res["phishing_intent_analysis"]["intent_score"]
        signals = res["phishing_intent_analysis"]["detected_signals"]
        verdict = res["overall_security_verdict"]
        risk_score = res["risk_score"]
        
        email_match = (email_pred == exp)
        
        # Overall verdict correctness:
        # Expected HAM -> Overall SAFE (or SUSPICIOUS only if anomalous/marketing)
        # Expected SPAM -> Overall SUSPICIOUS or MALICIOUS
        verdict_correct = (verdict == "SAFE") if exp == "HAM" else (verdict in ["SUSPICIOUS", "MALICIOUS"])
        
        results_b.append({
            "filename": fn,
            "expected": exp,
            "subject": subject,
            "email_pred": email_pred,
            "spam_prob": spam_prob,
            "email_match": email_match,
            "url_count": url_cnt,
            "phish_urls": phish_urls,
            "max_phish_prob": max_phish_p,
            "intent_cat": intent_cat,
            "intent_risk": intent_risk,
            "intent_score": intent_score,
            "signals": signals,
            "verdict": verdict,
            "risk_score": risk_score,
            "verdict_correct": verdict_correct,
            "urls": [u["url"] + f" (p={u['phishing_probability']:.2f})" for u in urls]
        })

    df_b = pd.DataFrame(results_b)
    print(df_b[["filename", "expected", "email_pred", "spam_prob", "url_count", "intent_cat", "intent_risk", "verdict", "risk_score", "verdict_correct"]].to_string())
    print("\nSuite B Email Text Classifier Accuracy:", f"{(df_b['email_match'].sum())} / {len(df_b)} ({df_b['email_match'].mean()*100:.1f}%)")
    print("Suite B Overall Verdict Correctness:", f"{(df_b['verdict_correct'].sum())} / {len(df_b)} ({df_b['verdict_correct'].mean()*100:.1f}%)")

if __name__ == "__main__":
    run_audit()
