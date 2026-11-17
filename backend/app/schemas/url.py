"""
backend/app/schemas/url.py
Pydantic schemas for the standalone URL analysis endpoint.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator

class URLAnalyzeRequest(BaseModel):
    """Input payload for single URL phishing classification."""
    url: str = Field(..., description="Target URL to analyze for phishing threats", json_schema_extra={"example": "https://secure-login.bank-update.com/verify"})

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        trimmed = (v or "").strip()
        if not trimmed:
            raise ValueError("URL cannot be empty or whitespace.")
        
        # Check basic URL validity
        candidate = trimmed if "://" in trimmed else f"http://{trimmed}"
        parsed = urlparse(candidate)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL structure: '{trimmed}'. A valid domain or host is required.")
        return trimmed

class URLAnalyzeResponse(BaseModel):
    """Output analysis payload for standalone URL inspection."""
    id: Optional[int] = Field(default=None, description="Database history ID", json_schema_extra={"example": 1})
    url: str = Field(..., description="The analyzed URL", json_schema_extra={"example": "https://secure-login.bank-update.com/verify"})
    classification: str = Field(..., description="'Phishing' or 'Legitimate'", json_schema_extra={"example": "Phishing"})
    is_phishing: bool = Field(..., description="True if classified as malicious phishing", json_schema_extra={"example": True})
    phishing_probability: float = Field(..., description="Probability of phishing (0.0 to 1.0)", json_schema_extra={"example": 0.985})
    legitimate_probability: float = Field(..., description="Probability of legitimate (0.0 to 1.0)", json_schema_extra={"example": 0.015})
    confidence_percent: float = Field(..., description="Prediction confidence score", json_schema_extra={"example": 98.5})
    verdict: str = Field(..., description="High-level threat assessment verdict", json_schema_extra={"example": "Phishing URL Detected"})
    risk_score: float = Field(..., description="Risk score from 0.0 (safe) to 100.0 (dangerous)", json_schema_extra={"example": 98.5})
    recommended_action: str = Field(..., description="'BLOCK' or 'ALLOW'", json_schema_extra={"example": "BLOCK"})
    features: Dict[str, Any] = Field(..., description="18 deployable lexical features extracted from the URL")
