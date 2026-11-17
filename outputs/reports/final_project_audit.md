# Final Project Audit and System Documentation

**Project Name**: Machine Learning-Based Email Spam and Phishing Detection System  
**System Version**: 2.0.0-production  
**Date of Audit**: November 17, 2026  
**Audit Scope**: End-to-end evaluation of Email and URL detection models, preprocessing pipelines, FastAPI REST APIs, PostgreSQL database persistence, React frontend interface, and security/reliability hardening.

---

## 1. Project Architecture

The system operates on a decoupled **Dual-Representation Pipeline Architecture** designed to analyze incoming electronic mail and standalone web hyperlinks across two synchronized inspection streams:

```
                                      +------------------------------------+
                                      |          INCOMING INPUT            |
                                      |   (Plain Text, HTML, .eml, URL)    |
                                      +-----------------+------------------+
                                                        |
                            +---------------------------+---------------------------+
                            |                                                       |
                            v                                                       v
            +-------------------------------+                       +-------------------------------+
            |           STREAM 1            |                       |           STREAM 2            |
            |     Embedded URL Extractor    |                       |    Variant C Preprocessor     |
            |   (Regex + BeautifulSoup href)|                       |  (HTML clean, opt-out footer) |
            +---------------+---------------+                       +---------------+---------------+
                            |                                                       |
                            v                                                       v
            +-------------------------------+                       +-------------------------------+
            |      18-Feature Lexical       |                       |       TF-IDF Vectorizer       |
            |       URL Transformer         |                       |     (268,754 n-grams, 1-2)    |
            +---------------+---------------+                       +---------------+---------------+
                            |                                                       |
                            v                                                       v
            +-------------------------------+                       +-------------------------------+
            |    URL Phishing Classifier    |                       |    Email Spam Classifier      |
            |   (Tuned Random Forest, 400)  |                       | (MultinomialNB, alpha=0.01)   |
            +---------------+---------------+                       +---------------+---------------+
                            |                                                       |
                            +---------------------------+---------------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |      COMPOSITE RISK ENGINE         |
                                      |   (Threat Level, Verdict, Action)  |
                                      +-----------------+------------------+
                                                        |
                            +---------------------------+---------------------------+
                            |                                                       |
                            v                                                       v
            +-------------------------------+                       +-------------------------------+
            |      PostgreSQL Database      |                       |       React / Vite GUI        |
            |    (Audit History Logging)    |                       |      (Real-Time Insights)     |
            +-------------------------------+                       +-------------------------------+
```

---

## 2. Dataset Sources & Preprocessing Pipelines

### A. Email Subsystem Datasets
The email model is trained on a unified multi-corpus dataset combining six public email repositories:

| Corpus | Original Source | Samples (Ham / Spam) | Role in System |
| :--- | :--- | :---: | :--- |
| **Enron Spam Corpus** | Enron executive mailbox archive | 15,269 / 11,698 (in train) | Foundation corporate communications & raw spam |
| **SpamAssassin Public Corpus** | Apache SpamAssassin (easy_ham 1 & 2, spam 1 & 2) | 3,948 (in train) | Real-world personal inboxes & spam attacks |
| **Ling-Spam Corpus** | Academic linguistics mailing list | 2,011 (in train) | Specialized professional listserv messages |
| **CEAS 2008 Live Challenge** | Conference on Email and Anti-Spam | 3,515 ham | Commercial newsletters, transactional notifications |
| **TREC 2007 Public Corpus** | NIST / University of Waterloo | 4,918 ham | Real-world academic/enterprise email streams & HTML |
| **TREC 2006 Public Corpus** | NIST / University of Waterloo | 2,490 ham | Technology bulletins & automated alerts |
| **Total Clean Samples** | — | **49,698 emails** | Split into Train (37,890), Val (5,779), Test (5,779) |

