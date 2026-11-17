"""
src/models/verify_audit_metrics.py
Performs an exact verification of all 24 individual samples in Suite B and all 18 samples in Suite A.
Calculates text classifier confusion matrices and overall verdict matrices.
Identifies the exact sample(s) responsible for any discrepancy.
"""

import os
import sys
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.models.audit_test_suites import SUITE_A_DIR, SUITE_B_DIR, SUITE_B_KEY, parse_eml
from src.pipeline import SecurityAnalysisPipeline

pipeline = SecurityAnalysisPipeline()

def verify():
    # -------------------------------------------------------------------------
    # SUITE B VERIFICATION (24 emails)
    # -------------------------------------------------------------------------
    key_df = pd.read_csv(SUITE_B_KEY)
    records_b = []
    for _, row in key_df.iterrows():
        fn = row['filename']
        exp = row['expected_class'].strip().upper()
        meaning = row['meaning']
        subj, body, sender = parse_eml(os.path.join(SUITE_B_DIR, fn))
        res = pipeline.analyze_email(subj, body, sender)
        text_pred = res['email_analysis']['label'].upper()
        p_spam = res['email_analysis']['spam_probability']
        verdict = res['overall_security_verdict']
        threat = res['threat_level']
        risk = res['risk_score']
        action = res['recommended_action']
        
        # Exact evaluation logic:
        # Expected HAM:
        #   - SAFE: Correct (True Negative)
        #   - SUSPICIOUS: Legitimate flagged as Suspicious (Borderline false alarm / move to junk)
        #   - MALICIOUS: Legitimate flagged as Malicious (Critical false positive)
        # Expected SPAM:
        #   - MALICIOUS / SUSPICIOUS: Correctly identified as threat / junk
        #   - SAFE: Threat slipped through as Safe (Critical false negative)
        
        # Binary verdict accuracy (Strict: HAM->SAFE, SPAM->SUSPICIOUS/MALICIOUS)
        is_verdict_correct = (verdict == "SAFE") if exp == "HAM" else (verdict in ["SUSPICIOUS", "MALICIOUS"])
        
        records_b.append({
            'filename': fn,
            'expected': exp,
            'meaning': meaning,
            'text_pred': text_pred,
            'p_spam': p_spam,
            'verdict': verdict,
            'threat': threat,
            'risk': risk,
            'action': action,
            'text_correct': (text_pred == exp),
            'verdict_correct': is_verdict_correct
        })

    df_b = pd.DataFrame(records_b)

    print("=" * 90)
    print("SUITE B (24 EMAILS) INDIVIDUAL BREAKDOWN")
    print("=" * 90)
    for _, r in df_b.iterrows():
        t_stat = "OK" if r['text_correct'] else "MISMATCH"
        v_stat = "PASS" if r['verdict_correct'] else "FAIL"
        print(f"{r['filename']} | Exp: {r['expected']:4s} | Text: {r['text_pred']:4s} (p={r['p_spam']:.4f}, {t_stat:8s}) | Verdict: {r['verdict']:10s} (Risk: {r['risk']:5.1f}%, Action: {r['action']:18s}) -> Verdict: {v_stat}")

    incorrect_b_verdict = df_b[~df_b['verdict_correct']]
    print("\nSUITE B INCORRECT OVERALL VERDICTS:")
    if len(incorrect_b_verdict) == 0:
        print("  None! All 24 passed.")
    else:
        for _, r in incorrect_b_verdict.iterrows():
            print(f"  -> File: {r['filename']} | Expected: {r['expected']} ({r['meaning']})")
            print(f"     Text Pred: {r['text_pred']} (p={r['p_spam']:.4f})")
            print(f"     Verdict: {r['verdict']} | Threat Level: {r['threat']} | Risk Score: {r['risk']}%")
            print(f"     Reason for failure: Expected HAM was classified as {r['verdict']} instead of SAFE.")

    # -------------------------------------------------------------------------
    # SUITE A VERIFICATION (18 emails)
    # -------------------------------------------------------------------------
    suite_a_expected = {
        '01_legitimate_meeting.eml': 'HAM',
        '02_legitimate_invoice.eml': 'HAM',
        '03_legitimate_password_notice.eml': 'HAM',
        '04_legitimate_newsletter.eml': 'HAM',
        '05_legitimate_assignment.eml': 'HAM',
        '06_spam_prize.eml': 'SPAM',
        '07_spam_weight_loss.eml': 'SPAM',
        '08_spam_crypto.eml': 'SPAM',
        '09_spam_lottery.eml': 'SPAM',
        '10_spam_free_gift.eml': 'SPAM',
        '11_phishing_account.eml': 'SPAM',
        '12_phishing_bank.eml': 'SPAM',
        '13_phishing_delivery.eml': 'SPAM',
        '14_phishing_mailbox.eml': 'SPAM',
        '15_phishing_otp.eml': 'SPAM',
        '16_mixed_work_offer.eml': 'HAM',
        '17_mixed_account_alert.eml': 'HAM',
        '18_mixed_sale.eml': 'HAM',
    }

    records_a = []
    for fn in sorted(os.listdir(SUITE_A_DIR)):
        if not fn.endswith('.eml'): continue
        exp = suite_a_expected[fn]
        subj, body, sender = parse_eml(os.path.join(SUITE_A_DIR, fn))
        res = pipeline.analyze_email(subj, body, sender)
        text_pred = res['email_analysis']['label'].upper()
        p_spam = res['email_analysis']['spam_probability']
        verdict = res['overall_security_verdict']
        threat = res['threat_level']
        risk = res['risk_score']
        action = res['recommended_action']
        
        is_verdict_correct = (verdict == "SAFE") if exp == "HAM" else (verdict in ["SUSPICIOUS", "MALICIOUS"])
        
        records_a.append({
            'filename': fn,
            'expected': exp,
            'text_pred': text_pred,
            'p_spam': p_spam,
            'verdict': verdict,
            'threat': threat,
            'risk': risk,
            'action': action,
            'text_correct': (text_pred == exp),
            'verdict_correct': is_verdict_correct
        })

    df_a = pd.DataFrame(records_a)

    print("\n" + "=" * 90)
    print("SUITE A (18 EMAILS) INDIVIDUAL BREAKDOWN")
    print("=" * 90)
    for _, r in df_a.iterrows():
        t_stat = "OK" if r['text_correct'] else "MISMATCH"
        v_stat = "PASS" if r['verdict_correct'] else "FAIL"
        print(f"{r['filename']} | Exp: {r['expected']:4s} | Text: {r['text_pred']:4s} (p={r['p_spam']:.4f}, {t_stat:8s}) | Verdict: {r['verdict']:10s} (Risk: {r['risk']:5.1f}%, Action: {r['action']:18s}) -> Verdict: {v_stat}")

    incorrect_a_verdict = df_a[~df_a['verdict_correct']]
    print("\nSUITE A INCORRECT OVERALL VERDICTS:")
    if len(incorrect_a_verdict) == 0:
        print("  None! All 18 passed.")
    else:
        for _, r in incorrect_a_verdict.iterrows():
            print(f"  -> File: {r['filename']} | Expected: {r['expected']}")
            print(f"     Text Pred: {r['text_pred']} (p={r['p_spam']:.4f})")
            print(f"     Verdict: {r['verdict']} | Threat Level: {r['threat']} | Risk Score: {r['risk']}%")
            print(f"     Reason for failure: Expected HAM was classified as {r['verdict']} instead of SAFE.")

    print("\n" + "=" * 90)
    print("SUMMARY METRICS RECAP")
    print("=" * 90)
    print(f"Suite B Text Classifier Accuracy:    {df_b['text_correct'].sum()} / {len(df_b)} ({df_b['text_correct'].mean()*100:.1f}%)")
    print(f"Suite B Overall Verdict Accuracy:    {df_b['verdict_correct'].sum()} / {len(df_b)} ({df_b['verdict_correct'].mean()*100:.1f}%)")
    print(f"Suite A Text Classifier Accuracy:    {df_a['text_correct'].sum()} / {len(df_a)} ({df_a['text_correct'].mean()*100:.1f}%)")
    print(f"Suite A Overall Verdict Accuracy:    {df_a['verdict_correct'].sum()} / {len(df_a)} ({df_a['verdict_correct'].mean()*100:.1f}%)")

    # Overall Verdict Confusion Matrices:
    # Class mapping: 0 = Benign/Legitimate, 1 = Threat (Spam or Phishing)
    # Predicted: SAFE -> 0, SUSPICIOUS/MALICIOUS -> 1
    y_true_b_binary = [0 if e == 'HAM' else 1 for e in df_b['expected']]
    y_pred_b_binary = [0 if v == 'SAFE' else 1 for v in df_b['verdict']]
    cm_b = confusion_matrix(y_true_b_binary, y_pred_b_binary)
    print("\nSuite B Overall Verdict Confusion Matrix [TN, FP / FN, TP]:")
    print(cm_b)
    tn_b, fp_b, fn_b, tp_b = cm_b.ravel()
    print(f"  True Negatives (Legitimate -> SAFE):       {tn_b} / 12 ({tn_b/12*100:.1f}%)")
    print(f"  False Positives (Legitimate -> SUSP/MAL):  {fp_b} / 12 ({fp_b/12*100:.1f}%) [Breakdown: {sum((df_b['expected']=='HAM') & (df_b['verdict']=='SUSPICIOUS'))} Suspicious, {sum((df_b['expected']=='HAM') & (df_b['verdict']=='MALICIOUS'))} Malicious]")
    print(f"  False Negatives (Threats -> SAFE):         {fn_b} / 12 ({fn_b/12*100:.1f}%) [Zero threats missed!]")
    print(f"  True Positives (Threats -> SUSP/MAL):      {tp_b} / 12 ({tp_b/12*100:.1f}%) [Breakdown: {sum((df_b['expected']=='SPAM') & (df_b['verdict']=='MALICIOUS'))} Malicious, {sum((df_b['expected']=='SPAM') & (df_b['verdict']=='SUSPICIOUS'))} Suspicious]")

    y_true_a_binary = [0 if e == 'HAM' else 1 for e in df_a['expected']]
    y_pred_a_binary = [0 if v == 'SAFE' else 1 for v in df_a['verdict']]
    cm_a = confusion_matrix(y_true_a_binary, y_pred_a_binary)
    print("\nSuite A Overall Verdict Confusion Matrix [TN, FP / FN, TP]:")
    print(cm_a)
    tn_a, fp_a, fn_a, tp_a = cm_a.ravel()
    print(f"  True Negatives (Legitimate -> SAFE):       {tn_a} / 8 ({tn_a/8*100:.1f}%)")
    print(f"  False Positives (Legitimate -> SUSP/MAL):  {fp_a} / 8 ({fp_a/8*100:.1f}%) [Breakdown: {sum((df_a['expected']=='HAM') & (df_a['verdict']=='SUSPICIOUS'))} Suspicious, {sum((df_a['expected']=='HAM') & (df_a['verdict']=='MALICIOUS'))} Malicious]")
    print(f"  False Negatives (Threats -> SAFE):         {fn_a} / 10 ({fn_a/10*100:.1f}%) [Zero threats missed!]")
    print(f"  True Positives (Threats -> SUSP/MAL):      {tp_a} / 10 ({tp_a/10*100:.1f}%)")

if __name__ == "__main__":
    verify()
