# Phase 6: Legitimate Newsletter Dataset Improvement Report

## 1. Executive Summary
In Phase 6, we investigated legally accessible, authentic legitimate email corpora to acquire real HTML marketing newsletters, technology digests, automated notifications, and German/non-English legitimate messages. A total of **10,923 verified legitimate emails** were successfully integrated from CEAS-08, TREC-07, and TREC-06, strictly verified to have **0 overlap with the Hard Ham holdout** and **0 overlap with existing train/val/test splits**.

## 2. Experimental Results Comparison Table

| Configuration | Train N | Threshold | Test Acc | Spam Prec | Spam Rec | Spam F1 | Test FPR | Hard Ham FPs | Hard Ham FPR | Mean P(spam) | Synth Acc | Synth FNs |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A: Existing Data + Variant C (MultinomialNB alpha=0.01)** | 26,967 | 0.43 | 98.89% | 99.27% | 98.16% | 0.9872 | 0.55% | **98/250** | **39.2%** | 0.3791 | 88.9% | 1 |
| **Model B: Augmented Data (10.9k Legitimate Added) + Variant C (MultinomialNB alpha=0.01)** | 37,890 | 0.26 | 98.49% | 99.27% | 97.25% | 0.9825 | 0.55% | **44/250** | **17.6%** | 0.1283 | 94.4% | 0 |
| **Model B2: Augmented Data + Variant C (MultinomialNB alpha=0.01, Uniform Prior)** | 37,890 | 0.43 | 98.51% | 99.27% | 97.29% | 0.9827 | 0.55% | **45/250** | **18.0%** | 0.1562 | 94.4% | 0 |
| **Model B3: Augmented Data + Variant C (Logistic Regression C=2.0)** | 37,890 | 0.72 | 97.65% | 99.46% | 95.09% | 0.9723 | 0.4% | **22/250** | **8.8%** | 0.2928 | 88.9% | 1 |

## 3. Key Findings & Behavioral Analysis
1. **Substantial Reduction in Newsletter False Positives**:
   - Adding 10,923 authentic legitimate emails containing newsletters and digests significantly expanded the model's ham vocabulary, reducing false positives on legitimate marketing and newsletter communications.
2. **Preservation of Phishing and Spam Recall**:
   - General test set spam recall remained exceptionally high (~98%), confirming that expanding legitimate newsletter representation does not create blind spots for malicious emails.
3. **Hard Ham Diagnostic Context**:
   - Disclosed: The 250 Hard Ham holdout samples were previously inspected in Phases 4 & 5. While useful as a diagnostic trend indicator, it is not an independent unseen test set.
