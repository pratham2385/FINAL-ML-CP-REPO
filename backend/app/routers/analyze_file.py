"""
backend/app/routers/analyze_file.py
Endpoint for uploading and analyzing .eml RFC 822 email files with automatic PostgreSQL audit persistence.
"""

from typing import List
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.dependencies import get_ml_service
from backend.app.services.ml_service import MLService
from backend.app.services.eml_parser import parse_eml_bytes
from backend.app.db.session import get_db
from backend.app.db.models.history import AnalysisHistory
from backend.app.schemas.file import (
    FileAnalyzeResponse,
    EMLMetadata,
    BatchFileItemResult,
    BatchFileAnalyzeSummary,
    BatchFileAnalyzeResponse,
)
from backend.app.schemas.common import EmailAnalysisResult, URLDetail, URLSummary, PhishingIntentResult
from backend.app.utils.logger import logger

router = APIRouter(prefix="/analyze", tags=["Security Analysis"])

MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_BYTES

@router.post(
    "/file",
    response_model=FileAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and Analyze .eml Email File",
    description=(
        "Uploads a standard RFC 822 / MIME format .eml file. Automatically parses "
        "headers (From, To, Date, Subject, Message-ID), extracts plain text and "
        "HTML body content, preserves embedded links, performs dual-representation "
        "threat analysis, and records the audit result to PostgreSQL."
    )
)
async def analyze_file_endpoint(
    file: UploadFile = File(..., description="The .eml email file to inspect"),
    ml_service: MLService = Depends(get_ml_service),
    db: Session = Depends(get_db)
) -> FileAnalyzeResponse:
    # 1. Filename validation
    filename = file.filename or ""
    if not filename.lower().endswith(".eml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: '{filename}'. Only .eml files are accepted."
        )

    # 2. Read bytes
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    # 3. Size validation
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes)."
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # 4. Parse .eml
    try:
        parsed_email = parse_eml_bytes(content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid .eml file format: {str(e)}"
        )

    # 5. Check readable content
    if not parsed_email.subject and not parsed_email.body_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The .eml file does not contain readable subject or body content."
        )

    # 6. Execute ML pipeline
    try:
        logger.info(f"Analyzing .eml file '{filename}' ({file_size} bytes, Subject: '{parsed_email.subject[:40]}...')")
        result = ml_service.analyze_email(
            subject=parsed_email.subject,
            message=parsed_email.body_text,
            sender=parsed_email.sender
        )
    except Exception as e:
        logger.error(f"Error during .eml ML inference: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing the email file: {str(e)}"
        )

    email_data = result["email_analysis"]
    url_summary_data = result["url_summary"]
    url_details_data = result["url_details"]
    extracted_urls = [u["url"] for u in url_details_data]
    intent_data = result.get("phishing_intent_analysis")

    eml_meta = EMLMetadata(
        filename=filename,
        file_size_bytes=file_size,
        sender=parsed_email.sender or None,
        recipient=parsed_email.recipient or None,
        date=parsed_email.date or None,
        subject=parsed_email.subject or None,
        message_id=parsed_email.message_id or None
    )

    # 7. Persist to PostgreSQL AnalysisHistory
    history_record = AnalysisHistory(
        analysis_type="file",
        subject=parsed_email.subject or None,
        submitted_url=None,
        email_prediction=email_data["label"],
        spam_probability=email_data["spam_probability"],
        url_count=url_summary_data["total_urls_found"],
        extracted_urls=extracted_urls,
        overall_verdict=result["verdict"],
        threat_level=result["threat_level"],
        risk_score=result["overall_risk_score"],
        recommended_action=result["recommended_action"],
        complete_analysis_result={
            **result,
            "eml_metadata": eml_meta.model_dump()
        }
    )

    try:
        db.add(history_record)
        db.commit()
        db.refresh(history_record)
        record_id = history_record.id
        logger.info(f"File analysis persisted successfully to PostgreSQL with ID: {record_id}")
    except Exception as db_err:
        db.rollback()
        logger.error(f"Database persistence failure for file analysis: {str(db_err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis completed but failed to persist to database: {str(db_err)}"
        )

    return FileAnalyzeResponse(
        id=record_id,
        eml_metadata=eml_meta,
        verdict=result["verdict"],
        overall_security_verdict=result.get("overall_security_verdict", result["verdict"]),
        threat_level=result["threat_level"],
        overall_risk_score=result["overall_risk_score"],
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


@router.post(
    "/files",
    response_model=BatchFileAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Upload and Analyze Multiple .eml Email Files",
    description=(
        "Uploads and inspects multiple RFC 822 .eml files in a single batch request. "
        "Enforces controlled concurrency (up to 5 concurrent analyses), streams file reads, "
        "validates each file independently, records successful audits to PostgreSQL, and aggregates "
        "summary metrics across the batch."
    )
)
async def analyze_files_batch_endpoint(
    files: List[UploadFile] = File(..., description="List of .eml email files to inspect"),
    ml_service: MLService = Depends(get_ml_service),
    db: Session = Depends(get_db)
) -> BatchFileAnalyzeResponse:
    start_time = time.perf_counter()

    # 1. Batch-level validation: file count
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for batch analysis."
        )

    if len(files) > settings.MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size ({len(files)} files) exceeds maximum allowed limit of {settings.MAX_FILES_PER_BATCH} files."
        )

    # 2. Concurrency primitives
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_EMAIL_ANALYSIS)
    db_lock = asyncio.Lock()
    cumulative_size = 0
    size_lock = asyncio.Lock()

    async def process_single_file(upload_file: UploadFile) -> BatchFileItemResult:
        nonlocal cumulative_size
        filename = upload_file.filename or "unknown.eml"

        # Check extension
        if not filename.lower().endswith(".eml"):
            return BatchFileItemResult(
                filename=filename,
                status="failed",
                file_size_bytes=0,
                error_message=f"Unsupported file format: '{filename}'. Only .eml files are accepted."
            )

        # Stream read file content
        content = bytearray()
        try:
            while True:
                chunk = await upload_file.read(64 * 1024)
                if not chunk:
                    break
                content.extend(chunk)
                if len(content) > settings.MAX_FILE_SIZE_BYTES:
                    return BatchFileItemResult(
                        filename=filename,
                        status="failed",
                        file_size_bytes=len(content),
                        error_message=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                    )
        except Exception as read_err:
            return BatchFileItemResult(
                filename=filename,
                status="failed",
                file_size_bytes=len(content),
                error_message=f"Failed to read file content: {str(read_err)}"
            )

        file_size = len(content)

        # Check empty or whitespace-only file
        if file_size == 0 or len(content.strip()) == 0:
            return BatchFileItemResult(
                filename=filename,
                status="failed",
                file_size_bytes=file_size,
                error_message="The uploaded file is empty (0 bytes)."
            )

        # Check cumulative batch size
        async with size_lock:
            cumulative_size += file_size
            if cumulative_size > settings.MAX_BATCH_SIZE_BYTES:
                return BatchFileItemResult(
                    filename=filename,
                    status="failed",
                    file_size_bytes=file_size,
                    error_message=f"Total batch size exceeded maximum limit of {settings.MAX_BATCH_SIZE_BYTES // (1024 * 1024)}MB."
                )

        # Parse .eml MIME structure
        try:
            parsed_email = parse_eml_bytes(bytes(content))
        except Exception as parse_err:
            return BatchFileItemResult(
                filename=filename,
                status="failed",
                file_size_bytes=file_size,
                error_message=f"Invalid .eml file format: {str(parse_err)}"
            )

        # Check readable subject or body
        if not parsed_email.subject and not parsed_email.body_text:
            return BatchFileItemResult(
                filename=filename,
                status="failed",
                file_size_bytes=file_size,
                error_message="The .eml file does not contain readable subject or body content."
            )

        # Perform ML inference under bounded semaphore concurrency
        async with semaphore:
            try:
                result = await asyncio.to_thread(
                    ml_service.analyze_email,
                    subject=parsed_email.subject,
                    message=parsed_email.body_text,
                    sender=parsed_email.sender
                )
            except Exception as ml_err:
                logger.error(f"Error during batch ML inference for '{filename}': {str(ml_err)}", exc_info=True)
                return BatchFileItemResult(
                    filename=filename,
                    status="failed",
                    file_size_bytes=file_size,
                    error_message=f"Analysis inference error: {str(ml_err)}"
                )

        email_data = result["email_analysis"]
        url_summary_data = result["url_summary"]
        url_details_data = result["url_details"]
        extracted_urls = [u["url"] for u in url_details_data]
        intent_data = result.get("phishing_intent_analysis")

        eml_meta = EMLMetadata(
            filename=filename,
            file_size_bytes=file_size,
            sender=parsed_email.sender or None,
            recipient=parsed_email.recipient or None,
            date=parsed_email.date or None,
            subject=parsed_email.subject or None,
            message_id=parsed_email.message_id or None
        )

        # Persist to PostgreSQL under db lock for thread/session safety
        record_id = None
        try:
            async with db_lock:
                history_record = AnalysisHistory(
                    analysis_type="file",
                    subject=parsed_email.subject or None,
                    submitted_url=None,
                    email_prediction=email_data["label"],
                    spam_probability=email_data["spam_probability"],
                    url_count=url_summary_data["total_urls_found"],
                    extracted_urls=extracted_urls,
                    overall_verdict=result["verdict"],
                    threat_level=result["threat_level"],
                    risk_score=result["overall_risk_score"],
                    recommended_action=result["recommended_action"],
                    complete_analysis_result={
                        **result,
                        "eml_metadata": eml_meta.model_dump()
                    }
                )
                db.add(history_record)
                db.commit()
                db.refresh(history_record)
                record_id = history_record.id
                logger.info(f"Batch item '{filename}' persisted with history ID {record_id}")
        except Exception as db_err:
            logger.error(f"Database persistence failure for batch item '{filename}': {str(db_err)}", exc_info=True)
            try:
                db.rollback()
            except Exception:
                pass

        return BatchFileItemResult(
            filename=filename,
            status="completed",
            file_size_bytes=file_size,
            id=record_id,
            eml_metadata=eml_meta,
            verdict=result["verdict"],
            overall_security_verdict=result.get("overall_security_verdict", result["verdict"]),
            threat_level=result["threat_level"],
            overall_risk_score=result["overall_risk_score"],
            recommended_action=result["recommended_action"],
            verdict_explanation=result.get("verdict_explanation"),
            evidence_summary=result.get("evidence_summary", []),
            email_classification=email_data["label"],
            spam_probability=email_data["spam_probability"],
            ham_probability=email_data["ham_probability"],
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

    # Execute all file tasks concurrently
    results = await asyncio.gather(*[process_single_file(f) for f in files])

    # Check if entire batch was rejected for total size exceeding limit
    if cumulative_size > settings.MAX_BATCH_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Batch exceeds maximum allowed size of {settings.MAX_BATCH_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Aggregate summary metrics
    total_files = len(results)
    successful_count = sum(1 for r in results if r.status == "completed")
    failed_count = sum(1 for r in results if r.status == "failed")
    ham_count = sum(1 for r in results if r.status == "completed" and r.email_classification == "Ham")
    spam_count = sum(1 for r in results if r.status == "completed" and r.email_classification == "Spam")
    total_size_bytes = sum(r.file_size_bytes for r in results)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return BatchFileAnalyzeResponse(
        summary=BatchFileAnalyzeSummary(
            total_files=total_files,
            successful_count=successful_count,
            failed_count=failed_count,
            ham_count=ham_count,
            spam_count=spam_count,
            total_size_bytes=total_size_bytes,
            total_processing_time_ms=elapsed_ms
        ),
        results=results
    )
