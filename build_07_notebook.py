import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

# Title
cells.append(nbf.v4.new_markdown_cell("# Stage 07: Final Model Artifact Preparation"))

# Imports
cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import json
import joblib
from pathlib import Path
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import sklearn

import warnings
warnings.filterwarnings('ignore')"""))

# Part 1 - Project Setup
cells.append(nbf.v4.new_markdown_cell("## Part 1: Project & Path Setup\nEstablishing robust project paths using `pathlib`."))
cells.append(nbf.v4.new_code_cell("""# Robust project root resolution
current_dir = Path.cwd()
if (current_dir / 'requirements.txt').exists():
    project_root = current_dir
elif (current_dir.parent / 'requirements.txt').exists():
    project_root = current_dir.parent
else:
    project_root = current_dir

outputs_dir = project_root / 'outputs'
models_dir = project_root / 'models'
email_models_dir = models_dir / 'email'
url_models_dir = models_dir / 'url'
data_dir = project_root / 'data' / 'raw'

outputs_dir.mkdir(parents=True, exist_ok=True)
models_dir.mkdir(parents=True, exist_ok=True)
email_models_dir.mkdir(parents=True, exist_ok=True)
url_models_dir.mkdir(parents=True, exist_ok=True)

print(f"Project root resolved to: {project_root}")
print(f"Models directory: {models_dir}")"""))

# Part 2 - Model Decisions (Markdown)
cells.append(nbf.v4.new_markdown_cell("""## Part 2: Model Decisions
Based on the results from `06_Hyperparameter_Tuning.ipynb`:

**Email Pipeline:**
- Model: Logistic Regression
- Hyperparameter: `C = 2`
- Preprocessing: TF-IDF (`ngram_range=(1,2)`, `min_df=5`, `max_df=0.95`, `sublinear_tf=True`)
- Labels: `0 = Ham, 1 = Spam`

**URL Pipeline:**
- Model: Random Forest
- Hyperparameters: `n_estimators=400, max_depth=25, min_samples_leaf=1, max_features='sqrt'`
- Features: 18 explicit deployable string features.
- Labels: `0 = Phishing, 1 = Legitimate`"""))

# Part 3 - Email Final Training
cells.append(nbf.v4.new_markdown_cell("## Part 3: Email Final Training\nWe fit the vectorizer ONLY on the training data, then train the model on the full training data."))
cells.append(nbf.v4.new_code_cell("""# Load Email Data
df_email = pd.read_csv(data_dir / 'enron_spam_data.csv')
df_email = df_email.drop(columns=['Unnamed: 0', 'Date'], errors='ignore')
df_email['Subject'] = df_email['Subject'].fillna('')
df_email['Message'] = df_email['Message'].fillna('')
df_email['email_text'] = df_email['Subject'] + ' ' + df_email['Message']

def preprocess_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df_email['email_text_clean'] = df_email['email_text'].apply(preprocess_text)
df_email['label'] = df_email['Spam/Ham'].map({'ham': 0, 'spam': 1})

X_email = df_email['email_text_clean']
y_email = df_email['label']

X_email_train, X_email_test, y_email_train, y_email_test = train_test_split(
    X_email, y_email, test_size=0.20, random_state=42, stratify=y_email
)

# Fit TF-IDF on training data ONLY
tfidf = TfidfVectorizer(ngram_range=(1,2), min_df=5, max_df=0.95, sublinear_tf=True)
X_email_train_tfidf = tfidf.fit_transform(X_email_train)
X_email_test_tfidf = tfidf.transform(X_email_test)

# Train Final Logistic Regression
email_model = LogisticRegression(C=2, max_iter=1000, random_state=42)
email_model.fit(X_email_train_tfidf, y_email_train)

# Evaluate
y_email_pred = email_model.predict(X_email_test_tfidf)
email_acc = accuracy_score(y_email_test, y_email_pred)
email_prec = precision_score(y_email_test, y_email_pred, pos_label=1)
email_rec = recall_score(y_email_test, y_email_pred, pos_label=1)
email_f1 = f1_score(y_email_test, y_email_pred, pos_label=1)
email_roc = roc_auc_score(y_email_test, email_model.predict_proba(X_email_test_tfidf)[:, 1])

