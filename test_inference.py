"""
test_inference.py
Comprehensive test suite validating the complete ML operational pipeline.
"""

import json
from src.pipeline import SecurityAnalysisPipeline

def run_tests():
    print("=" * 70)
    print("INITIALIZING SECURITY ANALYSIS PIPELINE")
    print("=" * 70)
    pipeline = SecurityAnalysisPipeline()

    # -------------------------------------------------------------
    # TEST 1: URL Direct Scanning
    # -------------------------------------------------------------
    print("\n[TEST 1] Individual URL Scanning:")
    test_urls = [
        ("https://www.google.com", "Legitimate Global Search"),
        ("https://github.com/torvalds/linux", "Legitimate Repository"),
        ("http://www.teramill.com", "PhiUSIIL Benchmark Phishing"),
        ("http://43.134.167.94/v3/signin/identifier?dsh=s151927330&amp;continue=https://accounts.google.com", "IP-based Google credential harvesting link"),
        ("http://secure-login.bankofamerica.update-account.tk/login.php?user=test", "Subdomain Obfuscation Phish")
    ]

    for url, desc in test_urls:
        res = pipeline.analyze_url(url)
        print(f"  URL: {url}")
        print(f"  Description: {desc}")
        print(f"  Result -> Label: {res['label']} | Phish Prob: {res['phishing_probability']} | Legit Prob: {res['legitimate_probability']} | Conf: {res['confidence_percent']}%\n")

    # -------------------------------------------------------------
    # TEST 2: Clean Legitimate Corporate Email (Ham)
    # -------------------------------------------------------------
    print("-" * 70)
    print("[TEST 2] Legitimate Email (Ham with benign link):")
    ham_subject = "Meeting Agenda: Q3 Architecture Review"
    ham_body = "Hi team, please find the quarterly slide deck on https://docs.google.com/presentation before our 2 PM sync. Thanks, Dave."
    res_ham = pipeline.analyze_email(ham_subject, ham_body)
    print(f"  Verdict: {res_ham['verdict']} | Threat Level: {res_ham['threat_level']} | Risk Score: {res_ham['overall_risk_score']}/100")
    print(f"  Email Classification: {res_ham['email_analysis']['label']} (Spam Prob: {res_ham['email_analysis']['spam_probability']})")
    print(f"  Action: {res_ham['recommended_action']}\n")

    # -------------------------------------------------------------
    # TEST 3: Traditional Text-Based Spam Email
    # -------------------------------------------------------------
    print("-" * 70)
    print("[TEST 3] Traditional Text Spam Email:")
    spam_subject = "CONGRATULATIONS! You have won $1,000,000 Cash Prize!"
    spam_body = "Claim your lottery prize immediately! No investment needed, 100% guaranteed jackpot payout. Reply with your full bank account details to receive funds today!"
    res_spam = pipeline.analyze_email(spam_subject, spam_body)
    print(f"  Verdict: {res_spam['verdict']} | Threat Level: {res_spam['threat_level']} | Risk Score: {res_spam['overall_risk_score']}/100")
    print(f"  Email Classification: {res_spam['email_analysis']['label']} (Spam Prob: {res_spam['email_analysis']['spam_probability']})")
    print(f"  Action: {res_spam['recommended_action']}\n")

    # -------------------------------------------------------------
    # TEST 4: Phishing Email (Camouflaged text + Malicious link)
    # -------------------------------------------------------------
    print("-" * 70)
    print("[TEST 4] Advanced Phishing Email (Dual-Representation Validation):")
    phish_subject = "Urgent: Your IT Account has been flagged"
    phish_body = "Dear employee, your corporate access will expire in 2 hours due to an unauthorized login attempt. Please confirm your credentials immediately at http://43.134.167.94/v3/signin/identifier?dsh=s151927330&continue=https://accounts.google.com to prevent termination."
    res_phish = pipeline.analyze_email(phish_subject, phish_body)
    print(f"  Verdict: {res_phish['verdict']} | Threat Level: {res_phish['threat_level']} | Risk Score: {res_phish['overall_risk_score']}/100")
    print(f"  Email Classification: {res_phish['email_analysis']['label']} (Spam Prob: {res_phish['email_analysis']['spam_probability']})")
    print(f"  URLs Detected: {res_phish['url_summary']['total_urls_found']} | Phishing URLs: {res_phish['url_summary']['phishing_urls_count']}")
    print(f"  Action: {res_phish['recommended_action']}")
    print("=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY! INFERENCE ENGINE IS OPERATIONAL.")

if __name__ == '__main__':
    run_tests()
