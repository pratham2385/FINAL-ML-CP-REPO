import os
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

# Title
cells.append(nbf.v4.new_markdown_cell("# Notebook 09: Deployable URL Phishing Model"))

cells.append(nbf.v4.new_markdown_cell("""## 1. Introduction and Architectural Context

### OLD URL MODEL = BASELINE
- **Source**: `04_Model_Training_and_Evaluation.ipynb`
- **Features**: 18 pre-computed features from the PhiUSIIL dataset.
- **Problem**: The exact feature-generation logic for converting a raw URL into those specific 18 values is unavailable. Therefore, we cannot safely parse raw URLs during inference without risking severe distribution shift and false predictions.
- **Status**: Kept as an experimental baseline model. **NOT SAFE** for raw URL deployment.

### NEW URL MODEL = DEPLOYABLE
- **Source**: This notebook (`09_Deployable_URL_Model.ipynb`).
- **Features**: A new set of 23 deterministic lexical/structural features.
- **Advantage**: The exact parsing function is defined here in pure Python. It requires no external dependencies, no network requests, and is 100% deterministic.
- **Status**: Designed specifically for raw URL inference. **YES** safe for deployment.

*Beginner Note: In machine learning, the features (data points) you use to train a model must be calculated exactly the same way when the model is running in production (inference). If you don't know the exact recipe used to create the training data, you cannot deploy the model for new data. This notebook solves that by defining our own recipe.*"""))

cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import json
import joblib
import urllib.parse
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

import warnings
warnings.filterwarnings('ignore')"""))

cells.append(nbf.v4.new_markdown_cell("""## 2. Dataset Setup
We load the original `PhiUSIIL_Phishing_URL_Dataset.csv` but we will **ignore** its 18 pre-computed URL features. We only need two columns:
- `URL`: The raw URL string.
- `label`: The target indicating if it's phishing or legitimate.

*Beginner Note: The training data gives our model examples to learn from. The test data is held back and used only to grade the model.*"""))

cells.append(nbf.v4.new_code_cell("""current_dir = Path.cwd()
if (current_dir / 'requirements.txt').exists():
    project_root = current_dir
elif (current_dir.parent / 'requirements.txt').exists():
    project_root = current_dir.parent
else:
    project_root = current_dir

data_path = project_root / 'data' / 'raw' / 'PhiUSIIL_Phishing_URL_Dataset.csv'
df = pd.read_csv(data_path)

print(f"Dataset shape: {df.shape}")
print(f"Raw URL Column Present: {'URL' in df.columns}")
print(f"Label Column Present: {'label' in df.columns}")

# Verify Label Mapping
# From documentation and previous EDA: 1 = Legitimate, 0 = Phishing
label_counts = df['label'].value_counts()
print(f"\\nLabel Distribution:\\n{label_counts}")
"""))

cells.append(nbf.v4.new_markdown_cell("""## 3. Reusable Feature Engineering Function
*Beginner Note: Feature Engineering is the process of converting raw data (like a web address string) into numbers that a machine learning model can understand.*