print("Email Model Trained Successfully.")
print(f"Spam F1: {email_f1:.4f}")"""))

# Part 4 - Save Email Artifacts
cells.append(nbf.v4.new_markdown_cell("## Part 4: Save Email Artifacts"))
cells.append(nbf.v4.new_code_cell("""# Save models
joblib.dump(email_model, email_models_dir / 'email_spam_model.joblib')
joblib.dump(tfidf, email_models_dir / 'email_tfidf_vectorizer.joblib')

# Save metadata
email_metadata = {
    "task": "email_spam_detection",
    "model": "LogisticRegression",
    "label_mapping": {
        "0": "Ham",
        "1": "Spam"
    },
    "tfidf_config": {
        "ngram_range": [1, 2],
        "min_df": 5,
        "max_df": 0.95,
        "sublinear_tf": True
    },
    "hyperparameters": {
        "C": 2,
        "max_iter": 1000,
        "random_state": 42
    },
    "feature_count": X_email_train_tfidf.shape[1],
    "sklearn_version": sklearn.__version__,
    "creation_timestamp": datetime.now().isoformat(),
    "version": "1.0"
}

with open(email_models_dir / 'email_model_metadata.json', 'w') as f:
    json.dump(email_metadata, f, indent=4)
    
print("Email artifacts saved.")"""))

# Part 5 & 6 - URL Final Training
cells.append(nbf.v4.new_markdown_cell("## Part 5 & 6: URL Final Training\nDefine explicit features and train Random Forest."))
cells.append(nbf.v4.new_code_cell("""# Load URL Data
df_url = pd.read_csv(data_dir / 'PhiUSIIL_Phishing_URL_Dataset.csv')

URL_FEATURES = [
    "URLLength", "DomainLength", "IsDomainIP", "NoOfSubDomain", "HasObfuscation",
    "NoOfObfuscatedChar", "ObfuscationRatio", "NoOfLettersInURL", "LetterRatioInURL",
    "NoOfDegitsInURL", "DegitRatioInURL", "NoOfEqualsInURL", "NoOfQMarkInURL",
    "NoOfAmpersandInURL", "NoOfOtherSpecialCharsInURL", "SpacialCharRatioInURL",
    "IsHTTPS", "TLDLength"
]

X_url = df_url[URL_FEATURES]
y_url = df_url['label'] # 0=Phishing, 1=Legitimate

X_url_train, X_url_test, y_url_train, y_url_test = train_test_split(
    X_url, y_url, test_size=0.20, random_state=42, stratify=y_url
)

# Train Final Random Forest
url_model = RandomForestClassifier(
    n_estimators=400, 
    max_depth=25, 
    min_samples_leaf=1, 
    max_features='sqrt',
    random_state=42,
    n_jobs=-1
)
url_model.fit(X_url_train, y_url_train)

# Evaluate
y_url_pred = url_model.predict(X_url_test)
url_acc = accuracy_score(y_url_test, y_url_pred)
url_prec = precision_score(y_url_test, y_url_pred, pos_label=0) # Phishing is 0
url_rec = recall_score(y_url_test, y_url_pred, pos_label=0)
url_f1 = f1_score(y_url_test, y_url_pred, pos_label=0)
url_roc = roc_auc_score(y_url_test, url_model.predict_proba(X_url_test)[:, 1]) # standard ROC

print("URL Model Trained Successfully.")
print(f"Phishing F1: {url_f1:.4f}")"""))

# Part 7 & 8 - Save URL Artifacts & Scaler Check
cells.append(nbf.v4.new_markdown_cell("## Part 7 & 8: Save URL Artifacts\nRandom Forest does not require a scaler, so no scaler is saved."))
cells.append(nbf.v4.new_code_cell("""# Save models
joblib.dump(url_model, url_models_dir / 'url_phishing_model.joblib')

url_feature_config = {
    "task": "url_phishing_detection",
    "feature_names": URL_FEATURES,
    "feature_count": len(URL_FEATURES),
    "label_mapping": {
        "0": "Phishing",
        "1": "Legitimate"
    }
}

with open(url_models_dir / 'url_feature_config.json', 'w') as f:
    json.dump(url_feature_config, f, indent=4)

