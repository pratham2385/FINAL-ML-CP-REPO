# PhishGuard: Dual-Stream Email Spam, Phishing Intent & URL Detection System

An enterprise-grade, end-to-end security analysis system that detects email spam, identifies malicious hyperlinks, discovers deceptive phishing intent (such as Business Email Compromise and credential theft), and aggregates multi-signal composite risk verdicts. Built with a **Dual-Representation ML Pipeline**, a **FastAPI REST API**, a **PostgreSQL 18** audit database, and a **React + Tailwind CSS** Security Operations Center (SOC) threat analysis console.

---

## Architecture Overview

```
                      +-------------------------------------------------+
                      |              Incoming Threat Input              |
                      |        (Raw Email, URL, or .eml Batch)          |
                      +-------------------------------------------------+
                                               |
                 +-----------------------------+-----------------------------+
                 |                             |                             |
      [Stream 1: Lexical URL]      [Stream 2: NLP Spam Stream]    [Stream 3: Phishing Intent]
    Embedded Hyperlink Extractor   Variant C HTML Preprocessing   Heuristic Rule-Based Engine
                 |                             |                             |
    18 Lexical Dimensions          268,754 Unigram + Bigram       5 Attack Intent Categories:
                 |                     TF-IDF Features             - BEC & Wire Fraud
    400-Tree Random Forest                     |                   - Credential Harvesting
    (PhiUSIIL Benchmark)           Multinomial Naive Bayes         - Payment & Invoice Fraud
                 |                 (alpha=0.01, Threshold=0.43)    - Impersonation Lures
                 |                 (Multi-Corpus Benchmark)        - Malicious Attachments
                 |                             |                             |
                 +-----------------------------+-----------------------------+
                                               |
                           +----------------------------------------+
                           |     Multi-Signal Risk Aggregator       |
                           |  Verdict: SAFE / SUSPICIOUS / MALICIOUS|
                           |  Risk Score: 0.0 to 100.0              |
                           |  Action: ALLOW / WARN / JUNK / BLOCK   |
                           +----------------------------------------+
                                               |
         +-------------------------------------+-------------------------------------+
         |                                                                           |
[FastAPI REST API & Docs]                                                 [PostgreSQL 18 Database]
http://127.0.0.1:8000/docs                                                Audit Log & JSONB Payloads
         |
         +-------------------------------------+
                                               |
                              [React + Vite SOC Console]
                                 http://localhost:5173
```

---

## Tech Stack

- **Machine Learning**: Scikit-Learn, Joblib, NumPy, Pandas (MultinomialNB, Random Forest, TF-IDF Vectorization)
- **Heuristic Threat Modeling**: Phishing Intent Engine (BEC, display-name spoofing, freemail domain detection)
- **Backend API**: FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: PostgreSQL 18, SQLAlchemy 2.x, psycopg 3 (`psycopg[binary]`)
- **Frontend SPA**: React 19, Vite, Tailwind CSS v4, React Router v7, Axios, Lucide React, Recharts
- **Design System**: SOC Threat Console with Graphite neutral ramp (`#0d0f12`), hairline borders, and `tabular-nums` formatting

---

## Key Capabilities & Production Specifications

1. **Email Spam & Threat Classifier (Model B2)**
   - **Algorithm:** Multinomial Naive Bayes (`alpha=0.01`, `fit_prior=False`, uniform prior probability adjustment).
   - **Vocabulary:** 268,754 unigram + bigram TF-IDF features.
   - **Preprocessing:** Variant C (HTML structure-aware tag parsing + conservative marketing footer handling).
   - **Decision Threshold:** `0.43` (optimized on validation split).
   - **Benchmark Training Set:** 37,890 samples across Enron, CEAS, SpamAssassin, Nazario, and real legitimate marketing newsletters.
   - **Test Metrics:** 98.51% Accuracy, 99.27% Spam Precision, 97.29% Spam Recall, 0.55% FPR on test set.

2. **Standalone & Embedded URL Phishing Classifier**
   - **Algorithm:** 400-Tree Tuned Random Forest.
   - **Features:** 18 structural and lexical dimensions (domain length, path depth, subdomain count, special character frequency, obfuscation patterns, raw IP detection, sensitive keywords).
   - **Evaluation:** Dual-level canonical domain normalization and deep path inspection.

3. **Dedicated Phishing Intent Detection Layer**
   - Evaluates text independently of spam keyword density.
   - Detects Business Email Compromise (BEC), credential theft, financial wire fraud, authority impersonation, and malicious document lures.
   - Identifies display name mismatches (e.g. `CEO Johnathan Smith <urgent.exec@gmail.com>`) and freemail domain usage.

