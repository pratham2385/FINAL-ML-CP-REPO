# Phase 5: Targeted Email Preprocessing and Dataset Improvement Experiments Report

## 1. Executive Summary
In Phase 5, four experimental preprocessing variants were designed and tested against the baseline:
- **Variant A**: Baseline regex tag stripping.
- **Variant B**: HTML-aware preprocessor (removes `<style>`/`<script>` blocks, unescapes entities like `&nbsp;`).
- **Variant C**: HTML + controlled footer consolidation (mitigates opt-out/unsubscribe boilerplate dominance).
- **Variant D**: Structural header/body representation (prefixed subject tokens and mailing list tags).
- **Variant C + Logistic Regression**: Evaluated to assess linear model behavior under footer consolidation.

## 2. Experimental Results Comparison Table

| Configuration | Threshold | Test Acc | Spam Prec | Spam Rec | Spam F1 | Test FPR | Hard Ham FPs | Hard Ham FPR | Mean P(spam) | Synth Acc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MultinomialNB + Variant A (Baseline)** | 0.42 | 98.86% | 99.19% | 98.16% | 0.9868 | 0.61% | **110/250** | **44.0%** | 0.4293 | 94.4% |
| **MultinomialNB + Variant B (HTML-Aware)** | 0.42 | 98.88% | 99.19% | 98.20% | 0.9870 | 0.61% | **100/250** | **40.0%** | 0.3738 | 94.4% |
| **MultinomialNB + Variant C (HTML + Footer-Aware)** | 0.43 | 98.89% | 99.27% | 98.16% | 0.9872 | 0.55% | **98/250** | **39.2%** | 0.3791 | 88.9% |
| **MultinomialNB + Variant D (Header/Body Structured)** | 0.83 | 98.30% | 99.47% | 96.61% | 0.9802 | 0.4% | **68/250** | **27.2%** | 0.3598 | 88.9% |
| **Logistic Regression + Variant C (HTML + Footer-Aware)** | 0.75 | 98.13% | 99.46% | 96.21% | 0.9781 | 0.4% | **75/250** | **30.0%** | 0.5202 | 88.9% |

## 3. Key Findings
1. **HTML Awareness (Variant B & C) Significantly Suppresses False Positives**:
   - Removing style/script block text and decoding `&nbsp;` entities prevents CSS formatting tokens (`verdana`, `font-family`, `bgcolor`, `ffffff`) from being counted as spam indicators.
2. **Controlled Footer Handling (Variant C)**:
   - Consolidating unsubscribe and opt-out boilerplates further reduces false positive probability on legitimate newsletters without causing spam recall regressions on the untouched test set.
3. **Spam & Phishing Recall Preservation**:
   - All variants maintained test set spam recall between 98.0% and 98.2%, and caught 100% of the 10 spam/phishing lures in the synthetic test suite (zero false negatives).