### B. Standardized Preprocessing (Variant C)
Inference and training share the exact same implementation in `src/features/email_preprocessor.py`:
1. **Script and Style Stripping**: Deletes `<script>` and `<style>` blocks including all internal CSS and JS code via regex (`re.DOTALL`).
2. **Comment Stripping**: Removes HTML comments (`<!--...-->`).
3. **Block Spacing**: Replaces closing block tags (`<br>`, `<p>`, `<div>`, `<tr>`, `<td>`, `<li>`, `<h1-6>`) with single whitespace to prevent word concatenation.
4. **Entity Decoding**: Uses `html.unescape()` to resolve `&nbsp;`, `&amp;`, and Unicode escape sequences into standard characters.
5. **Controlled Opt-Out Consolidation**: Consolidates repetitive CAN-SPAM and subscription boilerplate text into the canonical token `newsletter_optout_boilerplate`.
6. **URL & Punctuation Cleanup**: Strips URLs, removes non-alphanumeric punctuation, lowercases, and normalizes whitespace.

### C. URL Subsystem Dataset
- **PhiUSIIL Phishing URL Dataset**: 235,795 URLs covering 134,850 legitimate web domains and 100,945 confirmed malicious phishing targets across diverse categories.

---

## 3. Model Training & Evaluation Methodology

- **Training vs. Validation vs. Test Discipline**:
  - Vectorizers and scalers were fit **strictly on training splits**.
  - Decision thresholds were optimized **strictly on the validation split** (`val_emails.parquet`) targeting $\text{FPR} \le 0.5\%$.
  - Evaluation was performed on an untouched, blind **test split** (`test_emails.parquet`, 5,779 samples).
- **Holdout Separation**:
  - The 250-sample SpamAssassin **Hard Ham holdout** was strictly isolated from training and threshold selection and was used solely as a diagnostic benchmark to measure newsletter false-positive mitigation across phases.
  - Zero synthetic samples were used for model training.

---

## 4. Email Detection Pipeline

- **Classifier**: `MultinomialNB(alpha=0.01, fit_prior=False)`
- **Feature Extraction**: TF-IDF unigram and bigram representation, `sublinear_tf=True`, `min_df=5`, `max_df=0.95`.
- **Active Decision Threshold**: **0.43**
- **Decision Logic**:
  $$\text{Label} = \begin{cases} \text{Spam}, & P(\text{spam}) \ge 0.43 \\ \text{Ham}, & P(\text{spam}) < 0.43 \end{cases}$$
  $$\text{Confidence} = \begin{cases} P(\text{spam}) \times 100\%, & \text{if Spam} \\ P(\text{ham}) \times 100\%, & \text{if Ham} \end{cases}$$

---

## 5. URL Detection Pipeline

- **Classifier**: `RandomForestClassifier(n_estimators=400, max_depth=25, max_features='sqrt', min_samples_leaf=1)`
- **Feature Extraction**: 18 lexical and structural features:
  - Length attributes: `URLLength`, `DomainLength`, `TLDLength`
  - Lexical counts & ratios: `NoOfLettersInURL`, `LetterRatioInURL`, `NoOfDegitsInURL`, `DegitRatioInURL`, `SpacialCharRatioInURL`
  - Special character counts: `NoOfEqualsInURL`, `NoOfQMarkInURL`, `NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`
  - Structural flags: `IsDomainIP`, `NoOfSubDomain`, `HasObfuscation`, `NoOfObfuscatedChar`, `ObfuscationRatio`, `IsHTTPS`
- **Dual-Level Inspection**: Evaluates both the full URL and the canonical apex domain to mitigate dataset host biases.
- **Classification Mapping**: Class 0 = Phishing, Class 1 = Legitimate.

---

## 6. API and Database Architecture

### REST API (FastAPI)
The backend is served by Uvicorn on `http://127.0.0.1:8000/api` with structured CORS middleware, request timing headers, and Pydantic schema validation.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Comprehensive health check: checks ML models and PostgreSQL status. |
| `POST` | `/api/analyze/email` | Analyzes raw email text; extracts links; computes composite threat. |
| `POST` | `/api/analyze/url` | Evaluates a standalone hyperlink using the 18-feature Random Forest model. |
| `POST` | `/api/analyze/file` | Parses RFC 822 `.eml` files, extracts headers/body, and runs analysis. |
| `GET` | `/api/history` | Paginated threat audit logs with filtering by analysis type. |
| `GET` | `/api/history/stats` | Aggregated analytics (threat distribution, total scans, spam/phish counts). |
| `DELETE` | `/api/history/{id}` | Deletes an individual audit record from PostgreSQL. |

