"""
backend/app/schemas/common.py
Shared Pydantic models and data structures for analysis endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class EmailAnalysisResult(BaseModel):
    """Granular NLP classification output for email content."""
    label: str = Field(..., description="'Spam' or 'Ham'", json_schema_extra={"example": "Ham"})
    is_spam: bool = Field(..., description="True if classified as spam", json_schema_extra={"example": False})
    spam_probability: float = Field(..., description="Calibrated probability of spam (0.0 to 1.0)", json_schema_extra={"example": 0.0123})
    ham_probability: float = Field(..., description="Calibrated probability of ham (0.0 to 1.0)", json_schema_extra={"example": 0.9877})
    confidence_percent: float = Field(..., description="Confidence percentage", json_schema_extra={"example": 98.77})
    cleaned_text_preview: str = Field(..., description="Preview of cleaned text passed into model", json_schema_extra={"example": "Quarterly project review meeting..."})

class URLDetail(BaseModel):
    """Detailed lexical classification and features for a single URL."""
    url: str = Field(..., description="Target URL analyzed", json_schema_extra={"example": "https://www.paypal.com"})
    label: str = Field(..., description="'Phishing' or 'Legitimate'", json_schema_extra={"example": "Legitimate"})
    is_phishing: bool = Field(..., description="True if classified as phishing", json_schema_extra={"example": False})
    phishing_probability: float = Field(..., description="Probability of phishing (0.0 to 1.0)", json_schema_extra={"example": 0.015})
    legitimate_probability: float = Field(..., description="Probability of legitimate (0.0 to 1.0)", json_schema_extra={"example": 0.985})
    confidence_percent: float = Field(..., description="Confidence percentage", json_schema_extra={"example": 98.5})
    features: Optional[Dict[str, Any]] = Field(default=None, description="Extracted lexical features")

class URLSummary(BaseModel):
    """Summary of all extracted URLs in an email."""
    total_urls_found: int = Field(..., description="Total URLs extracted from message", json_schema_extra={"example": 1})
    phishing_urls_count: int = Field(..., description="Number of phishing URLs detected", json_schema_extra={"example": 0})
    phishing_urls: List[str] = Field(default_factory=list, description="List of detected phishing URLs")
    max_phishing_probability: float = Field(..., description="Highest phishing probability among all URLs", json_schema_extra={"example": 0.015})

class PhishingIntentResult(BaseModel):
    """Explainable output from the phishing intent detection layer."""
    has_phishing_intent: bool = Field(..., description="True if deceptive phishing intent patterns were detected", json_schema_extra={"example": True})
    primary_intent: str = Field(..., description="Primary detected intent category", json_schema_extra={"example": "CREDENTIAL_THEFT"})
    intent_categories_detected: List[str] = Field(default_factory=list, description="All triggered intent categories")
    intent_risk_level: str = Field(..., description="Intent risk tier: 'HIGH', 'MEDIUM', 'LOW', or 'NONE'", json_schema_extra={"example": "HIGH"})
    intent_score: float = Field(..., description="Intent threat score from 0.0 to 100.0", json_schema_extra={"example": 85.0})
    detected_signals: List[str] = Field(default_factory=list, description="Human-readable social engineering signals discovered")
    evidence: List[str] = Field(default_factory=list, description="Specific textual and contextual evidence rationales")
    sender_indicators: Optional[Dict[str, Any]] = Field(default=None, description="Sender address and impersonation diagnostics")
    mitigating_factors: List[str] = Field(default_factory=list, description="Legitimate benign markers that tempered the risk score")