4. **Unified Multi-Signal Risk Aggregation**
   - Eliminates contradictions between email NLP predictions and URL classifications.
   - Outputs standardized verdicts: `SAFE`, `SUSPICIOUS`, or `MALICIOUS`.
   - Continuous risk score (0 to 100) and actionable mitigation instructions (`ALLOW`, `WARN_USER`, `MOVE_TO_JUNK`, `QUARANTINE_AND_BLOCK`).
   - Validated on synthetic test suites with 0 false negatives and 0 false alarms of `MALICIOUS`.

5. **Batch Email Upload (.eml)**
   - Drag-and-drop support for single or batch uploads up to **100 RFC 822 `.eml` files** (up to 10MB per file, 100MB batch total).
   - Concurrent asynchronous evaluation using a 5-worker thread pool.
   - Real-time progress bar, queue management, individual file removal, filter views (All, Spam, Ham, Failed), and collapsible inspection cards.

6. **PostgreSQL Audit History & Telemetry**
   - Persists all analyses with structured headers, extracted URLs, intent telemetry, and complete JSONB response payloads.
   - Filterable, searchable, and paginated with individual record deletion and deep modal inspection.

---

## PostgreSQL Database Setup

### 1. Database Configuration (.env)

Create or configure `backend/.env` with your PostgreSQL credentials:

```ini
# PostgreSQL Connection String (psycopg3 driver)
# Note: If your password contains special characters like '@', percent-encode it (e.g. '@' -> '%40')
DATABASE_URL=postgresql+psycopg://postgres:India%401974@localhost:5432/phishing_detection_db
TEST_DATABASE_URL=postgresql+psycopg://postgres:India%401974@localhost:5432/phishing_detection_test_db

# Discrete parameters (fallback / component access)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=India@1974
DB_NAME=phishing_detection_db
TEST_DB_NAME=phishing_detection_test_db
```

*Note: `backend/.env` is ignored by Git. A clean template is provided in `backend/.env.example`.*

### 2. Create Database via PowerShell

```powershell
# Set environment password for psql
$env:PGPASSWORD = "India@1974"

# Create application database
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432 -c "CREATE DATABASE phishing_detection_db;"

# Create isolated test database
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432 -c "CREATE DATABASE phishing_detection_test_db;"
```

---

## Running the Application

### 1. Start the Backend API (Port 8000)

```powershell
# From the project root:
.\venv\Scripts\python.exe backend/run.py
```
- **Backend URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/api/health`

### 2. Start the Frontend Dashboard (Port 5173)

In a separate terminal:

```powershell
cd frontend
npm run dev
```
- **Frontend Dashboard URL**: `http://localhost:5173`

---

## Automated Test Suites

### 1. Run Complete Backend Test Suite (45 Tests)

```powershell
.\venv\Scripts\python.exe -m pytest backend/tests/ -v
```

### 2. Run Synthetic Email Benchmark Audits

```powershell
# Suite A (18 emails) and Suite B (24 emails) verification
.\venv\Scripts\python.exe src/models/verify_audit_metrics.py
```

### 3. Build Frontend for Production

```powershell
cd frontend
npm run build
```

---

## Project Structure

```
ML CP/
├── backend/                        # FastAPI REST API
│   ├── app/
│   │   ├── config.py              # Environment settings & thresholds
│   │   ├── database.py            # PostgreSQL connection & session factory
│   │   ├── models/                # SQLAlchemy models (AnalysisHistory)
│   │   ├── routers/               # Endpoint routes (email, URL, file, history, health)
│   │   ├── schemas/               # Pydantic v2 validation schemas
│   │   └── services/              # ML inference service wrappers
│   ├── run.py                     # Uvicorn entrypoint
│   └── tests/                     # 45 automated backend unit & integration tests
├── frontend/                       # React 19 + Vite SOC Dashboard
│   ├── src/
│   │   ├── api/                   # Axios API service clients
│   │   ├── components/            # Reusable UI components & result cards
│   │   ├── pages/                 # Route pages (Dashboard, Email, URL, File, History, Settings)
│   │   ├── utils/                 # Formatters & style helpers
│   │   └── index.css              # Graphite design system styling
│   └── package.json
├── outputs/models/                 # Production model artifacts & metadata
│   ├── email_model.joblib         # Active MultinomialNB classifier
│   ├── email_tfidf.joblib         # Active TF-IDF vectorizer (268,754 features)
│   ├── model_metadata.json        # Active configuration, threshold (0.43), and metrics
│   ├── url_model.joblib           # Active 400-Tree Random Forest model
│   └── backups/                   # Versioned rollbacks (Phase 6, baseline)
├── src/
│   ├── features/                  # Preprocessing, feature extractors, phishing intent
│   │   ├── email_preprocessor.py  # Variant C HTML & footer preprocessor
│   │   ├── extract_features.py    # 18 lexical URL feature extractor
│   │   ├── phishing_intent.py     # Heuristic intent & BEC detection layer
│   │   └── risk_aggregator.py     # Multi-signal risk assessment engine
│   ├── models/                    # Prediction pipelines & audit scripts
│   └── pipeline.py                # Core dual-representation predictor
└── README.md
```
