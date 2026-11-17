"""
src/models/test_synthetic_emails.py
Tests all 18 synthetic .eml emails through the newly integrated production pipeline.
Reports individual predictions, probabilities, confidence, risk score, verdict, and action.
"""

import os
import sys
import email
from email.header import decode_header
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import SecurityAnalysisPipeline

SYNTHETIC_DIR = r"C:\Users\admin\Downloads\email_eml_test_samples"

EXPECTED_MAPPING = {
    "01_legitimate_meeting.eml": "Ham",
    "02_legitimate_invoice.eml": "Ham",
    "03_legitimate_password_notice.eml": "Ham",
    "04_legitimate_newsletter.eml": "Ham",
    "05_legitimate_assignment.eml": "Ham",
    "06_spam_prize.eml": "Spam",
    "07_spam_weight_loss.eml": "Spam",
    "08_spam_crypto.eml": "Spam",
    "09_spam_lottery.eml": "Spam",
    "10_spam_free_gift.eml": "Spam",
    "11_phishing_account.eml": "Spam",
    "12_phishing_bank.eml": "Spam",
    "13_phishing_delivery.eml": "Spam",
    "14_phishing_mailbox.eml": "Spam",
    "15_phishing_otp.eml": "Spam",
    "16_mixed_work_offer.eml": "Ham",
    "17_mixed_account_alert.eml": "Ham",
    "18_mixed_sale.eml": "Ham",
}

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

def get_body(msg):
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
                        t = payload.decode(charset, errors="replace")
                    except Exception:
                        t = payload.decode("latin-1", errors="replace")
                    parts.append(t)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                t = payload.decode(charset, errors="replace")
            except Exception:
                t = payload.decode("latin-1", errors="replace")
            parts.append(t)
    return "\n".join(parts).strip()

def main():
    pipe = SecurityAnalysisPipeline()
    print("=" * 90)
    print("EVALUATING 18 SYNTHETIC EMAILS WITH INTEGRATED MULTINOMIAL NAIVE BAYES PIPELINE")
    print(f"Decision Threshold: {pipe.email_predictor.threshold}")
    print("=" * 90)

    results = []
    correct_count = 0

    for fname in sorted(os.listdir(SYNTHETIC_DIR)):
        if not fname.endswith(".eml"):
            continue

        fpath = os.path.join(SYNTHETIC_DIR, fname)
        with open(fpath, "rb") as f:
            msg = email.message_from_bytes(f.read())

        subj = decode_mime(msg.get("Subject", ""))
        body = get_body(msg)

        res = pipe.analyze_email(subject=subj, message=body)
        ea = res["email_analysis"]

        expected = EXPECTED_MAPPING.get(fname, "Ham")
        predicted = ea["label"]
        is_correct = (predicted == expected)
        if is_correct:
            correct_count += 1

        results.append({
            "filename": fname,
            "expected": expected,
            "predicted": predicted,
            "p_spam": ea["spam_probability"],
            "p_ham": ea["ham_probability"],
            "confidence": ea["confidence_percent"],
            "overall_risk_score": res["overall_risk_score"],
            "verdict": res["verdict"],
            "threat_level": res["threat_level"],
            "action": res["recommended_action"],
            "urls_found": res["url_summary"]["total_urls_found"],
            "correct": is_correct
        })

    for r in results:
        status = "MATCH" if r["correct"] else "MISMATCH"
        print(f"[{status:8s}] {r['filename']:32s} | Exp: {r['expected']:4s} | Pred: {r['predicted']:4s} | P(spam)={r['p_spam']:.4f} | Risk={r['overall_risk_score']:4.1f} | Verdict: {r['verdict']}")

    print("\n" + "=" * 90)
    print(f"OVERALL SUMMARY: {correct_count} / {len(results)} ({correct_count / len(results) * 100:.1f}%) MATCHES")
    print("=" * 90)

if __name__ == "__main__":
    main()
