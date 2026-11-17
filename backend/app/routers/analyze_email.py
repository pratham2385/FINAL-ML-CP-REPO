"""
backend/app/routers/analyze_email.py
Endpoint for analyzing email content and embedded hyperlinks, with automatic PostgreSQL audit persistence.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_ml_service
from backend.app.services.ml_service import MLService
from backend.app.db.session import get_db
from backend.app.db.models.history import AnalysisHistory
from backend.app.schemas.email import EmailAnalyzeRequest, EmailAnalyzeResponse
from backend.app.schemas.common import EmailAnalysisResult, URLDetail, URLSummary, PhishingIntentResult
from backend.app.utils.logger import logger

router = APIRouter(prefix="/analyze", tags=["Security Analysis"])

@router.post(
    "/email",
    response_model=EmailAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Email for Spam and Phishing Threats",
    description=(
        "Executes the Dual-Representation Pipeline on email subject and body: "
        "evaluates NLP spam features, extracts embedded hyperlinks, performs lexical "
        "phishing analysis on all links, computes a composite threat score, and records "
        "the audit result to PostgreSQL."
    )
)
async def analyze_email_endpoint(
    payload: EmailAnalyzeRequest,
    ml_service: MLService = Depends(get_ml_service),
    db: Session = Depends(get_db)
) -> EmailAnalyzeResponse:
    subject = payload.subject or ""
    message = payload.message or ""
    
    logger.info(f"Analyzing email (Subject: '{subject[:40]}...', Message length: {len(message)} chars)")
    
    # 1. Execute ML pipeline with intent analysis
    try:
        result = ml_service.analyze_email(
            subject=subject,
            message=message,
            sender=payload.sender
        )
    except Exception as e:
        logger.error(f"Error during email ML inference: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during ML email analysis: {str(e)}"
        )

    email_data = result["email_analysis"]
    url_summary_data = result["url_summary"]
    url_details_data = result["url_details"]
    extracted_urls = [u["url"] for u in url_details_data]
    intent_data = result.get("phishing_intent_analysis")

    # 2. Persist to PostgreSQL AnalysisHistory
    history_record = AnalysisHistory(
        analysis_type="email",
        subject=subject or None,
        submitted_url=None,
        email_prediction=email_data["label"],
        spam_probability=email_data["spam_probability"],
        url_count=url_summary_data["total_urls_found"],
        extracted_urls=extracted_urls,
        overall_verdict=result["verdict"],
        threat_level=result["threat_level"],
        risk_score=result["overall_risk_score"],
        recommended_action=result["recommended_action"],
        complete_analysis_result=result
    )

    try:
        db.add(history_record)
        db.commit()
        db.refresh(history_record)
        record_id = history_record.id
        logger.info(f"Email analysis persisted successfully to PostgreSQL with ID: {record_id}")
    except Exception as db_err:
        db.rollback()
        logger.error(f"Database persistence failure for email analysis: {str(db_err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis completed but failed to persist to database: {str(db_err)}"
        )

    return EmailAnalyzeResponse(
        id=record_id,
        verdict=result["verdict"],
        overall_security_verdict=result.get("overall_security_verdict", result["verdict"]),
        threat_level=result["threat_level"],
        risk_score=result["overall_risk_score"],
        recommended_action=result["recommended_action"],
        verdict_explanation=result.get("verdict_explanation"),
        evidence_summary=result.get("evidence_summary", []),
        email_classification=email_data["label"],
        spam_probability=email_data["spam_probability"],
        confidence_percent=email_data["confidence_percent"],
        extracted_urls=extracted_urls,
        phishing_intent_analysis=PhishingIntentResult(**intent_data) if intent_data else None,
        email_analysis=EmailAnalysisResult(
            label=email_data["label"],
            is_spam=email_data["is_spam"],
            spam_probability=email_data["spam_probability"],
            ham_probability=email_data["ham_probability"],
            confidence_percent=email_data["confidence_percent"],
            cleaned_text_preview=email_data["cleaned_text_preview"]
        ),
        url_summary=URLSummary(
            total_urls_found=url_summary_data["total_urls_found"],
            phishing_urls_count=url_summary_data["phishing_urls_count"],
            phishing_urls=url_summary_data["phishing_urls"],
            max_phishing_probability=url_summary_data["max_phishing_probability"]
        ),
        url_details=[
            URLDetail(
                url=ud["url"],
                label=ud["label"],
                is_phishing=ud["is_phishing"],
                phishing_probability=ud["phishing_probability"],
                legitimate_probability=ud["legitimate_probability"],
                confidence_percent=ud["confidence_percent"],
                features=ud.get("features")
            )
            for ud in url_details_data
        ]
    )
