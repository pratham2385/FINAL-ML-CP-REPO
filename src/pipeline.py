"""
src/pipeline.py
The Master Threat Analysis Engine implementing the Multi-Representation Pipeline Architecture.
Coordinates NLP email spam scoring, embedded link extraction, lexical phishing classification,
explainable phishing-intent analysis, and centralized risk aggregation.
"""

from typing import Dict, Any, List, Optional
from src.features.url_extractor import extract_urls_from_text
from src.features.phishing_intent import PhishingIntentDetector
from src.features.risk_aggregator import SecurityRiskAggregator
from src.models.predictor import EmailPredictor, URLPredictor


class SecurityAnalysisPipeline:
    """
    End-to-end security pipeline for email and URL inspection.
    Integrates ML classifiers with an explainable phishing intent layer
    and centralized risk aggregation.
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir:
            self.email_predictor = EmailPredictor(models_dir=models_dir)
            self.url_predictor = URLPredictor(models_dir=models_dir)
        else:
            self.email_predictor = EmailPredictor()
            self.url_predictor = URLPredictor()

        self.phishing_intent_detector = PhishingIntentDetector()
        self.risk_aggregator = SecurityRiskAggregator()

    def analyze_url(self, url: str) -> Dict[str, Any]:
        """Scans an individual URL directly."""
        return self.url_predictor.predict(url)

    def analyze_email(
        self,
        subject: str = "",
        message: str = "",
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the Multi-Representation Security Pipeline on an email:
        1. Link Stream: Extracts embedded hyperlinks and classifies each with the URL model.
        2. NLP Text Stream: Evaluates spam features using TF-IDF and Naive Bayes model.
        3. Intent Stream: Evaluates social engineering, BEC, credential theft, and payment fraud lures.
        4. Centralized Aggregator: Synthesizes all streams into an explainable overall verdict (SAFE, SUSPICIOUS, MALICIOUS).
        """
        raw_combined = f"{subject} {message}"

        # 1. Embedded URL Extraction & Lexical Phishing Classification
        extracted_urls = extract_urls_from_text(raw_combined)
        url_results: List[Dict[str, Any]] = []
        max_url_phish_prob = 0.0
        phishing_urls_found = []

        for u in extracted_urls:
            url_eval = self.url_predictor.predict(u)
            url_results.append(url_eval)
            if url_eval["is_phishing"]:
                phishing_urls_found.append(u)
            if url_eval["phishing_probability"] > max_url_phish_prob:
                max_url_phish_prob = url_eval["phishing_probability"]

        url_summary = {
            "total_urls_found": len(extracted_urls),
            "phishing_urls_count": len(phishing_urls_found),
            "phishing_urls": phishing_urls_found,
            "max_phishing_probability": round(max_url_phish_prob, 4),
        }

        # 2. Email Spam Text Classification (MultinomialNB)
        email_result = self.email_predictor.predict(subject, message)

        # 3. Phishing Intent Detection Layer
        phishing_intent = self.phishing_intent_detector.analyze(
            subject=subject,
            body=message,
            sender=sender,
            extracted_urls=extracted_urls,
            url_results=url_results
        )

        # 4. Centralized Risk Aggregation
        aggregation = self.risk_aggregator.aggregate(
            email_result=email_result,
            url_summary=url_summary,
            url_details=url_results,
            phishing_intent=phishing_intent
        )

        return {
            "overall_security_verdict": aggregation["overall_security_verdict"],
            "verdict": aggregation["verdict"], # SAFE, SUSPICIOUS, MALICIOUS
            "threat_level": aggregation["threat_level"],
            "overall_risk_score": aggregation["overall_risk_score"],
            "risk_score": aggregation["overall_risk_score"], # Alias for schemas expecting risk_score
            "recommended_action": aggregation["recommended_action"],
            "verdict_explanation": aggregation["verdict_explanation"],
            "evidence_summary": aggregation["evidence_summary"],
            "email_analysis": email_result,
            "url_summary": url_summary,
            "url_details": url_results,
            "phishing_intent_analysis": phishing_intent,
        }
