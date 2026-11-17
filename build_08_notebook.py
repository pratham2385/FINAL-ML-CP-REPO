import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

# Title
cells.append(nbf.v4.new_markdown_cell("# Stage 08: URL Extraction & Inference Pipeline"))

# Imports
cells.append(nbf.v4.new_code_cell(r"""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import json
import joblib
from pathlib import Path
import urllib.parse

import warnings
warnings.filterwarnings('ignore')"""))

# Part 1 - Project Setup
cells.append(nbf.v4.new_markdown_cell("## Part 1: Project & Path Setup\nDetermining project root and verifying all required artifacts exist."))
cells.append(nbf.v4.new_code_cell(r"""# Robust project root resolution
current_dir = Path.cwd()
if (current_dir / 'requirements.txt').exists():
    project_root = current_dir
elif (current_dir.parent / 'requirements.txt').exists():
    project_root = current_dir.parent
else:
    project_root = current_dir

models_dir = project_root / 'models'

required_files = [
    models_dir / 'email' / 'email_spam_model.joblib',
    models_dir / 'email' / 'email_tfidf_vectorizer.joblib',
    models_dir / 'url' / 'url_phishing_model.joblib',
    models_dir / 'url' / 'url_feature_config.json',
    models_dir / 'model_manifest.json'
]

for f in required_files:
    if not f.exists():
        raise FileNotFoundError(f"CRITICAL ERROR: Missing required artifact: {f}")

print(f"Project root: {project_root}")
print("All required artifacts found.")"""))

# Part 2 - Load and Verify Models
cells.append(nbf.v4.new_markdown_cell("## Part 2: Load and Verify Models\nLoading the saved artifacts without retraining."))
cells.append(nbf.v4.new_code_cell(r"""with open(models_dir / 'model_manifest.json', 'r') as f:
    manifest = json.load(f)

email_model = joblib.load(models_dir / manifest['email']['model_file'])
email_vectorizer = joblib.load(models_dir / manifest['email']['vectorizer_file'])
url_model = joblib.load(models_dir / manifest['url']['model_file'])

with open(models_dir / manifest['url']['feature_config_file'], 'r') as f:
    url_feature_config = json.load(f)
url_features = url_feature_config['feature_names']

print("--- EMAIL MODEL ---")
print(f"Model Type: {type(email_model).__name__}")
print(f"TF-IDF Features: {len(email_vectorizer.vocabulary_)}")
print(f"Model Classes: {email_model.classes_}")

print("\n--- URL MODEL ---")
print(f"Model Type: {type(url_model).__name__}")
print(f"URL Features Expected: {len(url_features)}")
print(f"Model Classes: {url_model.classes_}")

# Validate email model classes against manifest
for label, class_name in manifest['email']['label_mapping'].items():
    if int(label) not in email_model.classes_:
        raise ValueError(f"Manifest label {label} not found in email model classes!")

# Validate url model classes against manifest
for label, class_name in manifest['url']['label_mapping'].items():
    if int(label) not in url_model.classes_:
        raise ValueError(f"Manifest label {label} not found in url model classes!")
print("\nClass mappings successfully verified against models.")"""))

# Part 3 - Email Text Preprocessing
cells.append(nbf.v4.new_markdown_cell("## Part 3: Email Text Preprocessing\nReproducing the exact cleaning logic used during model training."))
cells.append(nbf.v4.new_code_cell(r"""def clean_email_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http[s]?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text"""))

# Part 4 - URL Extraction
cells.append(nbf.v4.new_markdown_cell("## Part 4: URL Extraction\nExtracting URLs from the raw original email text using Regex."))
cells.append(nbf.v4.new_code_cell(r"""def extract_urls(text):
    if not isinstance(text, str): return []
    # Regex to capture http/https URLs including fragments and query params
    url_pattern = re.compile(r'https?://[a-zA-Z0-9./\-_?=&%:#]+')
    urls = url_pattern.findall(text)
    
    cleaned_urls = []
    seen = set()
    for url in urls:
        # Strip trailing punctuation that often gets caught in regex
        url = url.rstrip('.,!?)\]}\"')
        if url not in seen:
            seen.add(url)
            cleaned_urls.append(url)
            
    return cleaned_urls"""))

