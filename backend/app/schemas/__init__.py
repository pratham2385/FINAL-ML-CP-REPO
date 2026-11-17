"""
backend/app/schemas/__init__.py
"""
from backend.app.schemas.common import (
    EmailAnalysisResult,
    URLDetail,
    URLSummary,
)
from backend.app.schemas.health import HealthResponse
from backend.app.schemas.email import EmailAnalyzeRequest, EmailAnalyzeResponse
from backend.app.schemas.url import URLAnalyzeRequest, URLAnalyzeResponse
from backend.app.schemas.file import FileAnalyzeResponse, EMLMetadata
from backend.app.schemas.history import (
    AnalysisHistorySummaryItem,
    AnalysisHistoryListResponse,
    AnalysisHistoryDetailResponse,
    DeleteHistoryResponse,
    AnalysisHistoryStatsResponse,
)

__all__ = [
    "EmailAnalysisResult",
    "URLDetail",
    "URLSummary",
    "HealthResponse",
    "EmailAnalyzeRequest",
    "EmailAnalyzeResponse",
    "URLAnalyzeRequest",
    "URLAnalyzeResponse",
    "FileAnalyzeResponse",
    "EMLMetadata",
    "AnalysisHistorySummaryItem",
    "AnalysisHistoryListResponse",
    "AnalysisHistoryDetailResponse",
    "DeleteHistoryResponse",
    "AnalysisHistoryStatsResponse",
]