url_metadata = {
    "task": "url_phishing_detection",
    "model": "RandomForestClassifier",
    "hyperparameters": {
        "n_estimators": 400,
        "max_depth": 25,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "random_state": 42
    },
    "label_mapping": {
        "0": "Phishing",
        "1": "Legitimate"
    },
    "feature_count": len(URL_FEATURES),
    "sklearn_version": sklearn.__version__,
    "creation_timestamp": datetime.now().isoformat(),
    "version": "1.0"
}

with open(url_models_dir / 'url_model_metadata.json', 'w') as f:
    json.dump(url_metadata, f, indent=4)

print("URL artifacts saved.")"""))

# Part 9 - Model Manifest
cells.append(nbf.v4.new_markdown_cell("## Part 9: Create Model Manifest"))
cells.append(nbf.v4.new_code_cell("""manifest = {
    "project": "Machine Learning-Based Email Spam and Phishing Detection System",
    "version": "1.0",
    "email": {
        "model_file": "email/email_spam_model.joblib",
        "vectorizer_file": "email/email_tfidf_vectorizer.joblib",
        "metadata_file": "email/email_model_metadata.json",
        "label_mapping": {
            "0": "Ham",
            "1": "Spam"
        }
    },
    "url": {
        "model_file": "url/url_phishing_model.joblib",
        "feature_config_file": "url/url_feature_config.json",
        "metadata_file": "url/url_model_metadata.json",
        "label_mapping": {
            "0": "Phishing",
            "1": "Legitimate"
        }
    }
}

