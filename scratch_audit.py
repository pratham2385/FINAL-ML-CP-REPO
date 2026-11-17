"""
scratch_audit.py
Performs the independent research-validity audit on both Email and URL datasets
without modifying or retraining any production model artifacts.
"""

import os
import re
import json
import joblib
import pandas as pd
import numpy as np
from collections import Counter
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from src.features.email_preprocessor import preprocess_email_text
from src.features.url_feature_extractor import DEPLOYABLE_URL_FEATURES

def audit_email():
    print("=" * 70)
    print("PART 1: EMAIL SPAM RESEARCH-VALIDITY AUDIT")
    print("=" * 70)
    
    enron_path = "data/raw/enron_spam_data.csv"
    df = pd.read_csv(enron_path)
    df['Subject'] = df['Subject'].fillna('')
    df['Message'] = df['Message'].fillna('')
    df['email_text'] = df['Subject'] + ' ' + df['Message']
    df['clean_text'] = df['email_text'].apply(preprocess_email_text)
    df['label'] = df['Spam/Ham'].map({'ham': 0, 'spam': 1})
    
    # 1. Exact duplicates in whole dataset
    total_rows = len(df)
    exact_text_dups = df.duplicated(subset=['email_text']).sum()
    clean_text_dups = df.duplicated(subset=['clean_text']).sum()
    print(f"Total email rows: {total_rows}")
    print(f"Exact raw text duplicates: {exact_text_dups} ({exact_text_dups/total_rows*100:.2f}%)")
    print(f"Clean text duplicates: {clean_text_dups} ({clean_text_dups/total_rows*100:.2f}%)")
    
    # 2. Check 80/20 random split (seed 42)
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        df['clean_text'], df['label'], df.index,
        test_size=0.20, random_state=42, stratify=df['label']
    )
    
    train_texts = set(X_train)
    overlap_exact = X_test.isin(train_texts).sum()
    print(f"\nRandom 80/20 Split (seed 42):")
    print(f"  Test samples exactly matching a training sample: {overlap_exact} / {len(X_test)} ({overlap_exact/len(X_test)*100:.2f}%)")
    
    # 3. Subject thread overlap (stripping re:, fw:, etc.)
    def base_subject(subj):
        s = subj.lower()
        s = re.sub(r'^(re\s*:\s*|fw\s*:\s*|fwd\s*:\s*)+', '', s)
        s = re.sub(r'[^a-z0-9\s]', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()
    
    df['base_subject'] = df['Subject'].apply(base_subject)
    train_base_subjs = set(df.loc[idx_train, 'base_subject'])
    test_base_subjs = df.loc[idx_test, 'base_subject']
    overlap_subj = test_base_subjs.isin(train_base_subjs).sum()
    print(f"  Test samples sharing base subject/thread with train: {overlap_subj} / {len(X_test)} ({overlap_subj/len(X_test)*100:.2f}%)")
    
    # 4. Enron corporate artifact analysis
    corporate_enron_terms = ['enron', 'ect', 'vince', 'hou', 'kaminski', 'houston', 'deal', 'corp', 'gas', 'power']
    ham_texts = df[df['label'] == 0]['clean_text']
    spam_texts = df[df['label'] == 1]['clean_text']
    
    print("\nDataset Artifact Analysis (Enron internal tokens in Ham vs Spam):")
    for term in corporate_enron_terms:
        ham_has = ham_texts.str.contains(r'\b' + term + r'\b', regex=True).mean() * 100
        spam_has = spam_texts.str.contains(r'\b' + term + r'\b', regex=True).mean() * 100
        print(f"  Word '{term:10}': Present in {ham_has:5.1f}% of HAM vs {spam_has:5.1f}% of SPAM")
        
    # 5. Evaluate existing model on Group-Disjoint Test Set (grouped by base_subject)
    # First, load existing production model
    email_model = joblib.load("outputs/models/email_model.joblib")
    email_tfidf = joblib.load("outputs/models/email_tfidf.joblib")
    
    # Performance on standard random test set
    X_test_tfidf = email_tfidf.transform(X_test)
    y_pred_rand = email_model.predict(X_test_tfidf)
    rand_acc = accuracy_score(y_test, y_pred_rand)
    rand_f1 = f1_score(y_test, y_pred_rand)
    print(f"\nExisting Model on Standard Random Test Set:")
    print(f"  Accuracy: {rand_acc*100:.2f}%, Spam F1: {rand_f1*100:.2f}%")
    
    # Group-Disjoint Split by Base Subject
    # Non-empty base subjects as groups
    df['group'] = df['base_subject'].apply(lambda x: x if len(x) > 3 else f"single_{np.random.randint(1e9)}")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_grp_idx, test_grp_idx = next(gss.split(df, groups=df['group']))
    
    # Check disjointness
    train_grps = set(df.iloc[train_grp_idx]['group'])
    test_grps = set(df.iloc[test_grp_idx]['group'])
    assert len(train_grps.intersection(test_grps)) == 0, "Groups not disjoint!"
    
    df_test_grp = df.iloc[test_grp_idx]
    X_test_grp_tfidf = email_tfidf.transform(df_test_grp['clean_text'])
    y_test_grp = df_test_grp['label']
    y_pred_grp = email_model.predict(X_test_grp_tfidf)
    
    grp_acc = accuracy_score(y_test_grp, y_pred_grp)
    grp_f1 = f1_score(y_test_grp, y_pred_grp)
    grp_prec = precision_score(y_test_grp, y_pred_grp)
    grp_rec = recall_score(y_test_grp, y_pred_grp)
    print(f"\nExisting Model Evaluated on Group-Disjoint Test Set (no thread/subject leakage):")
    print(f"  Test size: {len(df_test_grp)} (Spam: {y_test_grp.sum()}, Ham: {(y_test_grp==0).sum()})")
    print(f"  Accuracy:       {grp_acc*100:.2f}%")
    print(f"  Spam Precision: {grp_prec*100:.2f}%")
    print(f"  Spam Recall:    {grp_rec*100:.2f}%")
    print(f"  Spam F1-Score:  {grp_f1*100:.2f}%")
    
    # Also evaluate on Deduplicated Test Set (removing any test samples whose clean_text appeared in train)
    leak_free_mask = ~X_test.isin(train_texts)
    X_test_dedup = X_test[leak_free_mask]
    y_test_dedup = y_test[leak_free_mask]
    X_test_dedup_tfidf = email_tfidf.transform(X_test_dedup)
    y_pred_dedup = email_model.predict(X_test_dedup_tfidf)
    
    dedup_acc = accuracy_score(y_test_dedup, y_pred_dedup)
    dedup_f1 = f1_score(y_test_dedup, y_pred_dedup)
    print(f"\nExisting Model on De-duplicated Test Set (exact duplicates removed, n={len(X_test_dedup)}):")
    print(f"  Accuracy: {dedup_acc*100:.2f}%, Spam F1: {dedup_f1*100:.2f}%")
    
    return {
        "rand_acc": rand_acc,
        "rand_f1": rand_f1,
        "grp_acc": grp_acc,
        "grp_f1": grp_f1,
        "dedup_acc": dedup_acc,
        "dedup_f1": dedup_f1,
        "exact_dups": clean_text_dups,
        "overlap_exact": overlap_exact,
        "overlap_subj": overlap_subj
    }

def audit_url():
    print("\n" + "=" * 70)
    print("PART 2: PHIUSIIL URL RESEARCH-VALIDITY AUDIT")
    print("=" * 70)
    
    url_path = "data/raw/PhiUSIIL_Phishing_URL_Dataset.csv"
    df = pd.read_csv(url_path)
    total_urls = len(df)
    print(f"Total URL rows: {total_urls}")
    
    # 1. Exact duplicate URLs
    url_dups = df.duplicated(subset=['URL']).sum()
    print(f"Exact duplicate URLs: {url_dups} ({url_dups/total_urls*100:.2f}%)")
    
    # 2. Hostname/Domain Overlap
    num_unique_domains = df['Domain'].nunique()
    print(f"Unique Domains: {num_unique_domains} across {total_urls} URLs")
    print(f"Top 5 most frequent domains in dataset:")
    print(df['Domain'].value_counts().head(5))
    
    # Standard 80/20 random split
    X = df[DEPLOYABLE_URL_FEATURES]
    y = df['label'] # 0=phishing, 1=legitimate
    
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.20, random_state=42, stratify=y
    )
    
    train_domains = set(df.loc[idx_train, 'Domain'])
    test_domains = set(df.loc[idx_test, 'Domain'])
    domain_overlap = test_domains.intersection(train_domains)
    test_urls_with_train_domain = df.loc[idx_test, 'Domain'].isin(train_domains).sum()
    print(f"\nRandom 80/20 Split (seed 42):")
    print(f"  Test domains already in train: {len(domain_overlap)} / {len(test_domains)} ({len(domain_overlap)/len(test_domains)*100:.2f}%)")
    print(f"  Test URLs belonging to a domain seen in train: {test_urls_with_train_domain} / {len(X_test)} ({test_urls_with_train_domain/len(X_test)*100:.2f}%)")
    
    # 3. Structural Collection Artifacts & Label Confounding
    print("\nCollection Artifact & Label Confounding Analysis:")
    # Check IsHTTPS by class
    legit_https = (df[df['label'] == 1]['IsHTTPS'] == 1).mean() * 100
    phish_https = (df[df['label'] == 0]['IsHTTPS'] == 1).mean() * 100
    print(f"  IsHTTPS == 1: {legit_https:.2f}% of Legitimate vs {phish_https:.2f}% of Phishing")
    
    # Check URL structure: has path / query / slash count
    df['has_path'] = df['URL'].apply(lambda u: len(re.sub(r'^https?://[^/]+', '', u).strip('/')) > 0)
    legit_has_path = df[df['label'] == 1]['has_path'].mean() * 100
    phish_has_path = df[df['label'] == 0]['has_path'].mean() * 100
    print(f"  Has URL Path/Parameters: {legit_has_path:.2f}% of Legitimate vs {phish_has_path:.2f}% of Phishing")
    
    # Average URL Length
    legit_len = df[df['label'] == 1]['URLLength'].mean()
    phish_len = df[df['label'] == 0]['URLLength'].mean()
    print(f"  Mean URLLength: {legit_len:.1f} (Legitimate) vs {phish_len:.1f} (Phishing)")
    
    # 4. Evaluate existing model on Random Split vs Domain-Disjoint Split
    url_model = joblib.load("outputs/models/url_model.joblib")
    
    # Random split performance
    y_pred_rand = url_model.predict(X_test)
    rand_acc = accuracy_score(y_test, y_pred_rand)
    rand_phish_f1 = f1_score(y_test, y_pred_rand, pos_label=0)
    rand_phish_rec = recall_score(y_test, y_pred_rand, pos_label=0)
    print(f"\nExisting URL Model on Standard Random Test Set:")
    print(f"  Accuracy: {rand_acc*100:.2f}%, Phishing F1: {rand_phish_f1*100:.2f}%, Phishing Recall: {rand_phish_rec*100:.2f}%")
    
    # Domain-Disjoint Split
    # Group by Domain so no domain in train ever appears in test!
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_grp_idx, test_grp_idx = next(gss.split(df, groups=df['Domain']))
    
    df_test_grp = df.iloc[test_grp_idx]
    X_test_grp = df_test_grp[DEPLOYABLE_URL_FEATURES]
    y_test_grp = df_test_grp['label']
    
    y_pred_grp = url_model.predict(X_test_grp)
    grp_acc = accuracy_score(y_test_grp, y_pred_grp)
    grp_phish_f1 = f1_score(y_test_grp, y_pred_grp, pos_label=0)
    grp_phish_rec = recall_score(y_test_grp, y_pred_grp, pos_label=0)
    grp_phish_prec = precision_score(y_test_grp, y_pred_grp, pos_label=0)
    
    print(f"\nExisting URL Model Evaluated on Domain-Disjoint Test Set (Zero Domain Overlap):")
    print(f"  Test URLs: {len(X_test_grp)} across {df_test_grp['Domain'].nunique()} unique domains")
    print(f"  Phishing samples: {(y_test_grp == 0).sum()}, Legitimate samples: {(y_test_grp == 1).sum()}")
    print(f"  Accuracy:           {grp_acc*100:.2f}%")
    print(f"  Phishing Precision: {grp_phish_prec*100:.2f}%")
    print(f"  Phishing Recall:    {grp_phish_rec*100:.2f}%")
    print(f"  Phishing F1-Score:  {grp_phish_f1*100:.2f}%")
    
    return {
        "rand_acc": rand_acc,
        "rand_phish_f1": rand_phish_f1,
        "grp_acc": grp_acc,
        "grp_phish_f1": grp_phish_f1,
        "grp_phish_rec": grp_phish_rec,
        "grp_phish_prec": grp_phish_prec,
        "test_urls_with_train_domain": test_urls_with_train_domain,
        "legit_https": legit_https,
        "phish_https": phish_https,
        "legit_has_path": legit_has_path,
        "phish_has_path": phish_has_path
    }

if __name__ == '__main__':
    audit_email()
    audit_url()