### PostgreSQL Database Schema
- **Table**: `analysis_history`
- **Fields**: `id` (PK), `analysis_type`, `created_at`, `subject`, `submitted_url`, `email_prediction`, `spam_probability`, `url_count`, `extracted_urls` (JSONB), `overall_verdict`, `threat_level`, `risk_score`, `recommended_action`, `complete_analysis_result` (JSONB).
- **Privacy & Minimization**: Raw email bodies and file binaries are strictly excluded from database persistence.

---

## 7. Final Model Evaluation Metrics

### A. Independent Test Split Metrics (Untouched, N=5,779)
| Metric | Value |
| :--- | :---: |
| **Accuracy** | **98.51%** |
| **Spam Precision** | **99.27%** |
| **Spam Recall** | **97.29%** |
| **Spam F1 Score** | **0.9827** |
| **Ham Recall** | **99.45%** |
| **False Positive Rate (FPR)** | **0.55%** |
| **False Negative Rate (FNR)** | **2.71%** |
| **ROC-AUC** | **0.9984** |
| **PR-AUC** | **0.9983** |
| **Brier Score** | **0.0126** |
| **Confusion Matrix** | TN: 3,255 \| FP: 18 \| FN: 68 \| TP: 2,438 |

### B. Validation Split Metrics (Threshold Tuning, N=5,779)
| Metric | Value |
| :--- | :---: |
| **Optimal Threshold** | **0.43** |
| **Validation Accuracy** | **98.29%** |
| **Validation FPR** | **0.49%** (Satisfies $\le 0.50\%$ constraint) |
| **Validation Recall** | **96.69%** |
| **Validation Confusion Matrix** | TN: 3,256 \| FP: 16 \| FN: 83 \| TP: 2,424 |

### C. Diagnostic Hard Ham Holdout Progress (N=250)
> *Disclosure: The 250 Hard Ham holdout samples were analyzed during Phases 4 & 5. This evaluation is strictly diagnostic for newsletter regression tracking.*

| Phase / Configuration | False Positives (/250) | FPR (%) | Mean $P(\text{spam})$ |
| :--- | :---: | :---: | :---: |
| **Phase 3 Baseline (Enron+SA NB)** | 110 / 250 | 44.0% | 0.4293 |
| **Phase 5 Preprocessing (Variant C)** | 98 / 250 | 39.2% | 0.3791 |
| **Phase 7 Multi-Corpus NB (Model B2)** | **45 / 250** | **18.0%** | **0.1562** |
| **Overall Relative Improvement** | **-59.09%** | **-26.0%** | **-63.6%** |

### D. Synthetic Email Test Suite (18 Benchmark Emails)
- **Correct Predictions**: **17 / 18 (94.4%)**
- **False Negatives**: **0 (100% Phishing and Spam Recall: 10/10 caught)**
- **Legitimate Newsletters**: `04_legitimate_newsletter.eml` classified as Ham ($P=0.0425$, Risk: 4.2)
- **Credential Phishing Lures**: `14_phishing_mailbox.eml` caught as Spam ($P=0.4614 \ge 0.43$)

---

## 8. Final System Testing Results

All 12 automated system tests passed with 100% success on the live environment:
1. `GET /api/health` $\to$ **PASS** (HTTP 200, operational, DB connected)
2. `POST /api/analyze/email` (Plain Text) $\to$ **PASS** (Verdict: Clean / Legitimate, Threat: SAFE)
3. `POST /api/analyze/email` (HTML Email) $\to$ **PASS** (Verdict: Clean / Legitimate, Threat: SAFE)
4. `POST /api/analyze/email` (Legitimate Newsletter) $\to$ **PASS** (Risk: 3.4, Threat: SAFE)
5. `POST /api/analyze/email` (Spam Email) $\to$ **PASS** (Verdict: Spam Email, Risk: 100.0)
6. `POST /api/analyze/email` (Phishing Email) $\to$ **PASS** (Verdict: Phishing Attack Detected, Risk: 97.5, Action: QUARANTINE_AND_BLOCK)
7. `POST /api/analyze/email` (Multiple URLs) $\to$ **PASS** (Extracted 3 URLs, detected 1 phishing URL)
8. `POST /api/analyze/url` (URL Only) $\to$ **PASS** (Legitimate: 0.1 risk; Phishing: 97.5 risk)
9. Boundary & Malformed Inputs $\to$ **PASS** (Empty JSON: HTTP 422, Empty File: HTTP 400, Invalid Ext: HTTP 400)
10. `POST /api/analyze/file` (.eml Upload) $\to$ **PASS** (Parsed headers, verified sender, classified as Ham)
11. `GET /api/history` $\to$ **PASS** (Retrieved paginated audit history with correct schemas)
12. `GET /api/history/stats` $\to$ **PASS** (Calculated aggregated threat metrics)

