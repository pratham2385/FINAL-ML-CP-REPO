"""
train_and_export_models.py
Trains the final selected & tuned models on the train partitions and serializes them
along with vectorizers and feature schemas to outputs/models/ for production use.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

def clean_email_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def train_email_model(output_dir="outputs/models"):
    print("--- Training Final Email Spam Model (Tuned Logistic Regression C=2) ---")
    data_path = 'data/raw/enron_spam_data.csv'
    df_email = pd.read_csv(data_path)
    df_email = df_email.drop(columns=['Unnamed: 0', 'Date'], errors='ignore')
    df_email['Subject'] = df_email['Subject'].fillna('')
    df_email['Message'] = df_email['Message'].fillna('')
    df_email['email_text'] = df_email['Subject'] + ' ' + df_email['Message']
    df_email['email_text_clean'] = df_email['email_text'].apply(clean_email_text)
    df_email['label'] = df_email['Spam/Ham'].map({'ham': 0, 'spam': 1})

    X_train, X_test, y_train, y_test = train_test_split(
        df_email['email_text_clean'],
        df_email['label'],
        test_size=0.20,
        random_state=42,
        stratify=df_email['label']
    )

    print(f"Fitting TfidfVectorizer on {len(X_train)} training emails...")
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_df=0.95, sublinear_tf=True)
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    print("Fitting LogisticRegression(C=2, max_iter=1000)...")
    email_model = LogisticRegression(C=2, max_iter=1000, random_state=42)
    email_model.fit(X_train_tfidf, y_train)

    # Evaluate on test set
    y_pred = email_model.predict(X_test_tfidf)
    y_prob = email_model.predict_proba(X_test_tfidf)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label=1)
    rec = recall_score(y_test, y_pred, pos_label=1)
    f1 = f1_score(y_test, y_pred, pos_label=1)
    auc = roc_auc_score(y_test, y_prob)

    print(f"Email Test Results -> Acc: {acc:.6f}, Prec: {prec:.6f}, Rec: {rec:.6f}, F1: {f1:.6f}, AUC: {auc:.6f}")

    # Serialize artifacts
    model_path = os.path.join(output_dir, 'email_model.joblib')
    tfidf_path = os.path.join(output_dir, 'email_tfidf.joblib')
    joblib.dump(email_model, model_path, compress=3)
    joblib.dump(tfidf, tfidf_path, compress=3)
    print(f"Saved email model to {model_path}")
    print(f"Saved email TF-IDF vectorizer to {tfidf_path}")

    return {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "roc_auc": float(auc)
    }

def train_url_model(output_dir="outputs/models"):
    print("\n--- Training Final URL Phishing Model (Tuned Random Forest) ---")
    data_path = 'data/raw/PhiUSIIL_Phishing_URL_Dataset.csv'
    df_url = pd.read_csv(data_path)

    deployable_url_features = [
        'URLLength', 'DomainLength', 'IsDomainIP', 'NoOfSubDomain', 'HasObfuscation',
        'NoOfObfuscatedChar', 'ObfuscationRatio', 'NoOfLettersInURL', 'LetterRatioInURL',
        'NoOfDegitsInURL', 'DegitRatioInURL', 'NoOfEqualsInURL', 'NoOfQMarkInURL',
        'NoOfAmpersandInURL', 'NoOfOtherSpecialCharsInURL', 'SpacialCharRatioInURL',
        'IsHTTPS', 'TLDLength'
    ]

    X = df_url[deployable_url_features]
    y = df_url['label'] # 0=Phishing, 1=Legitimate

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"Fitting RandomForest on {len(X_train)} samples with 18 features (n_estimators=400, max_depth=25)...")
    url_model = RandomForestClassifier(
        n_estimators=400,
        max_depth=25,
        max_features='sqrt',
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1
    )
    url_model.fit(X_train, y_train)

    # Evaluate on test set (Class 0 = Phishing)
    y_pred = url_model.predict(X_test)
    y_prob = url_model.predict_proba(X_test)[:, 0] # probability of phishing (class 0)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label=0)
    rec = recall_score(y_test, y_pred, pos_label=0)
    f1 = f1_score(y_test, y_pred, pos_label=0)
    auc = roc_auc_score(1 - y_test, y_prob)

    print(f"URL Test Results (Phishing pos_label=0) -> Acc: {acc:.6f}, Prec: {prec:.6f}, Rec: {rec:.6f}, F1: {f1:.6f}, AUC: {auc:.6f}")

    # Serialize artifacts
    model_path = os.path.join(output_dir, 'url_model.joblib')
    joblib.dump(url_model, model_path, compress=3)
    print(f"Saved URL model to {model_path}")

    return {
        "accuracy": float(acc),
        "phishing_precision": float(prec),
        "phishing_recall": float(rec),
        "phishing_f1": float(f1),
        "roc_auc": float(auc),
        "features": deployable_url_features
    }

def main():
    os.makedirs("outputs/models", exist_ok=True)
    email_metrics = train_email_model("outputs/models")
    url_metrics = train_url_model("outputs/models")

    metadata = {
        "email_model": {
            "algorithm": "LogisticRegression(C=2, max_iter=1000, random_state=42)",
            "vectorizer": "TfidfVectorizer(ngram_range=(1,2), min_df=5, max_df=0.95, sublinear_tf=True)",
            "label_mapping": {"ham": 0, "spam": 1},
            "metrics": email_metrics
        },
        "url_model": {
            "algorithm": "RandomForestClassifier(n_estimators=400, max_depth=25, max_features='sqrt', min_samples_leaf=1, random_state=42)",
            "label_mapping": {"phishing": 0, "legitimate": 1},
            "feature_order": url_metrics["features"],
            "metrics": {k: v for k, v in url_metrics.items() if k != "features"}
        }
    }

    meta_path = "outputs/models/model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata saved to {meta_path}")
    print("SUCCESS: All models and metadata serialized successfully!")

if __name__ == '__main__':
    main()