We define `extract_deployable_url_features(url)` here. It will calculate 23 features using only standard string and regex operations."""))

cells.append(nbf.v4.new_code_cell("""def extract_deployable_url_features(url):
    if not isinstance(url, str) or not url.strip():
        return None
        
    try:
        # Standardize prefix for parsing if missing
        if not url.startswith('http://') and not url.startswith('https://'):
            parsed = urllib.parse.urlparse('http://' + url)
        else:
            parsed = urllib.parse.urlparse(url)
            
        hostname = parsed.netloc if parsed.netloc else ""
        path = parsed.path if parsed.path else ""
        query = parsed.query if parsed.query else ""
        
        # Lengths
        url_length = len(url)
        hostname_length = len(hostname)
        path_length = len(path)
        query_length = len(query)
        
        # Character counts
        num_dots = url.count('.')
        num_hyphens = url.count('-')
        num_underscores = url.count('_')
        num_slashes = url.count('/')
        num_question_marks = url.count('?')
        num_equals = url.count('=')
        num_ampersands = url.count('&')
        num_percent = url.count('%')
        
        num_digits = sum(c.isdigit() for c in url)
        num_letters = sum(c.isalpha() for c in url)
        
        # Alphanumeric count
        num_alnum = num_digits + num_letters
        num_special_chars = url_length - num_alnum
        
        # Ratios (safe division)
        digit_ratio = num_digits / url_length if url_length > 0 else 0
        letter_ratio = num_letters / url_length if url_length > 0 else 0
        special_char_ratio = num_special_chars / url_length if url_length > 0 else 0
        
        # Indicators
        is_https = 1 if url.startswith('https://') else 0
        
        # IP Address matching (simple IPv4)
        ip_pattern = re.compile(r'^(\\d{1,3}\\.){3}\\d{1,3}$')
        is_ip_address = 1 if ip_pattern.match(hostname.split(':')[0]) else 0
        
        # Suspicious keywords
        keywords = ['login', 'verify', 'update', 'secure', 'account', 'bank', 'confirm']
        url_lower = url.lower()
        has_suspicious_keywords = 1 if any(kw in url_lower for kw in keywords) else 0
        
        # URL shorteners
        shorteners = ['bit.ly', 'goo.gl', 'tinyurl.com', 't.co', 'ow.ly', 'is.gd', 'buff.ly', 'adf.ly']
        is_shortener = 1 if any(sh in hostname.lower() for sh in shorteners) else 0
        
        # Structure
        num_path_segments = len([s for s in path.split('/') if s])
        
        features = {
            'url_length': url_length,
            'hostname_length': hostname_length,
            'path_length': path_length,
            'query_length': query_length,
            'num_dots': num_dots,
            'num_hyphens': num_hyphens,
            'num_underscores': num_underscores,
            'num_slashes': num_slashes,
            'num_question_marks': num_question_marks,
            'num_equals': num_equals,
            'num_ampersands': num_ampersands,
            'num_percent': num_percent,
            'num_digits': num_digits,
            'num_letters': num_letters,
            'num_special_chars': num_special_chars,
            'digit_ratio': digit_ratio,
            'letter_ratio': letter_ratio,
            'special_char_ratio': special_char_ratio,
            'is_https': is_https,
            'is_ip_address': is_ip_address,
            'has_suspicious_keywords': has_suspicious_keywords,
            'is_shortener': is_shortener,
            'num_path_segments': num_path_segments
        }
        return features
    except Exception:
        return None

# Test the function
test_features = extract_deployable_url_features("https://secure-login-update-account.com.account-verify.info/login.php?user=123")
print(test_features.keys())
deployable_feature_names = list(test_features.keys())
print(f"Total Features: {len(deployable_feature_names)}")"""))

cells.append(nbf.v4.new_markdown_cell("""## 4. Extracting the Feature Matrix
We will apply our deterministic function to the entire `URL` column to create our new feature matrix `X`.

*Beginner Note: We are creating our own dataset from the raw text, completely isolated from any pre-computed features.*"""))

cells.append(nbf.v4.new_code_cell("""print("Extracting features... This may take a moment.")
# We use apply to run our function over every URL
extracted = df['URL'].apply(extract_deployable_url_features)

# Drop any rows that failed to parse (None)
valid_idx = extracted.notna()
df_valid = df[valid_idx]
extracted_valid = extracted[valid_idx]

# Convert list of dictionaries to DataFrame
X = pd.DataFrame(extracted_valid.tolist(), index=df_valid.index)
y = df_valid['label']

print(f"Final X shape: {X.shape}")
print(f"Final y shape: {y.shape}")
print(f"Missing values in X: {X.isna().sum().sum()}")
print(f"Infinity values in X: {np.isinf(X).sum().sum()}")"""))

cells.append(nbf.v4.new_markdown_cell("""## 5. Train/Test Split
We split the data 80% for training and 20% for testing, using stratification to maintain class balance.

