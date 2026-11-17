"""
backend/app/routers/history.py
API endpoints for managing persisted threat analysis history in PostgreSQL.
Provides pagination, type filtering, detailed retrieval, deletion, and dashboard metrics.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.history import AnalysisHistory
from backend.app.schemas.history import (
    AnalysisHistoryListResponse,
    AnalysisHistoryDetailResponse,
    DeleteHistoryResponse,
    AnalysisHistorySummaryItem,
    AnalysisHistoryStatsResponse,
)
from backend.app.utils.logger import logger

router = APIRouter(prefix="/history", tags=["Analysis History"])

@router.get(
    "",
    response_model=AnalysisHistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Analysis History Records",
    description="Returns paginated threat analysis audit logs with optional filtering by analysis_type ('email', 'url', 'file')."
)
async def list_history(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    offset: int = Query(default=0, ge=0, description="Offset index for pagination"),
    analysis_type: Optional[str] = Query(
        default=None,
        description="Filter records by analysis_type ('email', 'url', 'file')"
    ),
    db: Session = Depends(get_db)
) -> AnalysisHistoryListResponse:
    try:
        # Base queries
        query = select(AnalysisHistory)
        count_query = select(func.count(AnalysisHistory.id))

        if analysis_type:
            cleaned_type = analysis_type.strip().lower()
            if cleaned_type not in ["email", "url", "file"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid analysis_type filter. Must be 'email', 'url', or 'file'."
                )
            query = query.where(AnalysisHistory.analysis_type == cleaned_type)
            count_query = count_query.where(AnalysisHistory.analysis_type == cleaned_type)

        # Total count
        total = db.scalar(count_query) or 0

        # Paginated items ordered by newest first
        query = query.order_by(desc(AnalysisHistory.created_at)).offset(offset).limit(limit)
        records = db.scalars(query).all()

        items = [AnalysisHistorySummaryItem.model_validate(r) for r in records]

        return AnalysisHistoryListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=items
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying analysis history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query error: {str(e)}"
        )

@router.get(
    "/stats",
    response_model=AnalysisHistoryStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Aggregated History Statistics",
    description="Calculates summary counts for total analyses, threat levels, verdicts, and analysis types for dashboard analytics."
)
async def get_history_stats(db: Session = Depends(get_db)) -> AnalysisHistoryStatsResponse:
    try:
        total = db.scalar(select(func.count(AnalysisHistory.id))) or 0
        if total == 0:
            return AnalysisHistoryStatsResponse(
                total_analyses=0,
                spam_count=0,
                phishing_count=0,
                safe_count=0,
                threat_percentage=0.0,
                threat_distribution={
                    "CRITICAL": 0,
                    "HIGH": 0,
                    "MEDIUM": 0,
                    "LOW_SUSPICIOUS": 0,
                    "SAFE": 0
                },
                type_distribution={
                    "email": 0,
                    "url": 0,
                    "file": 0
                }
            )

        # Type breakdown
        type_res = db.execute(
            select(AnalysisHistory.analysis_type, func.count(AnalysisHistory.id))
            .group_by(AnalysisHistory.analysis_type)
        ).all()
        type_dist = {row[0]: row[1] for row in type_res}

        # Threat tier breakdown
        threat_res = db.execute(
            select(AnalysisHistory.threat_level, func.count(AnalysisHistory.id))
            .group_by(AnalysisHistory.threat_level)
        ).all()
        threat_dist = {row[0]: row[1] for row in threat_res}

        phishing_count = db.scalar(
            select(func.count(AnalysisHistory.id)).where(
                (AnalysisHistory.threat_level.in_(["CRITICAL", "HIGH"])) | 
                (AnalysisHistory.overall_verdict == "MALICIOUS") |
                (AnalysisHistory.overall_verdict.ilike("%Phishing%"))
            )
        ) or 0

        spam_count = db.scalar(
            select(func.count(AnalysisHistory.id)).where(
                (AnalysisHistory.email_prediction == "Spam") |
                (AnalysisHistory.overall_verdict.ilike("%Spam%"))
            )
        ) or 0

        safe_count = db.scalar(
            select(func.count(AnalysisHistory.id)).where(
                (AnalysisHistory.threat_level == "SAFE") |
                (AnalysisHistory.overall_verdict == "SAFE") |
                (AnalysisHistory.overall_verdict.ilike("%Clean%")) |
                (AnalysisHistory.overall_verdict.ilike("%Legitimate%"))
            )
        ) or 0

        threat_count = db.scalar(
            select(func.count(AnalysisHistory.id)).where(
                AnalysisHistory.threat_level != "SAFE"
            )
        ) or 0

        threat_pct = round((threat_count / total) * 100, 1) if total > 0 else 0.0

        return AnalysisHistoryStatsResponse(
            total_analyses=total,
            spam_count=spam_count,
            phishing_count=phishing_count,
            safe_count=safe_count,
            threat_percentage=threat_pct,
            threat_distribution={
                "CRITICAL": threat_dist.get("CRITICAL", 0),
                "HIGH": threat_dist.get("HIGH", 0),
                "MEDIUM": threat_dist.get("MEDIUM", 0),
                "LOW_SUSPICIOUS": threat_dist.get("LOW_SUSPICIOUS", 0),
                "SAFE": threat_dist.get("SAFE", 0)
            },
            type_distribution={
                "email": type_dist.get("email", 0),
                "url": type_dist.get("url", 0),
                "file": type_dist.get("file", 0)
            }
        )
    except Exception as e:
        logger.error(f"Error fetching history stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database aggregation error: {str(e)}"
        )

@router.get(
    "/{id}",
    response_model=AnalysisHistoryDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Analysis History Record",
    description="Retrieves a complete analysis record by ID, including complete ML results, lexical features, and URLs."
)
async def get_history_detail(
    id: int,
    db: Session = Depends(get_db)
) -> AnalysisHistoryDetailResponse:
    try:
        record = db.get(AnalysisHistory, id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis history record with ID {id} not found."
            )
        return AnalysisHistoryDetailResponse.model_validate(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history record {id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query error: {str(e)}"
        )

@router.delete(
    "/{id}",
    response_model=DeleteHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Analysis History Record",
    description="Deletes a specific threat analysis record from the PostgreSQL database."
)
async def delete_history_record(
    id: int,
    db: Session = Depends(get_db)
) -> DeleteHistoryResponse:
    try:
        record = db.get(AnalysisHistory, id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis history record with ID {id} not found."
            )
        db.delete(record)
        db.commit()
        logger.info(f"Deleted analysis history record with ID {id}")
        return DeleteHistoryResponse(
            message=f"Analysis history record {id} deleted successfully.",
            id=id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting history record {id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error deleting record: {str(e)}"
        )
