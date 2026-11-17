"""
src/models/benchmark_email_models.py
Phase 2: Email Model Benchmarking & Threshold Optimization
Trains, evaluates, and compares:
1. Logistic Regression (tuning C and class_weight)
2. Linear SVM (LinearSVC with CalibratedClassifierCV sigmoid calibration)
3. Multinomial Naive Bayes (tuning alpha)

Features: TF-IDF unigram+bigram fitted exclusively on the training set.
Evaluates on:
- Validation set (tuning & threshold selection)
- Test set (untouched benchmark)
- Hard Ham holdout (external challenge benchmark)
- 18 Synthetic .eml test emails (practical real-world samples)

Saves candidate models to outputs/models/candidates/ without overwriting production models.
"""

import os
import sys
import time
import json
import email
from email.header import decode_header
from typing import Dict, Any, List, Tuple

import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix
)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.features.email_preprocessor import preprocess_email_text

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed", "splits")
TRAIN_PATH = os.path.join(DATA_DIR, "train_emails.parquet")
VAL_PATH = os.path.join(DATA_DIR, "val_emails.parquet")
TEST_PATH = os.path.join(DATA_DIR, "test_emails.parquet")
HARD_HAM_PATH = os.path.join(DATA_DIR, "hard_ham_holdout.parquet")
SYNTHETIC_DIR = r"C:\Users\admin\Downloads\email_eml_test_samples"

OUTPUT_CANDIDATES_DIR = os.path.join(PROJECT_ROOT, "outputs", "models", "candidates")
OUTPUT_REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "reports")


def decode_mime_header(header_val: Any) -> str:
    if not header_val:
        return ""
    try:
        parts = decode_header(str(header_val))
        res = []
        for content, enc in parts:
            if isinstance(content, bytes):
                res.append(content.decode(enc or "utf-8", errors="replace"))
            else:
                res.append(str(content))
        return " ".join(res).strip()
    except Exception:
        return str(header_val).strip()


def extract_mime_body(msg: email.message.Message) -> str:
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            cdispo = str(part.get("Content-Disposition", ""))
            if "attachment" in cdispo:
                continue
            ctype = part.get_content_type()
            if ctype in ["text/plain", "text/html"]:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        text = payload.decode(charset, errors="replace")
                    except Exception:
                        text = payload.decode("latin-1", errors="replace")
                    body_parts.append(text)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
            except Exception:
                text = payload.decode("latin-1", errors="replace")
            body_parts.append(text)

    return "\n".join(body_parts).strip()