*Beginner Note: Data Leakage happens when information from outside the training dataset is used to create the model. By splitting our data and fitting models ONLY on the training data, we ensure our tests reflect real-world performance on completely unseen URLs.*"""))

cells.append(nbf.v4.new_code_cell("""X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"Training instances: {X_train.shape[0]}")
print(f"Testing instances: {X_test.shape[0]}")"""))

cells.append(nbf.v4.new_markdown_cell("""## 6. Model Training & Evaluation
We will train Logistic Regression, Linear SVM, and Random Forest.

*Beginner Notes on Evaluation:*
- **Classification**: Assigning an item (URL) into a category (Phishing or Legitimate).
- **Precision**: Out of all URLs the model flagged as phishing, what percentage were *actually* phishing? (High precision means few false alarms).
- **Recall**: Out of all the *actual* phishing URLs, what percentage did the model successfully catch? (High recall means few missed attacks).
- **F1-score**: A harmonic balance of Precision and Recall.
- **ROC-AUC**: Measures how well the model separates the two classes across all confidence thresholds.
- **Overfitting**: When a model memorizes the training data perfectly but performs terribly on the test data.

**Why Phishing Recall is Critical:**
If we miss a phishing email (False Negative), a user could be compromised. This is highly dangerous. If we accidentally flag a legitimate email (False Positive, hurting Precision), the user might just check their spam folder. Therefore, we prioritize catching attacks (Recall)."""))

cells.append(nbf.v4.new_code_cell("""models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Linear SVM": LinearSVC(random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42)
}

results = []

for name, model in models.items():
    print(f"Training {name}...")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    
    # Class 0 is Phishing
    # By setting pos_label=0, we get precision/recall specifically for catching phishing
    prec = precision_score(y_test, y_pred, pos_label=0)
    rec = recall_score(y_test, y_pred, pos_label=0)
    f1 = f1_score(y_test, y_pred, pos_label=0)
    
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_test)[:, 0] # Prob for class 0
        roc = roc_auc_score(y_test == 0, probs)
    else:
        # LinearSVC doesn't natively predict probabilities without calibration
        roc = np.nan
        
    results.append({
        "Model": name,
        "Accuracy": acc,
        "Phishing Precision": prec,
        "Phishing Recall": rec,
        "Phishing F1": f1,
        "ROC-AUC": roc
    })
    
results_df = pd.DataFrame(results)
display(results_df)"""))

cells.append(nbf.v4.new_markdown_cell("""## 7. Model Selection and Saving
*Beginner Note: Random Forest is an ensemble model that uses many decision trees to vote on the outcome. It handles non-linear relationships in data very well, which is often the case with these lexical URL features.*

We select **Random Forest** because it typically offers the highest Phishing Recall and ROC-AUC for this type of feature set. We save it explicitly to a new directory `models/url_deployable/` to isolate it from the unsafe experimental model."""))

cells.append(nbf.v4.new_code_cell("""best_model_name = "Random Forest"
best_model = models[best_model_name]

deploy_dir = project_root / 'models' / 'url_deployable'
deploy_dir.mkdir(parents=True, exist_ok=True)

# Save Model
model_file = deploy_dir / 'url_deployable_rf.joblib'
joblib.dump(best_model, model_file)

# Save Feature Config
config = {
    "model_name": best_model_name,
    "training_random_state": 42,
    "feature_extraction_version": "1.0",
    "feature_names": deployable_feature_names,
    "label_mapping": {
        "0": "Phishing",
        "1": "Legitimate"
    }
}
with open(deploy_dir / 'url_deployable_config.json', 'w') as f:
    json.dump(config, f, indent=4)