# Part 5 & 6 - URL Feature Extraction & Definitions
cells.append(nbf.v4.new_markdown_cell("""## Part 5 & 6: URL Feature Extraction & Definitions

**CRITICAL ISSUE:** The training pipeline loaded `PhiUSIIL_Phishing_URL_Dataset.csv` directly. The project notebooks (01-07) do NOT contain the Python code used to extract the 18 URL features from raw URLs. 

### Feature Consistency Table

| Feature | Definition | Verified Source |
|---|---|---|
| URLLength | Total string length of the URL | PhiUSIIL Documentation |
| DomainLength | Length of domain name | PhiUSIIL Documentation |
| IsDomainIP | 1 if domain is an IP address | PhiUSIIL Documentation |
| NoOfSubDomain | **FEATURE DEFINITION UNVERIFIED** (Exact TLD handling/dot parsing logic unknown) | NONE |
| HasObfuscation | **FEATURE DEFINITION UNVERIFIED** (Obfuscation characters undefined) | NONE |
| NoOfObfuscatedChar | Number of obfuscated chars | PhiUSIIL Documentation |
| ObfuscationRatio | NoOfObfuscatedChar / URLLength | PhiUSIIL Documentation |
| NoOfLettersInURL | Number of alphabetical characters in the URL | PhiUSIIL Documentation |
| LetterRatioInURL | NoOfLettersInURL / URLLength | PhiUSIIL Documentation |
| NoOfDegitsInURL | Number of digit characters in the URL | PhiUSIIL Documentation |
| DegitRatioInURL | NoOfDegitsInURL / URLLength | PhiUSIIL Documentation |
| NoOfEqualsInURL | Count of '=' | PhiUSIIL Documentation |
| NoOfQMarkInURL | Count of '?' | PhiUSIIL Documentation |
| NoOfAmpersandInURL | Count of '&' | PhiUSIIL Documentation |
| NoOfOtherSpecialCharsInURL | **FEATURE DEFINITION UNVERIFIED** (Exact character set unknown) | NONE |
| SpacialCharRatioInURL | NoOfOtherSpecialCharsInURL / URLLength | PhiUSIIL Documentation |
| IsHTTPS | 1 if URL starts with https | PhiUSIIL Documentation |
| TLDLength | **FEATURE DEFINITION UNVERIFIED** | NONE |

We require the original feature extraction script used by the PhiUSIIL dataset creators to guarantee consistency.
"""))
cells.append(nbf.v4.new_code_cell(r"""def extract_url_features(url):
    parsed = urllib.parse.urlparse(url)
    raise NotImplementedError(
        "CRITICAL ERROR: Cannot verify the exact documented definitions for: "
        "'NoOfSubDomain', 'NoOfOtherSpecialCharsInURL', 'HasObfuscation', 'TLDLength'. "
        "Stopping to prevent arbitrary approximations."
    )"""))

# Part 7, 8, 9, 10 - Single Email Inference Function
cells.append(nbf.v4.new_markdown_cell("## Part 7, 8, 9, 10: Single Email Inference Function\nCombines everything: predict email spam, extract URLs, extract URL features, predict URL phishing."))
cells.append(nbf.v4.new_code_cell(r"""def analyze_email(subject, body):
    subject = subject if subject else ""
    body = body if body else ""
    raw_email = subject + " " + body
    
    # 1. Email Spam Inference
    cleaned_text = clean_email_text(raw_email)
    email_vec = email_vectorizer.transform([cleaned_text])
    email_pred_class = email_model.predict(email_vec)[0]
    email_probs = email_model.predict_proba(email_vec)[0]
    
    email_pred_label = manifest['email']['label_mapping'][str(email_pred_class)]
    email_class_idx = np.where(email_model.classes_ == email_pred_class)[0][0]
    email_confidence = email_probs[email_class_idx]
    
    # 2. URL Extraction & Inference
    urls = extract_urls(raw_email)
    url_results = []
    
    for url in urls:
        try:
            features = extract_url_features(url)
        except NotImplementedError:
            features = None
            
        if features is None:
            url_results.append({
                "url": url,
                "prediction": "Error",
                "label": -1,
                "confidence": 0.0
            })
            continue
            
        feature_df = pd.DataFrame([features], columns=url_features)
        url_pred_class = url_model.predict(feature_df)[0]
        url_probs = url_model.predict_proba(feature_df)[0]
        
        url_pred_label = manifest['url']['label_mapping'][str(url_pred_class)]
        url_class_idx = np.where(url_model.classes_ == url_pred_class)[0][0]
        url_confidence = url_probs[url_class_idx]
        
        url_results.append({
            "url": url,
            "prediction": url_pred_label,
            "label": int(url_pred_class),
            "confidence": float(url_confidence),
            "probs": url_probs.tolist() # Stored for debug displaying later
        })
        
    return {
        "email": {
            "prediction": email_pred_label,
            "label": int(email_pred_class),
            "confidence": float(email_confidence),
            "probs": email_probs.tolist()
        },
        "urls": url_results,
        "url_count": len(urls)
    }"""))

