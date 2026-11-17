"""
backend/app/dependencies.py
Dependency injection providers for FastAPI routers.
"""

from fastapi import Depends
from backend.app.services.ml_service import MLService
from src.pipeline import SecurityAnalysisPipeline

def get_ml_service() -> MLService:
    """Provides the singleton MLService instance."""
    return MLService.get_instance()

def get_pipeline(service: MLService = Depends(get_ml_service)) -> SecurityAnalysisPipeline:
    """Provides direct access to the loaded SecurityAnalysisPipeline."""
    return service.pipeline
