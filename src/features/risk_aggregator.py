"""
src/features/risk_aggregator.py
Centralized Security Risk Aggregation Engine.

Synthesizes three distinct, decoupled security signals:
1. NLP Email Spam Probability & Classification (MultinomialNB)
2. Lexical Phishing URL Probability & Classification (Random Forest)
3. Explainable Phishing Intent Analysis (Rule-based Intent Layer)

Derives standard overall security verdicts: SAFE, SUSPICIOUS, MALICIOUS
with complete explainability, threat tiering, and actionable mitigation advice.
"""

from typing import Dict, Any, List, Optional


class SecurityRiskAggregator:
    """
    Centralized risk aggregation engine applying explainable decision rules
    rather than naive mathematical probability averaging.
    """

    def __init__(
        self,
        high_phish_url_threshold: float = 0.80,
        moderate_phish_url_threshold: float = 0.45,
        high_spam_threshold: float = 0.75,
        moderate_spam_threshold: float = 0.40,
    ):
        self.high_phish_url_threshold = high_phish_url_threshold
        self.moderate_phish_url_threshold = moderate_phish_url_threshold
        self.high_spam_threshold = high_spam_threshold
        self.moderate_spam_threshold = moderate_spam_threshold

    def aggregate(
        self,
        email_result: Dict[str, Any],
        url_summary: Dict[str, Any],
        url_details: List[Dict[str, Any]],
        phishing_intent: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesizes model predictions into a coherent, standardized security verdict.

        Verdicts:
        - MALICIOUS: Confirmed attack indicators (phishing URL or high phishing intent).
        - SUSPICIOUS: Unsolicited spam, moderate intent, or borderline links.
        - SAFE: Legitimate communication free of deceptive indicators.
        """
        spam_prob = email_result.get("spam_probability", 0.0)
        is_spam = email_result.get("is_spam", False)
        email_label = email_result.get("label", "Ham")

        total_urls = url_summary.get("total_urls_found", 0)
        phishing_urls_count = url_summary.get("phishing_urls_count", 0)
        max_url_prob = url_summary.get("max_phishing_probability", 0.0)
        phishing_urls = url_summary.get("phishing_urls", [])

        has_intent = phishing_intent.get("has_phishing_intent", False)
        intent_risk = phishing_intent.get("intent_risk_level", "NONE")
        primary_intent = phishing_intent.get("primary_intent", "NONE")
        intent_score = phishing_intent.get("intent_score", 0.0)
        intent_evidence = phishing_intent.get("evidence", [])

        explanation_parts: List[str] = []
        evidence_summary: List[str] = []

        # =====================================================================
        # RULE 1: Confirmed Phishing URL (High Severity Attack)
        # =====================================================================
        # A confirmed phishing URL must NEVER result in an overall SAFE verdict.
        # Even if text was classified as HAM, this is definitively MALICIOUS.
        if phishing_urls_count > 0 or max_url_prob >= self.high_phish_url_threshold:
            verdict = "MALICIOUS"
            threat_level = "CRITICAL"
            recommended_action = "QUARANTINE_AND_BLOCK"
            
            # Risk score scaled between 85.0 and 100.0 based on URL and Intent confidence
            risk_score = round(max(85.0, min(100.0, max_url_prob * 100)), 1)
            
            bad_link = phishing_urls[0] if phishing_urls else "detected destination"
            explanation = (
                f"Malicious phishing URL detected ({bad_link}) with {max_url_prob * 100:.1f}% confidence. "
                f"The communication is classified as MALICIOUS regardless of text spam classification ({email_label})."
            )
            evidence_summary.append(f"Confirmed phishing URL: {bad_link}")
            if has_intent and intent_evidence:
                explanation += f" Correlating intent: {intent_evidence[0]}"
                evidence_summary.extend(intent_evidence[:2])

        # =====================================================================
        # RULE 2: High-Severity Phishing Intent (Linkless or Pre-link BEC / Theft)
        # =====================================================================
        # Detects credential harvesting or BEC even when URL count is 0 or URL model is uncertain.
        elif intent_risk == "HIGH":
            verdict = "MALICIOUS"
            threat_level = "HIGH"
            recommended_action = "QUARANTINE_AND_BLOCK"
            risk_score = round(max(80.0, min(95.0, intent_score)), 1)

            first_ev = intent_evidence[0] if intent_evidence else "Deceptive intent signals present"
            explanation = (
                f"High-risk phishing intent identified ({primary_intent}): {first_ev}. "
                "The message exhibits active credential theft, executive impersonation, or wire transfer coercion."
            )
            evidence_summary.extend(intent_evidence[:3])

        # =====================================================================
        # RULE 3: Moderate Phishing Intent OR Suspicious URL
        # =====================================================================
        elif intent_risk == "MEDIUM" or max_url_prob >= self.moderate_phish_url_threshold:
            verdict = "SUSPICIOUS"
            threat_level = "MEDIUM"
            recommended_action = "WARN_USER"
            
            risk_score = round(max(50.0, min(75.0, max(intent_score, max_url_prob * 100))), 1)
            
            reasons = []
            if intent_risk == "MEDIUM":
                reasons.append(f"phishing intent indicators ({primary_intent})")
                evidence_summary.extend(intent_evidence[:2])
            if max_url_prob >= self.moderate_phish_url_threshold:
                reasons.append(f"borderline URL risk ({max_url_prob * 100:.1f}%)")
                evidence_summary.append(f"Borderline URL risk: {max_url_prob * 100:.1f}%")

            explanation = (
                f"Suspicious communication detected based on {' and '.join(reasons)}. "
                "No confirmed malware or phishing URLs found, but recipient caution is advised."
            )

        # =====================================================================
        # RULE 4: Spam Email with Legitimate / No URLs & No Phishing Intent
        # =====================================================================
        # A SPAM email with legitimate URLs must NOT automatically be considered malicious.
        # It is unsolicited commercial email (spam), so overall verdict is SUSPICIOUS.
        elif is_spam and phishing_urls_count == 0 and intent_risk in ("NONE", "LOW"):
            verdict = "SUSPICIOUS"
            threat_level = "MEDIUM"
            recommended_action = "MOVE_TO_JUNK"
            
            # Bound risk score below MALICIOUS tier (50.0 - 65.0)
            risk_score = round(min(65.0, max(50.0, spam_prob * 70.0)), 1)
            
            url_note = "with legitimate embedded links" if total_urls > 0 else "without active links"
            explanation = (
                f"Classified as unsolicited bulk spam / marketing ({spam_prob * 100:.1f}% spam probability) {url_note}. "
                "No phishing intent or deceptive credential theft indicators detected. Recommended action is junk folder quarantine rather than security block."
            )
            evidence_summary.append(f"High spam probability ({spam_prob * 100:.1f}%) without phishing indicators")

        # =====================================================================
        # RULE 5: Borderline / Minor Anomalous Signals
        # =====================================================================
        elif spam_prob > self.moderate_spam_threshold or intent_risk == "LOW" or max_url_prob > 0.30:
            verdict = "SUSPICIOUS"
            threat_level = "LOW_SUSPICIOUS"
            recommended_action = "WARN_USER"
            
            risk_score = round(max(30.0, min(48.0, max(spam_prob * 50.0, intent_score))), 1)
            explanation = (
                "Mildly anomalous communication patterns observed. Does not meet high-risk threshold, "
                "but exhibits minor marketing or social engineering traits."
            )
            evidence_summary.append("Minor anomalous traits or low-level intent flags")

        # =====================================================================
        # RULE 6: Clean / Legitimate Communication
        # =====================================================================
        else:
            verdict = "SAFE"
            threat_level = "SAFE"
            recommended_action = "ALLOW"
            
            # Scaled low risk score (0.0 to 15.0)
            risk_score = round(max(0.1, max(spam_prob, max_url_prob) * 15.0), 1)
            explanation = (
                "No phishing intent, deceptive URLs, or spam patterns detected. "
                "The message conforms to legitimate correspondence."
            )
            evidence_summary.append("Clean text and link parameters verified")

        return {
            "overall_security_verdict": verdict,
            "verdict": verdict, # Direct backward-compatible alias
            "threat_level": threat_level,
            "overall_risk_score": risk_score,
            "recommended_action": recommended_action,
            "verdict_explanation": explanation,
            "evidence_summary": evidence_summary,
        }