# Part 11 - Test the Pipeline
cells.append(nbf.v4.new_markdown_cell("## Part 11: Test the Pipeline"))
cells.append(nbf.v4.new_code_cell(r"""tests = [
    ("TEST 1: Normal email with no URL", "Team meeting tomorrow", "Please attend the meeting at 10 AM."),
    ("TEST 2: Email containing one URL", "Action Required", "Click here: https://example.com/login"),
    ("TEST 3: Email containing multiple URLs", "Resources", "Docs: https://docs.python.org/3/ or Search: http://google.com"),
    ("TEST 4: Email containing duplicate URLs", "Reminders", "Visit https://test.com now. I repeat, go to https://test.com."),
    ("TEST 5: Long email", "Monthly Newsletter", "Welcome to the newsletter. "*20 + "Read more at https://newsletter.org/read."),
    ("TEST 6: Email with punctuation around URLs", "Hey!", "Have you seen (https://example.com/page)? It's cool!"),
    ("TEST 7: Empty subject but valid body", "", "Just wanted to share this: http://192.168.1.1/admin.php"),
    ("TEST 8: Valid subject but empty body", "http://suspicious-phishing-link.com/login", "")
]

for name, subj, body in tests:
    print(f"--- {name} ---")
    res = analyze_email(subj, body)
    print(f"Email Prediction: {res['email']['prediction']} (Conf: {res['email']['confidence']:.2f})")
    print(f"Extracted URLs ({res['url_count']}):")
    for u in res['urls']:
        print(f"  - {u['url']} -> {u['prediction']} (Conf: {u['confidence']:.2f})")
    print("")"""))

# Part 12 - Security Interpretation
cells.append(nbf.v4.new_markdown_cell("""## Part 12: Security Interpretation

**Important Context:**
An email and the URLs inside it are evaluated independently.
- **Spam + Legitimate URL**: Marketing spam containing a real link to a real company.
- **Spam + Phishing URL**: A malicious scam email trying to steal credentials.
- **Ham + Legitimate URL**: A normal coworker email sharing a safe link.
- **Ham + Phishing URL**: A sophisticated spear-phishing attack where the text seems perfectly normal (Ham) but the link is dangerous!

The system evaluates both vectors to provide defense-in-depth."""))

# Part 13 & 14 - Debugging Table & Prediction Details
cells.append(nbf.v4.new_markdown_cell("## Part 13 & 14: URL Feature Debugging Table & Model Prediction Details"))
cells.append(nbf.v4.new_code_cell(r"""example_url = "http://secure-login-update-account.com.account-verify.info/login.php?user=123"
example_features = extract_url_features(example_url)

print("--- URL Feature Debugging Table ---")
print(f"URL: {example_url}")
debug_df = pd.DataFrame({"Feature": url_features, "Extracted Value": example_features})
display(debug_df)

print("\n--- Model Prediction Details Example ---")
# Email Details
test_subj = "URGENT ACCOUNT UPDATE"
test_body = f"Please click the link to verify your account: {example_url}"
res = analyze_email(test_subj, test_body)

print("EMAIL:")
print(f"  Predicted Class: {res['email']['prediction']}")
print(f"  Probability Ham: {res['email']['probs'][0]:.4f}")
print(f"  Probability Spam: {res['email']['probs'][1]:.4f}")

print("\nURL:")
print(f"  URL Evaluated: {res['urls'][0]['url']}")
print(f"  Predicted Class: {res['urls'][0]['prediction']}")
print(f"  Probability Phishing: {res['urls'][0]['probs'][0]:.4f}")
print(f"  Probability Legitimate: {res['urls'][0]['probs'][1]:.4f}")"""))

# Part 15 - Edge Case Handling
cells.append(nbf.v4.new_markdown_cell("## Part 15: Edge Case Handling"))
cells.append(nbf.v4.new_code_cell(r"""edge_cases = [
    ("Empty Email", "", ""),
    ("Malformed URL", "Check this: http://???what.is.this", ""),
    ("IP URL", "Login here: http://192.168.1.100/admin", "")
]

for name, subj, body in edge_cases:
    res = analyze_email(subj, body)
    print(f"{name} -> Email: {res['email']['prediction']}, URLs: {[u['url'] for u in res['urls']]}")"""))

