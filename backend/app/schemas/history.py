"""
backend/app/schemas/history.py
Pydantic schemas for database analysis history endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AnalysisHistorySummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Summarized historical record for listing and pagination."""
    id: int = Field(..., description="Unique record identifier", json_schema_extra={"example": 1})
    analysis_type: str = Field(..., description="'email', 'url', or 'file'", json_schema_extra={"example": "email"})
    created_at: datetime = Field(..., description="UTC creation timestamp")
    subject: Optional[str] = Field(default=None, description="Email subject if applicable", json_schema_extra={"example": "Project Sync"})
    submitted_url: Optional[str] = Field(default=None, description="Submitted URL if standalone", json_schema_extra={"example": None})
    email_prediction: Optional[str] = Field(default=None, description="'Ham' or 'Spam'", json_schema_extra={"example": "Ham"})
    spam_probability: Optional[float] = Field(default=None, description="Spam probability", json_schema_extra={"example": 0.02})
    url_count: int = Field(..., description="Count of URLs analyzed", json_schema_extra={"example": 1})
    overall_verdict: str = Field(..., description="Verdict outcome", json_schema_extra={"example": "Clean / Legitimate"})
    threat_level: str = Field(..., description="Threat tier", json_schema_extra={"example": "SAFE"})
    risk_score: float = Field(..., description="Composite risk score (0-100)", json_schema_extra={"example": 2.0})
    recommended_action: str = Field(..., description="Prescribed action", json_schema_extra={"example": "ALLOW"})

class AnalysisHistoryListResponse(BaseModel):
    """Paginated response containing historical analysis records."""
    total: int = Field(..., description="Total count matching filter criteria", json_schema_extra={"example": 42})
    limit: int = Field(..., description="Items requested per page", json_schema_extra={"example": 20})
    offset: int = Field(..., description="Offset from beginning", json_schema_extra={"example": 0})
    items: List[AnalysisHistorySummaryItem] = Field(..., description="List of summarized history records")

class AnalysisHistoryDetailResponse(AnalysisHistorySummaryItem):
    """Full detail of a historical analysis including deep results and lexical features."""
    extracted_urls: List[str] = Field(default_factory=list, description="All URLs associated with analysis")
    complete_analysis_result: Dict[str, Any] = Field(..., description="Complete ML pipeline result payload")

class DeleteHistoryResponse(BaseModel):
    """Confirmation payload for deleted history record."""
    message: str = Field(..., description="Status message", json_schema_extra={"example": "Analysis history record 1 deleted successfully."})
    id: int = Field(..., description="ID of deleted record", json_schema_extra={"example": 1})

class AnalysisHistoryStatsResponse(BaseModel):
    """Aggregated statistics for security dashboard visual analytics."""
    total_analyses: int = Field(..., description="Total number of scans completed", json_schema_extra={"example": 100})
    spam_count: int = Field(..., description="Total spam communications detected", json_schema_extra={"example": 35})
    phishing_count: int = Field(..., description="Total phishing threats detected", json_schema_extra={"example": 20})
    safe_count: int = Field(..., description="Total clean/safe analyses", json_schema_extra={"example": 45})
    threat_percentage: float = Field(..., description="Percentage of scans posing a threat", json_schema_extra={"example": 55.0})
    threat_distribution: Dict[str, int] = Field(..., description="Breakdown by threat level (CRITICAL, HIGH, etc.)")
    type_distribution: Dict[str, int] = Field(..., description="Breakdown by scan type (email, url, file)")
