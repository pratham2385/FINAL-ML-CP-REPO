"""
backend/app/schemas/file.py
Pydantic schemas for .eml file upload and security analysis.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.common import EmailAnalysisResult, URLDetail, URLSummary, PhishingIntentResult

class EMLMetadata(BaseModel):
    """Metadata extracted from the RFC 822 email header."""
    filename: str = Field(..., description="Uploaded filename", json_schema_extra={"example": "suspicious_notice.eml"})
    file_size_bytes: int = Field(..., description="File size in bytes", json_schema_extra={"example": 4096})
    sender: Optional[str] = Field(default=None, description="Sender header ('From')", json_schema_extra={"example": "billing@paypal-support-update.com"})
    recipient: Optional[str] = Field(default=None, description="Recipient header ('To')", json_schema_extra={"example": "target_user@example.com"})
    date: Optional[str] = Field(default=None, description="Date header", json_schema_extra={"example": "Mon, 16 Nov 2026 12:00:00 +0000"})
    subject: Optional[str] = Field(default=None, description="Subject line parsed from file", json_schema_extra={"example": "Your account has been suspended"})
    message_id: Optional[str] = Field(default=None, description="Message-ID header", json_schema_extra={"example": "<123456@mail.example.com>"})

class FileAnalyzeResponse(BaseModel):
    """Analysis result for an uploaded .eml file."""
    id: Optional[int] = Field(default=None, description="Database history ID", json_schema_extra={"example": 1})
    eml_metadata: EMLMetadata = Field(..., description="Parsed RFC 822 metadata")
    verdict: str = Field(..., description="Composite threat verdict", json_schema_extra={"example": "Phishing Attack Detected"})
    threat_level: str = Field(..., description="Threat tier: CRITICAL, HIGH, MEDIUM, LOW_SUSPICIOUS, SAFE", json_schema_extra={"example": "CRITICAL"})
    overall_risk_score: float = Field(..., description="Risk score from 0.0 to 100.0", json_schema_extra={"example": 95.0})
    recommended_action: str = Field(..., description="Prescribed action", json_schema_extra={"example": "QUARANTINE_AND_BLOCK"})
    
    email_classification: str = Field(..., description="'Spam' or 'Ham'", json_schema_extra={"example": "Spam"})
    spam_probability: float = Field(..., description="Spam probability", json_schema_extra={"example": 0.912})
    confidence_percent: float = Field(..., description="Confidence percentage", json_schema_extra={"example": 91.2})
    
    extracted_urls: List[str] = Field(default_factory=list, description="Extracted URLs")
    email_analysis: EmailAnalysisResult = Field(..., description="Granular text model metrics")
    url_summary: URLSummary = Field(..., description="Aggregated URL statistics")
    url_details: List[URLDetail] = Field(default_factory=list, description="Per-URL detailed breakdown")

    # Phishing Intent & Explainability Layer
    overall_security_verdict: Optional[str] = Field(default=None, description="Standard security verdict: SAFE, SUSPICIOUS, MALICIOUS", json_schema_extra={"example": "MALICIOUS"})
    verdict_explanation: Optional[str] = Field(default=None, description="Detailed explanation of how the overall verdict was assigned")
    evidence_summary: List[str] = Field(default_factory=list, description="Aggregated key threat and intent indicators")
    phishing_intent_analysis: Optional[PhishingIntentResult] = Field(default=None, description="Explainable intent layer analysis")


class BatchFileItemResult(BaseModel):
    """Analysis result or error status for a single file within a batch."""
    filename: str = Field(..., description="Uploaded filename", json_schema_extra={"example": "alert.eml"})
    status: str = Field(..., description="Processing status: 'completed' or 'failed'", json_schema_extra={"example": "completed"})
    file_size_bytes: int = Field(default=0, description="File size in bytes", json_schema_extra={"example": 4096})
    id: Optional[int] = Field(default=None, description="Database history ID", json_schema_extra={"example": 1})
    eml_metadata: Optional[EMLMetadata] = Field(default=None, description="Parsed RFC 822 metadata")
    verdict: Optional[str] = Field(default=None, description="Composite threat verdict", json_schema_extra={"example": "MALICIOUS"})
    threat_level: Optional[str] = Field(default=None, description="Threat tier: CRITICAL, HIGH, MEDIUM, LOW_SUSPICIOUS, SAFE", json_schema_extra={"example": "CRITICAL"})
    overall_risk_score: Optional[float] = Field(default=None, description="Risk score from 0.0 to 100.0", json_schema_extra={"example": 95.0})
    recommended_action: Optional[str] = Field(default=None, description="Prescribed action", json_schema_extra={"example": "QUARANTINE_AND_BLOCK"})
    email_classification: Optional[str] = Field(default=None, description="'Spam' or 'Ham'", json_schema_extra={"example": "Spam"})
    spam_probability: Optional[float] = Field(default=None, description="Spam probability", json_schema_extra={"example": 0.912})
    ham_probability: Optional[float] = Field(default=None, description="Ham probability", json_schema_extra={"example": 0.088})
    confidence_percent: Optional[float] = Field(default=None, description="Confidence percentage", json_schema_extra={"example": 91.2})
    extracted_urls: List[str] = Field(default_factory=list, description="Extracted URLs")
    email_analysis: Optional[EmailAnalysisResult] = Field(default=None, description="Granular text model metrics")
    url_summary: Optional[URLSummary] = Field(default=None, description="Aggregated URL statistics")
    url_details: List[URLDetail] = Field(default_factory=list, description="Per-URL detailed breakdown")
    overall_security_verdict: Optional[str] = Field(default=None, description="Standard security verdict: SAFE, SUSPICIOUS, MALICIOUS")
    verdict_explanation: Optional[str] = Field(default=None, description="Detailed explanation of how the overall verdict was assigned")
    evidence_summary: List[str] = Field(default_factory=list, description="Aggregated key threat and intent indicators")
    phishing_intent_analysis: Optional[PhishingIntentResult] = Field(default=None, description="Explainable intent layer analysis")
    error_message: Optional[str] = Field(default=None, description="Error detail if status is 'failed'", json_schema_extra={"example": "Unsupported file format"})


class BatchFileAnalyzeSummary(BaseModel):
    """Aggregated summary of batch email file analysis."""
    total_files: int = Field(..., description="Total files submitted in batch", json_schema_extra={"example": 10})
    successful_count: int = Field(..., description="Successfully parsed and analyzed files", json_schema_extra={"example": 9})
    failed_count: int = Field(..., description="Failed or skipped files", json_schema_extra={"example": 1})
    ham_count: int = Field(..., description="Files classified as Ham", json_schema_extra={"example": 6})
    spam_count: int = Field(..., description="Files classified as Spam", json_schema_extra={"example": 3})
    total_size_bytes: int = Field(..., description="Combined file size in bytes", json_schema_extra={"example": 524288})
    total_processing_time_ms: float = Field(..., description="Total batch elapsed time in milliseconds", json_schema_extra={"example": 450.2})


class BatchFileAnalyzeResponse(BaseModel):
    """Response payload for multi-file batch email analysis."""
    summary: BatchFileAnalyzeSummary = Field(..., description="Batch summary statistics")
    results: List[BatchFileItemResult] = Field(..., description="List of per-file analysis results")