# Part 16 - Data Leakage Check
cells.append(nbf.v4.new_markdown_cell("""## Part 16: Data Leakage Check
This notebook performs **inference only**.
It does **NOT**:
- fit TF-IDF
- train a model
- tune hyperparameters
- modify the test set
- use test labels
- use external information

All models and vectorizers are loaded directly from the isolated saved artifacts."""))

cells.append(nbf.v4.new_markdown_cell("""## Part 17: Final Pipeline Diagram
```mermaid
flowchart TD
    A[Email Subject + Body] --> B[Preserve Original Email]
    B --> C[Clean Email Text]
    C --> D[Saved TF-IDF Vectorizer]
    D --> E[Logistic Regression]
    E --> F[Ham / Spam]

    B --> G[Extract URLs]
    G --> H[Extract URL Features]
    H --> I[Saved Random Forest]
    I --> J[Phishing / Legitimate]
```"""))

# Training-Inference Consistency
cells.append(nbf.v4.new_markdown_cell("""## Part 17.5: Training–Inference Consistency
The model only understands the numerical features it saw during training. Therefore, a URL must be converted into those same features using the same definitions and feature order during prediction."""))
cells.append(nbf.v4.new_code_cell(r"""# Feature Consistency Test
extracted_features = extract_url_features("https://example.com")
if extracted_features is None:
    raise NotImplementedError(
        "CRITICAL ERROR: Training definition for the 18 URL features cannot be verified "
        "from the project code. The original PhiUSIIL dataset was pre-computed. "
        "You MUST provide the original extraction script to guarantee training-inference consistency."
    )

assert len(extracted_features) == len(url_features), "Mismatch in feature count!"

test_df = pd.DataFrame([extracted_features], columns=url_features)
assert list(test_df.columns) == url_features, "Mismatch in feature columns/order!"
print("Feature consistency verified.")"""))

# Part 18 - Final Output
cells.append(nbf.v4.new_code_cell(r"""print("========================================")
print("STAGE 08 VALIDATION")
print("========================================")

checks = {}
try:
    checks["Model Loading"] = (email_model is not None and url_model is not None)
except:
    checks["Model Loading"] = False
    
try:
    res = analyze_email("Test", "http://example.com")
    checks["Email Inference"] = ('prediction' in res['email'])
    checks["URL Extraction"] = (res['url_count'] == 1)
except:
    checks["Email Inference"] = False
    checks["URL Extraction"] = False

# We explicitly fail these due to missing implementation
checks["URL Feature Extraction"] = False
checks["Feature Order"] = False
checks["Training-Inference Consistency"] = False

try:
    res_none = analyze_email("No url here", "")
    checks["No URL Handling"] = (res_none['url_count'] == 0)
except:
    checks["No URL Handling"] = False

try:
    res_multi = analyze_email("Two urls", "http://a.com and http://b.com")
    checks["Multiple URL Handling"] = (res_multi['url_count'] == 2)
except:
    checks["Multiple URL Handling"] = False
    
try:
    res_dup = analyze_email("Dup urls", "http://a.com and http://a.com")
    checks["Duplicate URL Handling"] = (res_dup['url_count'] == 1)
except:
    checks["Duplicate URL Handling"] = False
    
try:
    res_mal = analyze_email("Malformed", "http://???what.is.this")
    checks["Malformed URL Handling"] = (res_mal['url_count'] >= 0)
except:
    checks["Malformed URL Handling"] = False

all_pass = True
for key in ["Model Loading", "Email Inference", "URL Extraction", "URL Feature Extraction", 
            "Feature Order", "Training-Inference Consistency", "No URL Handling", 
            "Multiple URL Handling", "Duplicate URL Handling", "Malformed URL Handling"]:
    v = checks.get(key, False)
    status = "PASS" if v else "FAIL"
    print(f"{key}: {status}")
    if not v:
        all_pass = False

print("\nFresh Kernel: MANUAL VERIFICATION REQUIRED\n")
print("========================================")
if all_pass:
    print("STAGE 08 COMPLETE: YES")
else:
    print("STAGE 08 COMPLETE: NO")
    print("\nMissing Feature Definitions:")
    print("- NoOfSubDomain")
    print("- NoOfOtherSpecialCharsInURL")
    print("- HasObfuscation")
    print("- TLDLength")
print("========================================")"""))

nb['cells'] = cells
with open('notebooks/08_URL_Extraction_and_Inference_Pipeline.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Notebook 08 created.")
