"""
backend/app/db/models/history.py
SQLAlchemy model representing the persistent security analysis audit log.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Integer, String, Float, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from backend.app.db.base import Base

class AnalysisHistory(Base):
    """
    Persistent record of email, URL, and .eml threat analyses.
    Excludes raw email bodies and binary attachments by design.
    """
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    analysis_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # 'email', 'url', 'file'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    submitted_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_prediction: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 'Spam' or 'Ham'
    spam_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    url_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extracted_urls: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    overall_verdict: Mapped[str] = mapped_column(String(100), nullable=False)
    threat_level: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(100), nullable=False)
    complete_analysis_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes model instance to a dictionary."""
        return {
            "id": self.id,
            "analysis_type": self.analysis_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "subject": self.subject,
            "submitted_url": self.submitted_url,
            "email_prediction": self.email_prediction,
            "spam_probability": self.spam_probability,
            "url_count": self.url_count,
            "extracted_urls": self.extracted_urls or [],
            "overall_verdict": self.overall_verdict,
            "threat_level": self.threat_level,
            "risk_score": self.risk_score,
            "recommended_action": self.recommended_action,
            "complete_analysis_result": self.complete_analysis_result,
        }