---

## 9. Backup and Rollback Procedure

- **Backup Archive**: `outputs/models/backups/production_backup_20261117_120851/`
  - `email_model.joblib`
  - `email_tfidf.joblib`
  - `model_metadata.json`
- **Restoration Command**:
  ```powershell
  Copy-Item outputs/models/backups/production_backup_20261117_120851/* outputs/models/ -Force
  ```
  Set `DEFAULT_EMAIL_THRESHOLD = 0.42` in `src/models/predictor.py` and restart the backend server.

---

## 10. Security & Reliability Audit Findings

1. **Email Parsing Robustness**:
   - `parse_eml_bytes` uses Python's `policy.default` MIME parser, gracefully handling multi-part boundaries, non-standard charsets, and malformed headers without throwing unhandled exceptions.
2. **Anchor Text Spoofing Protection**:
   - `_extract_text_and_links_from_html` parses anchor tags with BeautifulSoup and appends destination `href` URLs directly into the text stream, defeating attacks that disguise malicious URLs behind innocent anchor labels (`<a href="phish.com">google.com</a>`).
3. **Data Privacy & PII Protection**:
   - `logger.info` truncates subjects to 40 characters and logs only message length.
   - The PostgreSQL `analysis_history` table deliberately omits raw email bodies and binary attachments, mitigating data leak liability under GDPR/CCPA.
4. **Input Size Enforcements**:
   - File uploads enforce a strict 10 MB ceiling (`MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024`), rejecting oversized payloads with HTTP 413.

---

## 11. Known Limitations & Future Improvements

1. **Semantic Spear-Phishing**:
   - Bag-of-words Naive Bayes classifiers evaluate term frequency. Highly tailored spear-phishing messages that use plain, polite language without traditional commercial spam tokens or embedded links can evade lexical filters. Integrating transformer-based contextual embeddings (e.g., DeBERTa or modern LLM zero-shot routing) in future iterations will address this.
2. **Domain Authentication Headers**:
   - The current model analyzes email text and embedded links, but does not parse SPF, DKIM, or DMARC authentication headers from live mail exchangers. Integrating cryptographic header validation would eliminate false positives on promotional sales emails (such as `18_mixed_sale.eml`) sent from authenticated domains.
3. **Zero-Day Compromised Domains**:
   - Lexical URL feature extraction analyzes syntactic patterns. Malicious phishing pages hosted on newly compromised legitimate top-level domains (e.g. cloud storage services) require integration with dynamic DNS reputation and threat intelligence feeds.

---

## 12. Deliverables Summary

- **Final Audit Report**: [`outputs/reports/final_project_audit.md`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/reports/final_project_audit.md)
- **Final Metrics JSON**: [`outputs/reports/final_model_metrics.json`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/reports/final_model_metrics.json)
- **Final System Test Results JSON**: [`outputs/reports/final_system_test_results.json`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/reports/final_system_test_results.json)
- **Active Model Metadata**: [`outputs/models/model_metadata.json`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/models/model_metadata.json)
- **Production Email Model**: [`outputs/models/email_model.joblib`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/models/email_model.joblib)
- **Production Email Vectorizer**: [`outputs/models/email_tfidf.joblib`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/models/email_tfidf.joblib)
- **Production URL Model**: [`outputs/models/url_model.joblib`](file:///C:/Users/admin/Desktop/ML%20CP/outputs/models/url_model.joblib)
- **Archived Production Backup**: `outputs/models/backups/production_backup_20261117_120851/`