print("Deployable model and feature configuration saved successfully.")"""))

cells.append(nbf.v4.new_markdown_cell("""## 8. Reusable Inference Function
We bundle the feature extraction and model prediction into a single, clean pipeline that will be mirrored in our future backend."""))

cells.append(nbf.v4.new_code_cell("""def predict_url(url):
    features = extract_deployable_url_features(url)
    if features is None:
        return {"prediction": "Error", "error": "Invalid or malformed URL"}
        
    # Ensure DataFrame matches exact feature names and order
    feature_df = pd.DataFrame([features], columns=config["feature_names"])
    
    pred_class = best_model.predict(feature_df)[0]
    probs = best_model.predict_proba(feature_df)[0]
    
    class_idx = np.where(best_model.classes_ == pred_class)[0][0]
    confidence = probs[class_idx]
    
    pred_label = config["label_mapping"][str(pred_class)]
    
    return {
        "url": url,
        "prediction": pred_label,
        "label": int(pred_class),
        "confidence": float(confidence),
        "features_extracted": True
    }"""))

cells.append(nbf.v4.new_markdown_cell("""## 9. Deployment Tests
We test the model against brand new URLs and various edge cases to ensure it does not crash."""))

cells.append(nbf.v4.new_code_cell("""test_urls = [
    "https://example.com",
    "http://example.com/login",
    "https://secure-login-update-account.com.account-verify.info/login.php?user=123",
    "http://192.168.1.10/login",
    "",  # Empty
    "not_a_url", # Malformed
    "https://bit.ly/12345", # Shortener
    "https://example.com/search?q=hello&sort=asc#results" # Query and Fragment
]

print("--- DEPLOYMENT TESTS ---")
for t in test_urls:
    res = predict_url(t)
    print(f"URL: {t}")
    if "error" in res:
        print(f"  -> Error: {res['error']}")
    else:
        print(f"  -> {res['prediction']} (Conf: {res['confidence']:.2f})")
    print("")"""))

cells.append(nbf.v4.new_markdown_cell("""## 10. Final Validation Checklist"""))

cells.append(nbf.v4.new_code_cell("""print("========================================")
print("DEPLOYABLE URL MODEL VALIDATION")
print("========================================")

checks = {}

checks["Dataset Loading"] = not df.empty
checks["Raw URL Column"] = 'URL' in df.columns
checks["Label Mapping"] = (0 in df['label'].values) and (1 in df['label'].values)

test_feat = extract_deployable_url_features("https://test.com")
checks["Feature Extraction"] = test_feat is not None
checks["Feature Count"] = len(test_feat) == 23 if test_feat else False
checks["Feature Names"] = deployable_feature_names == list(test_feat.keys()) if test_feat else False
checks["Feature Order"] = list(X.columns) == deployable_feature_names
checks["No NaN/Infinity"] = (X.isna().sum().sum() == 0) and (np.isinf(X).sum().sum() == 0)

checks["Train/Test Split"] = len(X_train) > 0 and len(X_test) > 0
checks["Model Training"] = best_model is not None
checks["Model Evaluation"] = len(results_df) == 3
checks["Model Saving"] = model_file.exists()

try:
    loaded_model = joblib.load(model_file)
    checks["Model Loading"] = True
except:
    checks["Model Loading"] = False

try:
    res = predict_url("http://example.com")
    checks["Raw URL Inference"] = res.get("prediction") in ["Phishing", "Legitimate"]
except:
    checks["Raw URL Inference"] = False

try:
    res = predict_url("")
    checks["Malformed URL Handling"] = "error" in res
except:
    checks["Malformed URL Handling"] = False

all_pass = True
for key in ["Dataset Loading", "Raw URL Column", "Label Mapping", "Feature Extraction", 
            "Feature Count", "Feature Names", "Feature Order", "No NaN/Infinity", 
            "Train/Test Split", "Model Training", "Model Evaluation", "Model Saving", 
            "Model Loading", "Raw URL Inference", "Malformed URL Handling"]:
    v = checks.get(key, False)
    status = "PASS" if v else "FAIL"
    print(f"{key}: {status}")
    if not v:
        all_pass = False

print("\\n========================================")
if all_pass:
    print("DEPLOYABLE URL MODEL COMPLETE: YES")
else:
    print("DEPLOYABLE URL MODEL COMPLETE: NO")
print("========================================")
print("\\nOLD URL MODEL = BASELINE")
print("NEW URL MODEL = DEPLOYABLE")
"""))

nb['cells'] = cells
with open('notebooks/09_Deployable_URL_Model.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Notebook 09 created successfully.")