def load_synthetic_samples() -> List[Dict[str, Any]]:
    samples = []
    # Expected labels mapping: 1-5 Ham (0), 6-15 Spam (1), 16-18 Ham (0)
    expected_mapping = {
        "01_legitimate_meeting.eml": 0,
        "02_legitimate_invoice.eml": 0,
        "03_legitimate_password_notice.eml": 0,
        "04_legitimate_newsletter.eml": 0,
        "05_legitimate_assignment.eml": 0,
        "06_spam_prize.eml": 1,
        "07_spam_weight_loss.eml": 1,
        "08_spam_crypto.eml": 1,
        "09_spam_lottery.eml": 1,
        "10_spam_free_gift.eml": 1,
        "11_phishing_account.eml": 1,
        "12_phishing_bank.eml": 1,
        "13_phishing_delivery.eml": 1,
        "14_phishing_mailbox.eml": 1,
        "15_phishing_otp.eml": 1,
        "16_mixed_work_offer.eml": 0,
        "17_mixed_account_alert.eml": 0,
        "18_mixed_sale.eml": 0,
    }

    if not os.path.exists(SYNTHETIC_DIR):
        print(f"Warning: {SYNTHETIC_DIR} does not exist.")
        return samples

    for fname in sorted(os.listdir(SYNTHETIC_DIR)):
        if not fname.endswith(".eml"):
            continue
        fpath = os.path.join(SYNTHETIC_DIR, fname)
        with open(fpath, "rb") as f:
            msg = email.message_from_bytes(f.read())
        subj = decode_mime_header(msg.get("Subject", ""))
        body = extract_mime_body(msg)
        cleaned = preprocess_email_text(subj, body)
        expected = expected_mapping.get(fname, 0)
        samples.append({
            "filename": fname,
            "subject": subj,
            "body": body,
            "cleaned_text": cleaned,
            "expected_label": expected,
            "expected_label_name": "spam" if expected == 1 else "ham"
        })
    return samples


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.50) -> Dict[str, Any]:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    accuracy = float(accuracy_score(y_true, y_pred))
    spam_prec = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    spam_rec = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    spam_f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))

    ham_prec = float(precision_score(y_true, y_pred, pos_label=0, zero_division=0))
    ham_rec = float(recall_score(y_true, y_pred, pos_label=0, zero_division=0))

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0
    pr_auc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0
    brier = float(brier_score_loss(y_true, y_prob))

    return {
        "threshold": round(float(threshold), 4),
        "accuracy": round(accuracy, 4),
        "spam_precision": round(spam_prec, 4),
        "spam_recall": round(spam_rec, 4),
        "spam_f1": round(spam_f1, 4),
        "ham_precision": round(ham_prec, 4),
        "ham_recall": round(ham_rec, 4),
        "fpr": round(fpr, 4),
        "fpr_percentage": round(fpr * 100, 2),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        }
    }


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Tuple[float, List[Dict[str, Any]]]:
    """Calculates Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    bin_details = []

    for i in range(n_bins):
        b_low = bin_boundaries[i]
        b_high = bin_boundaries[i + 1]
        mask = (y_prob >= b_low) & (y_prob <= b_high if i == n_bins - 1 else y_prob < b_high)
        cnt = np.sum(mask)
        if cnt > 0:
            acc = float(np.mean(y_true[mask]))
            conf = float(np.mean(y_prob[mask]))
            ece += (cnt / n) * abs(acc - conf)
            bin_details.append({
                "bin_range": f"[{b_low:.1f}, {b_high:.1f}]",
                "count": int(cnt),
                "accuracy": round(acc, 4),
                "confidence": round(conf, 4)
            })

    return round(float(ece), 4), bin_details


def optimize_threshold(y_true: np.ndarray, y_prob: np.ndarray, target_fpr: float = 0.005) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Sweeps thresholds from 0.10 to 0.95 (step 0.01) on validation data.
    Finds threshold with FPR <= target_fpr (0.5%) maximizing spam recall.
    """
    thresholds = np.linspace(0.10, 0.95, 86)
    history = []
    qualifying = []

    for th in thresholds:
        m = compute_metrics(y_true, y_prob, threshold=th)
        history.append({
            "threshold": round(float(th), 2),
            "fpr": m["fpr"],
            "recall": m["spam_recall"],
            "precision": m["spam_precision"],
            "f1": m["spam_f1"]
        })
        if m["fpr"] <= target_fpr:
            qualifying.append((m["spam_recall"], m["spam_f1"], float(th), m))

    if qualifying:
        # Sort by recall descending, then f1 descending
        qualifying.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_rec, best_f1, best_th, best_m = qualifying[0]
        status = f"Target FPR <= {target_fpr*100:.1f}% achieved (FPR: {best_m['fpr']*100:.2f}%, Recall: {best_rec*100:.2f}%)"
    else:
        # Honest fallback: minimize FPR among thresholds with Recall >= 0.90
        print(f"Warning: Target FPR <= {target_fpr*100:.1f}% was not strictly achievable. Finding best compromise...")
        best_th = 0.50
        min_fpr = 1.0
        best_m = compute_metrics(y_true, y_prob, threshold=0.50)
        for h in history:
            if h["recall"] >= 0.90 and h["fpr"] < min_fpr:
                min_fpr = h["fpr"]
                best_th = h["threshold"]
                best_m = compute_metrics(y_true, y_prob, threshold=best_th)
        status = f"Best compromise selected: Threshold {best_th} (FPR: {best_m['fpr']*100:.2f}%, Recall: {best_m['spam_recall']*100:.2f}%)"

    return round(float(best_th), 4), best_m, history


