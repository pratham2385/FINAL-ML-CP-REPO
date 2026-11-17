"""
src/models/predictor.py
Encapsulates model loading, feature transformation, and inference for both
the Email Spam detector and the URL Phishing detector.
"""

import os
import re
import json
import warnings
import joblib
import pandas as pd
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from src.features.email_preprocessor import preprocess_email_text
from src.features.url_feature_extractor import extract_url_features, DEPLOYABLE_URL_FEATURES

warnings.filterwarnings("ignore", category=UserWarning)

DEFAULT_MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "models"))
DEFAULT_EMAIL_THRESHOLD = 0.43

class EmailPredictor:
    """Loads and serves the Multi-Corpus Multinomial Naive Bayes Email Spam Model."""

    def __init__(self, models_dir: str = DEFAULT_MODELS_DIR, threshold: Optional[float] = None):
        model_path = os.path.join(models_dir, "email_model.joblib")
        tfidf_path = os.path.join(models_dir, "email_tfidf.joblib")
        metadata_path = os.path.join(models_dir, "model_metadata.json")

        if not os.path.exists(model_path) or not os.path.exists(tfidf_path):
            raise FileNotFoundError(f"Email model artifacts not found in {models_dir}. Please run model training first.")

        self.model = joblib.load(model_path)
        self.tfidf = joblib.load(tfidf_path)

        # Determine decision threshold
        if threshold is not None:
            self.threshold = float(threshold)
        elif os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                self.threshold = float(meta.get("email_model", {}).get("decision_threshold", DEFAULT_EMAIL_THRESHOLD))
            except Exception:
                self.threshold = DEFAULT_EMAIL_THRESHOLD
        else:
            self.threshold = DEFAULT_EMAIL_THRESHOLD

        # Map class indices dynamically from model.classes_
        classes = list(self.model.classes_)
        self.idx_ham = classes.index(0) if 0 in classes else 0
        self.idx_spam = classes.index(1) if 1 in classes else 1

    def predict(self, subject: Optional[str] = "", message: Optional[str] = "") -> Dict[str, Any]:
        """
        Classifies an email as Spam (1) or Ham (0) with calibrated probability confidence
        evaluated against the optimized decision threshold (default 0.42).
        """
        cleaned_text = preprocess_email_text(subject, message)

        if not cleaned_text:
            return {
                "label": "Ham",
                "is_spam": False,
                "spam_probability": 0.0,
                "ham_probability": 1.0,
                "confidence_percent": 100.0,
                "cleaned_text_preview": ""
            }

        tfidf_features = self.tfidf.transform([cleaned_text])
        probabilities = self.model.predict_proba(tfidf_features)[0]
        p_ham = float(probabilities[self.idx_ham])
        p_spam = float(probabilities[self.idx_spam])

        is_spam = p_spam >= self.threshold
        label = "Spam" if is_spam else "Ham"
        confidence = p_spam if is_spam else p_ham

        return {
            "label": label,
            "is_spam": bool(is_spam),
            "spam_probability": round(p_spam, 4),
            "ham_probability": round(p_ham, 4),
            "confidence_percent": round(confidence * 100, 2),
            "cleaned_text_preview": cleaned_text[:120] + ("..." if len(cleaned_text) > 120 else "")
        }

class URLPredictor:
    """Loads and serves the Tuned Random Forest URL Phishing Model."""

    def __init__(self, models_dir: str = DEFAULT_MODELS_DIR):
        model_path = os.path.join(models_dir, "url_model.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"URL model artifact not found in {models_dir}. Please run model training first.")

        self.model = joblib.load(model_path)
        self.feature_names = DEPLOYABLE_URL_FEATURES

    def predict(self, url: str) -> Dict[str, Any]:
        """
        Classifies a URL as Phishing (0) or Legitimate (1) with calibrated probability and confidence.
        Note ground-truth mapping: Class 0 = Phishing, Class 1 = Legitimate.
        Employs dual-level evaluation (canonical domain root + full URL lexical features)
        to resolve PhiUSIIL root-domain training biases while preserving genuine model variance.
        """
        features_dict = extract_url_features(url)
        feature_df = pd.DataFrame([features_dict])[self.feature_names]

        prob_full = self.model.predict_proba(feature_df)[0]
        p_phish_full = float(prob_full[0])
        p_legit_full = float(prob_full[1])

        # Canonical domain root evaluation (mitigating PhiUSIIL root-domain-only training artifact)
        p = urlparse(url if '://' in url else 'http://' + url)
        host = p.hostname or ''
        scheme = p.scheme or 'http'
        is_ip = bool(re.match(r'^\d+\.\d+\.\d+\.\d+$', host))

        if not is_ip and host and not host.startswith('www.') and len(host.split('.')) >= 2:
            norm_host = 'www.' + host
        else:
            norm_host = host
        root_url = f'{scheme}://{norm_host}'

        feats_root = extract_url_features(root_url)
        df_root = pd.DataFrame([feats_root])[self.feature_names]
        prob_root = self.model.predict_proba(df_root)[0]
        p_phish_root = float(prob_root[0])
        p_legit_root = float(prob_root[1])

        # Specific path/payload risk factors
        is_ip_domain = bool(is_ip or features_dict.get('IsDomainIP', 0) == 1)
        has_obfuscation = bool(features_dict.get('HasObfuscation', 0) == 1 or features_dict.get('NoOfObfuscatedChar', 0) > 0 or '@' in url)
        dangerous_extensions = ('.exe', '.scr', '.bat', '.cmd', '.vbs', '.apk', '.msi', '.ps1', '.pif', '.hta')
        path_lower = (p.path or '').lower()
        has_executable_payload = any(path_lower.endswith(ext) or (ext + '?') in url.lower() for ext in dangerous_extensions)

        # Dual-level probability calibration:
        # If the domain root is classified by the model as legitimate (> 0.50 legit) and is not an IP:
        if p_legit_root > 0.50 and not is_ip_domain:
            if has_executable_payload or has_obfuscation:
                # Active malicious lure or executable on an otherwise benign host
                p_phishing = p_phish_full
                p_legitimate = 1.0 - p_phishing
            else:
                # Clean browsing path on legitimate domain: uses genuine model probability of the domain
                p_phishing = p_phish_root
                p_legitimate = p_legit_root
        else:
            # Domain root is suspicious or phishing: uses genuine model probability of the root domain
            p_phishing = p_phish_root
            p_legitimate = p_legit_root

        is_phishing = p_phishing >= 0.5
        label = "Phishing" if is_phishing else "Legitimate"
        confidence = p_phishing if is_phishing else p_legitimate

        # Operational risk score (0.0 to 100.0)
        if is_ip_domain or has_obfuscation or has_executable_payload:
            risk_score = round(max(85.0, p_phishing * 100), 1)
        else:
            risk_score = round(p_phishing * 100, 1)

        verdict = "Phishing URL Detected" if is_phishing else "Legitimate URL"
        recommended_action = "BLOCK" if is_phishing else "ALLOW"

        return {
            "url": url,
            "label": label,
            "is_phishing": bool(is_phishing),
            "phishing_probability": round(p_phishing, 4),
            "legitimate_probability": round(p_legitimate, 4),
            "confidence_percent": round(confidence * 100, 2),
            "risk_score": risk_score,
            "verdict": verdict,
            "recommended_action": recommended_action,
            "features": features_dict
        }

    def predict_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Classifies a list of URLs."""
        return [self.predict(u) for u in urls]
