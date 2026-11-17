"""
backend/app/schemas/email.py
Pydantic schemas for the email analysis endpoint.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from backend.app.schemas.common import EmailAnalysisResult, URLDetail, URLSummary, PhishingIntentResult

class EmailAnalyzeRequest(BaseModel):
    """Input payload for email spam and embedded link analysis."""
    subject: Optional[str] = Field(default="", description="Email subject line", json_schema_extra={"example": "Urgent Account Verification Required"})
    message: Optional[str] = Field(default="", description="Email body content", json_schema_extra={"example": "Please click here to verify your account: http://login-secure-verify.com"})
    body: Optional[str] = Field(default=None, description="Alias for message field", json_schema_extra={"example": None})
    sender: Optional[str] = Field(default=None, description="Optional sender header or email address ('From')", json_schema_extra={"example": "security@paypal-update.com"})

    @model_validator(mode="after")
    def validate_content_present(self):
        if not self.message and self.body:
            self.message = self.body
        
        subj = (self.subject or "").strip()
        msg = (self.message or "").strip()
        
        if not subj and not msg:
            raise ValueError("At least one of 'subject' or 'message' (body) must contain non-whitespace text.")
        return self

class EmailAnalyzeResponse(BaseModel):
    """Complete analysis response for an analyzed email."""
    # Database history reference
    id: Optional[int] = Field(default=None, description="Database history ID", json_schema_extra={"example": 1})

    # Top-level direct fields for fast dashboard rendering
    verdict: str = Field(..., description="Overall threat verdict", json_schema_extra={"example": "Phishing Attack Detected"})
    threat_level: str = Field(..., description="Risk tier: CRITICAL, HIGH, MEDIUM, LOW_SUSPICIOUS, SAFE", json_schema_extra={"example": "CRITICAL"})
    risk_score: float = Field(..., description="Overall numerical risk score (0.0 to 100.0)", json_schema_extra={"example": 94.5})
    recommended_action: str = Field(..., description="Actionable mitigation advice", json_schema_extra={"example": "QUARANTINE_AND_BLOCK"})
    
    # Email-specific direct fields
    email_classification: str = Field(..., description="'Spam' or 'Ham'", json_schema_extra={"example": "Spam"})
    spam_probability: float = Field(..., description="Probability of spam (0.0 to 1.0)", json_schema_extra={"example": 0.8842})
    confidence_percent: float = Field(..., description="Confidence percentage for email text classification", json_schema_extra={"example": 88.42})
    
    # URL analysis direct fields
    extracted_urls: List[str] = Field(default_factory=list, description="All URLs discovered within email body")
    
    # Structured nested details
    email_analysis: EmailAnalysisResult = Field(..., description="Granular text model metrics")
    url_summary: URLSummary = Field(..., description="Aggregated URL statistics")
    url_details: List[URLDetail] = Field(default_factory=list, description="Per-URL detailed breakdown")
    
    # Phishing Intent & Explainability Layer
    overall_security_verdict: Optional[str] = Field(default=None, description="Standard security verdict: SAFE, SUSPICIOUS, MALICIOUS", json_schema_extra={"example": "MALICIOUS"})
    verdict_explanation: Optional[str] = Field(default=None, description="Detailed explanation of how the overall verdict was assigned")
    evidence_summary: List[str] = Field(default_factory=list, description="Aggregated key threat and intent indicators")
    phishing_intent_analysis: Optional[PhishingIntentResult] = Field(default=None, description="Explainable intent layer analysis")