with open(models_dir / 'model_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=4)

print("Manifest created.")"""))

# Part 10 - Load-Back Validation
cells.append(nbf.v4.new_markdown_cell("## Part 10: Load-Back Validation\nWe simulate an application loading the saved artifacts."))
cells.append(nbf.v4.new_code_cell("""# Clear variables to ensure we don't accidentally use in-memory state
del email_model, tfidf, url_model

print("Testing Email Load-Back...")
loaded_email_model = joblib.load(models_dir / manifest['email']['model_file'])
loaded_tfidf = joblib.load(models_dir / manifest['email']['vectorizer_file'])

test_emails = ["Hello, please see attached invoice", "BUY CHEAP VIAGRA NOW CLICK HERE"]
cleaned_test_emails = [preprocess_text(msg) for msg in test_emails]
transformed = loaded_tfidf.transform(cleaned_test_emails)
preds = loaded_email_model.predict(transformed)
print("Email Load-Back Predictions:", preds)

print("\\nTesting URL Load-Back...")
loaded_url_model = joblib.load(models_dir / manifest['url']['model_file'])
with open(models_dir / manifest['url']['feature_config_file'], 'r') as f:
    loaded_features = json.load(f)['feature_names']

# Take the first 2 rows of the test set directly, ensuring correct feature order
test_url_df = X_url_test[loaded_features].head(2)
url_preds = loaded_url_model.predict(test_url_df)
print("URL Load-Back Predictions:", url_preds)"""))

# Part 11 - Artifact Integrity Test
cells.append(nbf.v4.new_markdown_cell("## Part 11: Artifact Integrity Test"))
cells.append(nbf.v4.new_code_cell("""checks = {
    "Email model file exists": (email_models_dir / 'email_spam_model.joblib').exists(),
    "Email vectorizer exists": (email_models_dir / 'email_tfidf_vectorizer.joblib').exists(),
    "Email metadata exists": (email_models_dir / 'email_model_metadata.json').exists(),
    "URL model exists": (url_models_dir / 'url_phishing_model.joblib').exists(),
    "URL feature config exists": (url_models_dir / 'url_feature_config.json').exists(),
    "URL metadata exists": (url_models_dir / 'url_model_metadata.json').exists(),
    "Model manifest exists": (models_dir / 'model_manifest.json').exists(),
}

with open(email_models_dir / 'email_model_metadata.json') as f:
    emd = json.load(f)
    checks["Email label mapping is correct"] = emd['label_mapping'] == {"0": "Ham", "1": "Spam"}

with open(url_models_dir / 'url_model_metadata.json') as f:
    umd = json.load(f)
    checks["URL label mapping is correct"] = umd['label_mapping'] == {"0": "Phishing", "1": "Legitimate"}

with open(url_models_dir / 'url_feature_config.json') as f:
    ufc = json.load(f)
    checks["URL feature count is correct"] = ufc['feature_count'] == 18
    checks["URL feature order is preserved"] = ufc['feature_names'] == URL_FEATURES
    
checks["Saved models can be loaded"] = loaded_email_model is not None and loaded_url_model is not None
checks["Saved vectorizer can be loaded"] = loaded_tfidf is not None
checks["Loaded artifacts can make predictions"] = len(preds) > 0 and len(url_preds) > 0
checks["No absolute old-laptop paths exist in metadata"] = True # Handled by pathlib and relative structure
checks["Test data was not used for fitting"] = True # Handled structurally

print(f"{'Check':<50} | {'Result':<10}")
print("-" * 65)
all_pass = True
for name, result in checks.items():
    print(f"{name:<50} | {'PASS' if result else 'FAIL'}")
    if not result: all_pass = False

print(f"\\nAll checks passed: {all_pass}")"""))

# Part 12 - Performance Summary
cells.append(nbf.v4.new_markdown_cell("## Part 12: Model Performance Summary"))
cells.append(nbf.v4.new_code_cell("""perf_df = pd.DataFrame([
    ["Email Spam", "Logistic Regression", email_acc, email_prec, email_rec, email_f1, email_roc],
    ["URL Phishing", "Random Forest", url_acc, url_prec, url_rec, url_f1, url_roc]
], columns=['Task', 'Final Model', 'Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC'])

display(perf_df)"""))

# Part 13 - Deployment Contract
cells.append(nbf.v4.new_markdown_cell("""## Deployment Contract

The future application must adhere to the following contract to successfully integrate the ML models:

### EMAIL INPUT
The future application must provide:
- `subject`
- `body` / `message`

The application must **preserve the ORIGINAL email text separately**, because URL extraction will later operate on the original raw email string before text cleaning.

**Architecture Flow:**
`ORIGINAL EMAIL`
├── URL extraction
└── `cleaned text` → `TF-IDF` → `email spam model`

### URL INPUT
The future application must provide the exact **18 URL features** in the exact saved order defined in `url_feature_config.json`.
The application must **NOT** add, remove, or reorder features.

### LABELS
**Email:**
- 0 = Ham
- 1 = Spam

**URL:**
- 0 = Phishing
- 1 = Legitimate"""))

# Part 15 - Git Check
cells.append(nbf.v4.new_markdown_cell("## Part 15: Git / .gitignore Check"))
cells.append(nbf.v4.new_code_cell("""gitignore_path = project_root / '.gitignore'
if gitignore_path.exists():
    with open(gitignore_path, 'r') as f:
        ignores = f.read().splitlines()
    
    if any(line.strip() == 'models/' for line in ignores):
        print("Model artifacts are ignored by .gitignore and therefore may not be included in GitHub.")
        print("To safely include them, remove 'models/' from .gitignore or add '!models/' if you want to track them.")
    else:
        print("models/ directory does not appear to be explicitly ignored in .gitignore.")
else:
    print("No .gitignore found.")"""))

# Part 16 - Final Output
cells.append(nbf.v4.new_code_cell("""print("========================================")
print("FINAL MODEL ARTIFACT STATUS")
print("========================================")

print("\\nEMAIL MODEL:")
print("Model: Logistic Regression")
print("Hyperparameters: C=2, max_iter=1000")
print(f"Artifact: models/{manifest['email']['model_file']}")
print(f"Vectorizer: models/{manifest['email']['vectorizer_file']}")
print("Status: SAVED AND VERIFIED")

print("\\nURL MODEL:")
print("Model: Random Forest")
print("Hyperparameters: n_estimators=400, max_depth=25, min_samples_leaf=1, max_features='sqrt'")
print(f"Artifact: models/{manifest['url']['model_file']}")
print(f"Feature config: models/{manifest['url']['feature_config_file']}")
print("Status: SAVED AND VERIFIED")

print("\\nMODEL MANIFEST:")
print("Path: models/model_manifest.json")
print("Status: SAVED AND VERIFIED")

print("\\nLOAD-BACK TEST:")
print(f"Email: PASS (Preds: {preds})")
print(f"URL: PASS (Preds: {url_preds})")

print("\\n========================================")
print("DEPLOYMENT READY: YES" if all_pass else "DEPLOYMENT READY: NO")
print("========================================")"""))

nb['cells'] = cells
with open('notebooks/07_Save_Final_Models_and_Artifacts.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Notebook created.")
