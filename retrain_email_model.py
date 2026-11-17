"""
retrain_email_model.py
Retrains and evaluates the email spam models (Logistic Regression C=2 and LinearSVC)
on the corrected Enron spam dataset (data/raw/enron_spam_data.csv).
Serializes the selected model and TF-IDF vectorizer to outputs/models/.
"""

import os
import re
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

DATA_PATH = "data/raw/enron_spam_data.csv"
OUTPUT_DIR = "outputs/models"
METADATA_PATH = os.path.join(OUTPUT_DIR, "model_metadata.json")

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("=" * 70)
    print("STEP 1: LOADING & PREPROCESSING CORRECTED ENRON DATASET")
    print("=" * 70)
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    print("Class distribution:")
    print(df['Spam/Ham'].value_counts())

    df['Subject'] = df['Subject'].fillna('')
    df['Message'] = df['Message'].fillna('')
    df['email_text'] = df['Subject'] + ' ' + df['Message']
    df['email_text_clean'] = df['email_text'].apply(clean_text)
    df['label'] = df['Spam/Ham'].map({'ham': 0, 'spam': 1})

    # Stratified 80/20 train/test split
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        df['email_text_clean'],
        df['label'],
        df.index,
        test_size=0.20,
        random_state=42,
        stratify=df['label']
    )

    print(f"\nTrain set: {len(X_train)} samples ({y_train.sum()} spam, {(y_train == 0).sum()} ham)")
    print(f"Test set:  {len(X_test)} samples ({y_test.sum()} spam, {(y_test == 0).sum()} ham)")

    # TF-IDF fit strictly on training set
    print("\nFitting TfidfVectorizer(ngram_range=(1,2), min_df=5, max_df=0.95, sublinear_tf=True)...")
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_df=0.95, sublinear_tf=True)
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)
    print(f"Vocabulary size: {len(tfidf.vocabulary_)} terms")

    # -------------------------------------------------------------
    # STEP 2: TRAINING MODELS
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 2: TRAINING LOGISTIC REGRESSION (C=2) AND LINEARSVC")
    print("=" * 70)

    # 1. Logistic Regression
    print("Training Logistic Regression (C=2, max_iter=1000, random_state=42)...")
    lr_model = LogisticRegression(C=2, max_iter=1000, random_state=42)
    lr_model.fit(X_train_tfidf, y_train)

    # 2. LinearSVC
    print("Training LinearSVC (random_state=42)...")
    svm_model = LinearSVC(random_state=42)
    svm_model.fit(X_train_tfidf, y_train)

    # -------------------------------------------------------------
    # STEP 3: EVALUATION ON UNTOUCHED TEST SET
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 3: TEST SET EVALUATION METRICS")
    print("=" * 70)

    def evaluate_model(name, model, X_t, y_t):
        preds = model.predict(X_t)
        acc = accuracy_score(y_t, preds)
        prec = precision_score(y_t, preds, pos_label=1)
        rec = recall_score(y_t, preds, pos_label=1)
        f1 = f1_score(y_t, preds, pos_label=1)
        cm = confusion_matrix(y_t, preds) # [[TN, FP], [FN, TP]]

        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_t)[:, 1]
            auc = roc_auc_score(y_t, probs)
        elif hasattr(model, "decision_function"):
            scores = model.decision_function(X_t)
            auc = roc_auc_score(y_t, scores)
        else:
            auc = None

        return {
            "name": name,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc,
            "confusion_matrix": cm.tolist(),
            "preds": preds
        }

    lr_eval = evaluate_model("Logistic Regression (C=2)", lr_model, X_test_tfidf, y_test)
    svm_eval = evaluate_model("LinearSVC", svm_model, X_test_tfidf, y_test)

    print(f"\n{'Metric':<20} | {'Logistic Regression (C=2)':<26} | {'LinearSVC':<20}")
    print("-" * 72)
    print(f"{'Accuracy':<20} | {lr_eval['accuracy']:.6f}                   | {svm_eval['accuracy']:.6f}")
    print(f"{'Spam Precision':<20} | {lr_eval['precision']:.6f}                   | {svm_eval['precision']:.6f}")
    print(f"{'Spam Recall':<20} | {lr_eval['recall']:.6f}                   | {svm_eval['recall']:.6f}")
    print(f"{'Spam F1-Score':<20} | {lr_eval['f1']:.6f}                   | {svm_eval['f1']:.6f}")
    print(f"{'ROC-AUC':<20} | {lr_eval['roc_auc']:.6f}                   | {svm_eval['roc_auc']:.6f}")

    print("\nConfusion Matrices:")
    for ev in [lr_eval, svm_eval]:
        cm = ev['confusion_matrix']
        print(f"\n{ev['name']}:")
        print(f"  True Ham  (TN): {cm[0][0]:<5} | False Spam (FP): {cm[0][1]:<5}")
        print(f"  False Ham (FN): {cm[1][0]:<5} | True Spam  (TP): {cm[1][1]:<5}")

    # -------------------------------------------------------------
    # STEP 4: ERROR ANALYSIS (Logistic Regression)
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 4: ERROR ANALYSIS ON TEST SET (Logistic Regression C=2)")
    print("=" * 70)

    lr_preds = lr_eval['preds']
    test_indices = idx_test.to_numpy()
    test_y_arr = y_test.to_numpy()

    fp_mask = (test_y_arr == 0) & (lr_preds == 1)
    fn_mask = (test_y_arr == 1) & (lr_preds == 0)

    fp_indices = test_indices[fp_mask]
    fn_indices = test_indices[fn_mask]

    print(f"Total False Positives (Ham predicted as Spam): {len(fp_indices)} / { (test_y_arr == 0).sum() }")
    print(f"Total False Negatives (Spam predicted as Ham): {len(fn_indices)} / { (test_y_arr == 1).sum() }")

    print("\nSample False Positives (Ham classified as Spam):")
    for idx in fp_indices[:3]:
        row = df.loc[idx]
        print(f"  [ID {idx}] Subject: {row['Subject']}")
        print(f"       Preview: {row['Message'][:120]}...\n")

    print("Sample False Negatives (Spam classified as Ham):")
    for idx in fn_indices[:3]:
        row = df.loc[idx]
        print(f"  [ID {idx}] Subject: {row['Subject']}")
        print(f"       Preview: {row['Message'][:120]}...\n")

    # -------------------------------------------------------------
    # STEP 5: MODEL SELECTION & ARTIFACT SERIALIZATION
    # -------------------------------------------------------------
    print("=" * 70)
    print("STEP 5: MODEL SELECTION & SERIALIZATION")
    print("=" * 70)
    # Selected Model: Logistic Regression (C=2)
    # Reason: Provides well-calibrated posterior probabilities (predict_proba)
    # necessary for application UI confidence scores and risk thresholding,
    # with comparable F1 performance to LinearSVC.
    print("Selected Model: Tuned Logistic Regression (C=2)")
    print("Reason: Delivers natively calibrated probabilities (predict_proba) for risk scoring with strong F1.")

    model_path = os.path.join(OUTPUT_DIR, "email_model.joblib")
    tfidf_path = os.path.join(OUTPUT_DIR, "email_tfidf.joblib")

    joblib.dump(lr_model, model_path, compress=3)
    joblib.dump(tfidf, tfidf_path, compress=3)
    print(f"Saved email model to: {model_path}")
    print(f"Saved email TF-IDF to: {tfidf_path}")

    # Update metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata["email_model"] = {
        "algorithm": "LogisticRegression(C=2, max_iter=1000, random_state=42)",
        "vectorizer": "TfidfVectorizer(ngram_range=(1,2), min_df=5, max_df=0.95, sublinear_tf=True)",
        "dataset": {
            "source": "Enron Spam Dataset (corrected, non-corrupted benchmark)",
            "total_rows": int(df.shape[0]),
            "spam_rows": int(df['label'].sum()),
            "ham_rows": int((df['label'] == 0).sum()),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test))
        },
        "label_mapping": {"ham": 0, "spam": 1},
        "metrics": {
            "accuracy": float(lr_eval["accuracy"]),
            "precision": float(lr_eval["precision"]),
            "recall": float(lr_eval["recall"]),
            "f1": float(lr_eval["f1"]),
            "roc_auc": float(lr_eval["roc_auc"]),
            "confusion_matrix": lr_eval["confusion_matrix"]
        },
        "alternative_linear_svc": {
            "accuracy": float(svm_eval["accuracy"]),
            "precision": float(svm_eval["precision"]),
            "recall": float(svm_eval["recall"]),
            "f1": float(svm_eval["f1"]),
            "roc_auc": float(svm_eval["roc_auc"]),
            "confusion_matrix": svm_eval["confusion_matrix"]
        }
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Updated metadata in: {METADATA_PATH}")

    # -------------------------------------------------------------
    # STEP 6: VALIDATION OF SERIALIZED ARTIFACTS
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 6: VALIDATING RELOADED ARTIFACTS ON SAMPLE EMAILS")
    print("=" * 70)
    from src.models.predictor import EmailPredictor
    predictor = EmailPredictor(models_dir=OUTPUT_DIR)

    test_samples = [
        {
            "name": "Legitimate Corporate Sync",
            "subject": "Q3 Budget Review and Strategy Meeting",
            "message": "Hi team, please find attached the revised budget draft for next quarter. Let me know if you have questions before our 2 PM call."
        },
        {
            "name": "Generic Scam / Cash Prize",
            "subject": "CONGRATULATIONS! You have won $1,000,000 Cash Prize!",
            "message": "Claim your lottery prize immediately! 100% guaranteed jackpot payout. Reply with your full bank account details to receive funds today!"
        },
        {
            "name": "Pharmaceutical / Urgent Product Spam",
            "subject": "Discounted prescriptions online - fast shipping",
            "message": "Order generic viagra and cialis without doctor prescription. Best quality pills delivered overnight directly to your door."
        },
        {
            "name": "Credential Phishing Subject",
            "subject": "Urgent: Your account has been suspended",
            "message": "Dear customer, we detected unauthorized activity on your account. Please verify your login credentials immediately to avoid termination."
        }
    ]

    for sample in test_samples:
        res = predictor.predict(sample["subject"], sample["message"])
        print(f"Sample: {sample['name']}")
        print(f"  Subject: '{sample['subject']}'")
        print(f"  Predicted Label: {res['label']} | Spam Prob: {res['spam_probability']:.4f} | Conf: {res['confidence_percent']}%")
        print()

    print("ALL RETRAINING & VALIDATION STEPS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    main()
