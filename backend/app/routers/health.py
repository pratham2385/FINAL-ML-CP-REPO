"""
backend/app/routers/health.py
Health check and system telemetry endpoint with PostgreSQL database connectivity verification.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from backend.app.config import settings
from backend.app.dependencies import get_ml_service
from backend.app.services.ml_service import MLService
from backend.app.schemas.health import HealthResponse
from backend.app.db.session import check_db_connection

router = APIRouter(tags=["System Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System, ML Pipeline, and Database Health",
    description="Returns backend runtime status, in-memory ML model readiness, and PostgreSQL connectivity."
)
async def get_health(ml_service: MLService = Depends(get_ml_service)) -> HealthResponse:
    """Verifies backend responsiveness, ML model readiness, and PostgreSQL connection."""
    ml_health = ml_service.get_health_status()
    db_health = check_db_connection()
    
    is_ml_ok = ml_health.get("status") == "operational"
    is_db_ok = db_health.get("status") == "connected"
    
    overall_status = "healthy" if (is_ml_ok and is_db_ok) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        ml_pipeline=ml_health,
        database=db_health
    )
