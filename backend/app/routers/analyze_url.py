"""
backend/app/routers/analyze_url.py
Endpoint for standalone URL phishing analysis with automatic PostgreSQL audit persistence.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_ml_service
from backend.app.services.ml_service import MLService
from backend.app.db.session import get_db
from backend.app.db.models.history import AnalysisHistory
from backend.app.schemas.url import URLAnalyzeRequest, URLAnalyzeResponse
from backend.app.utils.logger import logger

router = APIRouter(prefix="/analyze", tags=["Security Analysis"])

@router.post(
    "/url",
    response_model=URLAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Standalone URL for Phishing Threats",
    description=(
        "Extracts 18 lexical properties from a URL and executes dual-level "
        "Random Forest evaluation (full URL + canonical domain root) to classify "
        "as Legitimate or Phishing, and records the result to PostgreSQL."
    )
)
async def analyze_url_endpoint(
    payload: URLAnalyzeRequest,
    ml_service: MLService = Depends(get_ml_service),
    db: Session = Depends(get_db)
) -> URLAnalyzeResponse:
    url = payload.url.strip()
    logger.info(f"Analyzing standalone URL: {url}")
    
    # 1. Execute ML pipeline
    try:
        url_eval = ml_service.analyze_url(url=url)
    except Exception as e:
        logger.error(f"Error during URL ML inference: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during ML URL analysis: {str(e)}"
        )
    
    is_phish = url_eval["is_phishing"]
    phish_prob = url_eval["phishing_probability"]
    
    verdict = url_eval.get("verdict", "Phishing URL Detected" if is_phish else "Legitimate URL")
    action = url_eval.get("recommended_action", "BLOCK" if is_phish else "ALLOW")
    risk_score = url_eval.get("risk_score", round(phish_prob * 100, 1))
    threat_tier = "CRITICAL" if is_phish else ("LOW_SUSPICIOUS" if risk_score > 35 else "SAFE")

    # 2. Persist to PostgreSQL AnalysisHistory
    history_record = AnalysisHistory(
        analysis_type="url",
        subject=None,
        submitted_url=url,
        email_prediction=None,
        spam_probability=None,
        url_count=1,
        extracted_urls=[url],
        overall_verdict=verdict,
        threat_level=threat_tier,
        risk_score=risk_score,
        recommended_action=action,
        complete_analysis_result=url_eval
    )

    try:
        db.add(history_record)
        db.commit()
        db.refresh(history_record)
        record_id = history_record.id
        logger.info(f"URL analysis persisted successfully to PostgreSQL with ID: {record_id}")
    except Exception as db_err:
        db.rollback()
        logger.error(f"Database persistence failure for URL analysis: {str(db_err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis completed but failed to persist to database: {str(db_err)}"
        )

    return URLAnalyzeResponse(
        id=record_id,
        url=url_eval["url"],
        classification=url_eval["label"],
        is_phishing=is_phish,
        phishing_probability=phish_prob,
        legitimate_probability=url_eval["legitimate_probability"],
        confidence_percent=url_eval["confidence_percent"],
        verdict=verdict,
        risk_score=risk_score,
        recommended_action=action,
        features=url_eval.get("features", {})
    )