def main():
    print("=" * 70)
    print("PHASE 2: EMAIL MODEL BENCHMARKING & THRESHOLD OPTIMIZATION")
    print("=" * 70)

    # 1. Load Parquet datasets
    print("\nLoading datasets...")
    train_df = pd.read_parquet(TRAIN_PATH)
    val_df = pd.read_parquet(VAL_PATH)
    test_df = pd.read_parquet(TEST_PATH)
    hard_ham_df = pd.read_parquet(HARD_HAM_PATH)
    synth_samples = load_synthetic_samples()

    print(f"  Train:     {len(train_df)} rows")
    print(f"  Val:       {len(val_df)} rows")
    print(f"  Test:      {len(test_df)} rows")
    print(f"  Hard Ham:  {len(hard_ham_df)} rows")
    print(f"  Synthetic: {len(synth_samples)} samples")

    y_train = train_df["label"].values
    y_val = val_df["label"].values
    y_test = test_df["label"].values
    y_hard_ham = hard_ham_df["label"].values

    # 2. Fit TF-IDF Vectorizer EXCLUSIVELY on training set
    print("\nFitting TfidfVectorizer exclusively on training dataset...")
    t0 = time.time()
    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=5,
        max_df=0.95,
        sublinear_tf=True
    )
    X_train = tfidf.fit_transform(train_df["cleaned_text"])
    fit_time = time.time() - t0
    vocab_size = len(tfidf.vocabulary_)
    print(f"  TF-IDF fit time: {fit_time:.2f}s, Vocabulary: {vocab_size} n-grams")

    # Transform holdouts
    print("Transforming validation, test, hard_ham, and synthetic samples...")
    X_val = tfidf.transform(val_df["cleaned_text"])
    X_test = tfidf.transform(test_df["cleaned_text"])
    X_hard_ham = tfidf.transform(hard_ham_df["cleaned_text"])
    X_synth = tfidf.transform([s["cleaned_text"] for s in synth_samples])

    # 3. Model Training & Validation Tuning
    candidates = {}

    # -------------------------------------------------------------
    # Candidate 1: Logistic Regression
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print("1. Tuning & Training Logistic Regression")
    print("-" * 60)
    lr_c_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    best_lr_score = -1.0
    best_lr_c = 2.0
    best_lr_cw = None

    for cw in [None, "balanced"]:
        for c in lr_c_values:
            lr_tmp = LogisticRegression(C=c, class_weight=cw, max_iter=1000, random_state=42)
            lr_tmp.fit(X_train, y_train)
            probs_val = lr_tmp.predict_proba(X_val)[:, 1]
            pr_auc_val = average_precision_score(y_val, probs_val)
            f1_val = f1_score(y_val, (probs_val >= 0.5).astype(int), pos_label=1)
            score = (pr_auc_val + f1_val) / 2.0
            if score > best_lr_score:
                best_lr_score = score
                best_lr_c = c
                best_lr_cw = cw

    print(f"  Best Logistic Regression params: C={best_lr_c}, class_weight={best_lr_cw}")
    t0_train = time.time()
    lr_model = LogisticRegression(C=best_lr_c, class_weight=best_lr_cw, max_iter=1000, random_state=42)
    lr_model.fit(X_train, y_train)
    lr_train_time = time.time() - t0_train

    t0_pred = time.time()
    lr_val_probs = lr_model.predict_proba(X_val)[:, 1]
    lr_pred_latency_ms = ((time.time() - t0_pred) / len(y_val)) * 1000

    candidates["logistic_regression"] = {
        "name": "Logistic Regression",
        "model": lr_model,
        "params": {"C": best_lr_c, "class_weight": best_lr_cw, "max_iter": 1000, "random_state": 42},
        "train_time_sec": round(lr_train_time, 3),
        "pred_latency_ms": round(lr_pred_latency_ms, 4),
        "val_probs": lr_val_probs
    }

    # -------------------------------------------------------------
    # Candidate 2: Linear SVM (CalibratedClassifierCV)
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print("2. Tuning & Training Linear SVM with Sigmoid Calibration")
    print("-" * 60)
    svm_c_values = [0.1, 0.5, 1.0, 2.0]
    best_svm_score = -1.0
    best_svm_c = 1.0

    for c in svm_c_values:
        svm_base = LinearSVC(C=c, random_state=42, max_iter=2000)
        svm_base.fit(X_train, y_train)
        df_val = svm_base.decision_function(X_val)
        pr_auc_val = average_precision_score(y_val, df_val)
        if pr_auc_val > best_svm_score:
            best_svm_score = pr_auc_val
            best_svm_c = c

    print(f"  Best LinearSVC base C: {best_svm_c}")
    print("  Fitting CalibratedClassifierCV (method='sigmoid', cv=5)...")
    t0_train = time.time()
    svm_cal = CalibratedClassifierCV(
        estimator=LinearSVC(C=best_svm_c, random_state=42, max_iter=2000),
        method="sigmoid",
        cv=5
    )
    svm_cal.fit(X_train, y_train)
    svm_train_time = time.time() - t0_train

    t0_pred = time.time()
    svm_val_probs = svm_cal.predict_proba(X_val)[:, 1]
    svm_pred_latency_ms = ((time.time() - t0_pred) / len(y_val)) * 1000

    candidates["linear_svc"] = {
        "name": "Linear SVM (Sigmoid-Calibrated)",
        "model": svm_cal,
        "params": {"C": best_svm_c, "method": "sigmoid", "cv": 5, "random_state": 42},
        "train_time_sec": round(svm_train_time, 3),
        "pred_latency_ms": round(svm_pred_latency_ms, 4),
        "val_probs": svm_val_probs
    }

    # -------------------------------------------------------------
    # Candidate 3: Multinomial Naive Bayes
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print("3. Tuning & Training Multinomial Naive Bayes")
    print("-" * 60)
    nb_alphas = [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
    best_nb_score = -1.0
    best_nb_alpha = 0.1

    for a in nb_alphas:
        nb_tmp = MultinomialNB(alpha=a)
        nb_tmp.fit(X_train, y_train)
        probs_val = nb_tmp.predict_proba(X_val)[:, 1]
        score = average_precision_score(y_val, probs_val)
        if score > best_nb_score:
            best_nb_score = score
            best_nb_alpha = a

    print(f"  Best MultinomialNB alpha: {best_nb_alpha}")
    t0_train = time.time()
    nb_model = MultinomialNB(alpha=best_nb_alpha)
    nb_model.fit(X_train, y_train)
    nb_train_time = time.time() - t0_train

    t0_pred = time.time()
    nb_val_probs = nb_model.predict_proba(X_val)[:, 1]
    nb_pred_latency_ms = ((time.time() - t0_pred) / len(y_val)) * 1000

    candidates["multinomial_nb"] = {
        "name": "Multinomial Naive Bayes",
        "model": nb_model,
        "params": {"alpha": best_nb_alpha},
        "train_time_sec": round(nb_train_time, 3),
        "pred_latency_ms": round(nb_pred_latency_ms, 4),
        "val_probs": nb_val_probs
    }

    # 4. Threshold Optimization on Validation Data (Step 3)
    print("\n" + "=" * 70)
    print("STEP 3: THRESHOLD OPTIMIZATION (VALIDATION SET ONLY)")
    print("=" * 70)

    for ckey, cdata in candidates.items():
        vprobs = cdata["val_probs"]
        val_default_m = compute_metrics(y_val, vprobs, threshold=0.50)
        best_th, val_opt_m, th_history = optimize_threshold(y_val, vprobs, target_fpr=0.005)

        val_ece, val_cal_bins = compute_ece(y_val, vprobs, n_bins=10)

        cdata["selected_threshold"] = best_th
        cdata["val_default_metrics"] = val_default_m
        cdata["val_opt_metrics"] = val_opt_m
        cdata["val_ece"] = val_ece
        cdata["val_cal_bins"] = val_cal_bins
        cdata["threshold_history"] = th_history

        print(f"\n[{cdata['name']}]")
        print(f"  Default (0.50): Acc={val_default_m['accuracy']:.4f}, Prec={val_default_m['spam_precision']:.4f}, Rec={val_default_m['spam_recall']:.4f}, F1={val_default_m['spam_f1']:.4f}, FPR={val_default_m['fpr_percentage']:.2f}%")
        print(f"  Optimal ({best_th:.2f}): Acc={val_opt_m['accuracy']:.4f}, Prec={val_opt_m['spam_precision']:.4f}, Rec={val_opt_m['spam_recall']:.4f}, F1={val_opt_m['spam_f1']:.4f}, FPR={val_opt_m['fpr_percentage']:.2f}%")
        print(f"  ROC-AUC: {val_default_m['roc_auc']:.4f}, PR-AUC: {val_default_m['pr_auc']:.4f}, Brier: {val_default_m['brier_score']:.4f}, ECE: {val_ece:.4f}")

    # 5. Final Evaluation on Test Set, Hard Ham Holdout, and Synthetic Emails (Step 4)
    print("\n" + "=" * 70)
    print("STEP 4: FINAL TEST EVALUATION (UNTOUCHED HOLDOUTS)")
    print("=" * 70)

    benchmark_summary = {}

    for ckey, cdata in candidates.items():
        model = cdata["model"]
        best_th = cdata["selected_threshold"]

        # Test set evaluation
        test_probs = model.predict_proba(X_test)[:, 1]
        test_default_m = compute_metrics(y_test, test_probs, threshold=0.50)
        test_opt_m = compute_metrics(y_test, test_probs, threshold=best_th)
        test_ece, _ = compute_ece(y_test, test_probs, n_bins=10)

        # Hard Ham Holdout evaluation (All Ham: ground truth 0)
        hh_probs = model.predict_proba(X_hard_ham)[:, 1]
        hh_default_fps = int(np.sum(hh_probs >= 0.50))
        hh_opt_fps = int(np.sum(hh_probs >= best_th))
        hh_avg_prob = float(np.mean(hh_probs))

        # Synthetic 18-email evaluation
        synth_probs = model.predict_proba(X_synth)[:, 1]
        synth_results = []
        synth_default_correct = 0
        synth_opt_correct = 0
        synth_opt_fps = 0
        synth_opt_fns = 0

        for i, s in enumerate(synth_samples):
            prob = float(synth_probs[i])
            pred_def = 1 if prob >= 0.50 else 0
            pred_opt = 1 if prob >= best_th else 0
            exp = s["expected_label"]

            if pred_def == exp:
                synth_default_correct += 1
            if pred_opt == exp:
                synth_opt_correct += 1
            else:
                if pred_opt == 1 and exp == 0:
                    synth_opt_fps += 1
                elif pred_opt == 0 and exp == 1:
                    synth_opt_fns += 1

            synth_results.append({
                "filename": s["filename"],
                "expected": s["expected_label_name"],
                "p_spam": round(prob, 4),
                "pred_default": "spam" if pred_def == 1 else "ham",
                "pred_optimal": "spam" if pred_opt == 1 else "ham",
                "correct_optimal": bool(pred_opt == exp)
            })

        cdata["test_default_metrics"] = test_default_m
        cdata["test_opt_metrics"] = test_opt_m
        cdata["test_ece"] = test_ece
        cdata["hard_ham"] = {
            "total_samples": len(hard_ham_df),
            "false_positives_default_0_50": hh_default_fps,
            "fpr_default_percentage": round((hh_default_fps / len(hard_ham_df)) * 100, 2),
            "false_positives_optimal_thresh": hh_opt_fps,
            "fpr_optimal_percentage": round((hh_opt_fps / len(hard_ham_df)) * 100, 2),
            "mean_spam_probability": round(hh_avg_prob, 4)
        }
        cdata["synthetic_eval"] = {
            "total_samples": len(synth_samples),
            "accuracy_default": round(synth_default_correct / len(synth_samples), 4),
            "accuracy_optimal": round(synth_opt_correct / len(synth_samples), 4),
            "optimal_false_positives": synth_opt_fps,
            "optimal_false_negatives": synth_opt_fns,
            "email_details": synth_results
        }

        print(f"\n--- [{cdata['name']}] Test & Holdout Results ---")
        print(f"  Test Set (at th={best_th:.2f}): Acc={test_opt_m['accuracy']:.4f}, Prec={test_opt_m['spam_precision']:.4f}, Rec={test_opt_m['spam_recall']:.4f}, F1={test_opt_m['spam_f1']:.4f}, FPR={test_opt_m['fpr_percentage']:.2f}%")
        print(f"  Hard Ham (250 challenging legitimate emails):")
        print(f"    At 0.50:  {hh_default_fps} FPs ({hh_default_fps/250*100:.1f}%) | Mean P(spam): {hh_avg_prob:.4f}")
        print(f"    At {best_th:.2f}:  {hh_opt_fps} FPs ({hh_opt_fps/250*100:.1f}%)")
        print(f"  18 Synthetic Emails (at th={best_th:.2f}): {synth_opt_correct}/18 Correct (FPs: {synth_opt_fps}, FNs: {synth_opt_fns})")

        # Save to benchmark_summary
        benchmark_summary[ckey] = {
            "name": cdata["name"],
            "params": cdata["params"],
            "selected_threshold": cdata["selected_threshold"],
            "train_time_sec": cdata["train_time_sec"],
            "pred_latency_ms": cdata["pred_latency_ms"],
            "validation": {
                "default_metrics": cdata["val_default_metrics"],
                "optimal_metrics": cdata["val_opt_metrics"],
                "ece": cdata["val_ece"]
            },
            "test": {
                "default_metrics": cdata["test_default_metrics"],
                "optimal_metrics": cdata["test_opt_metrics"],
                "ece": cdata["test_ece"]
            },
            "hard_ham_holdout": cdata["hard_ham"],
            "synthetic_18_emails": cdata["synthetic_eval"]
        }

    # 6. Save Candidate Artifacts Separately (Step 6)
    print("\n" + "=" * 70)
    print("STEP 6: SERIALIZING CANDIDATE ARTIFACTS SEPARATELY")
    print("=" * 70)

    for ckey, cdata in candidates.items():
        cand_dir = os.path.join(OUTPUT_CANDIDATES_DIR, ckey)
        os.makedirs(cand_dir, exist_ok=True)

        model_path = os.path.join(cand_dir, "model.joblib")
        tfidf_path = os.path.join(cand_dir, "tfidf.joblib")
        metadata_path = os.path.join(cand_dir, "metadata.json")

        joblib.dump(cdata["model"], model_path)
        joblib.dump(tfidf, tfidf_path)

        metadata = {
            "candidate_key": ckey,
            "algorithm": cdata["name"],
            "params": cdata["params"],
            "selected_threshold": cdata["selected_threshold"],
            "train_time_sec": cdata["train_time_sec"],
            "pred_latency_ms": cdata["pred_latency_ms"],
            "vocabulary_size": vocab_size,
            "validation_metrics": cdata["val_opt_metrics"],
            "test_metrics": cdata["test_opt_metrics"],
            "hard_ham_metrics": cdata["hard_ham"],
            "synthetic_metrics": {
                "accuracy": cdata["synthetic_eval"]["accuracy_optimal"],
                "false_positives": cdata["synthetic_eval"]["optimal_false_positives"],
                "false_negatives": cdata["synthetic_eval"]["optimal_false_negatives"]
            },
            "probability_calibration": {
                "test_brier_score": cdata["test_opt_metrics"]["brier_score"],
                "test_ece": cdata["test_ece"]
            }
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"  Saved candidate [{ckey}] in: {cand_dir}")

    # Save master benchmark JSON report
    os.makedirs(OUTPUT_REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_REPORTS_DIR, "email_model_benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)
    print(f"\nSaved comprehensive benchmark report to: {report_path}")

    # Determine recommended candidate
    print("\n" + "=" * 70)
    print("RECOMMENDATION SUMMARY")
    print("=" * 70)
    # Comparison table
    for ckey, cdata in candidates.items():
        m_test = cdata["test_opt_metrics"]
        hh = cdata["hard_ham"]
        syn = cdata["synthetic_eval"]
        th = cdata["selected_threshold"]
        print(f"{cdata['name']}:")
        print(f"  Thresh={th:.2f} | Test F1={m_test['spam_f1']:.4f} | Test FPR={m_test['fpr_percentage']:.2f}% | Hard Ham FPs={hh['false_positives_optimal_thresh']}/250 ({hh['fpr_optimal_percentage']}%) | Synth Acc={syn['accuracy_optimal']*100:.1f}%")

    print("\nPhase 2 Email Model Benchmarking completed successfully!")


if __name__ == "__main__":
    main()
