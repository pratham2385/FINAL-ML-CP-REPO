"""
backend/app/schemas/health.py
Pydantic schemas for the health check endpoint.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """Health check status response."""
    status: str = Field(..., description="Overall system health status", json_schema_extra={"example": "healthy"})
    version: str = Field(..., description="API version", json_schema_extra={"example": "1.0.0"})
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    ml_pipeline: Dict[str, Any] = Field(..., description="Status of ML models and artifacts")
    database: Dict[str, Any] = Field(..., description="Status of PostgreSQL database connection")
