"""
backend/app/main.py
Main application entry point for the FastAPI backend with PostgreSQL persistence.
Configures CORS, lifespan model and database pre-warming, structured exception handlers,
and registers all API routers under /api.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.services.ml_service import MLService
from backend.app.db.session import init_db, check_db_connection
from backend.app.routers.health import router as health_router
from backend.app.routers.analyze_email import router as email_router
from backend.app.routers.analyze_url import router as url_router
from backend.app.routers.analyze_file import router as file_router
from backend.app.routers.history import router as history_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Pre-warms ML model artifacts and initializes PostgreSQL database tables.
    """
    logger.info("Initializing Email & Phishing Detection API...")
    
    # 1. Pre-load ML models
    try:
        ml_service = MLService.get_instance()
        ml_health = ml_service.get_health_status()
        logger.info(f"ML Pipeline pre-warmed successfully. Status: {ml_health.get('status')}")
    except Exception as e:
        logger.error(f"Failed to pre-warm ML models during startup: {str(e)}", exc_info=True)

    # 2. Initialize PostgreSQL tables
    try:
        init_db()
        db_health = check_db_connection()
        logger.info(f"PostgreSQL connection verified. Status: {db_health.get('status')}, Database: {db_health.get('database_name')}")
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed during startup: {str(e)}", exc_info=True)

    yield
    logger.info("Shutting down Email & Phishing Detection API...")

def create_app() -> FastAPI:
    """Application factory configuring routes, middleware, and documentation."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # 2. Request Timing & Logging Middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} "
            f"-> Status {response.status_code} ({process_time_ms}ms)"
        )
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)
        return response

    # 3. Custom Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "details": jsonable_encoder(exc.errors())
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
                "details": jsonable_encoder(exc.detail)
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(exc)
            }
        )

    # 4. Include Routers
    app.include_router(health_router, prefix=settings.API_PREFIX)
    app.include_router(email_router, prefix=settings.API_PREFIX)
    app.include_router(url_router, prefix=settings.API_PREFIX)
    app.include_router(file_router, prefix=settings.API_PREFIX)
    app.include_router(history_router, prefix=settings.API_PREFIX)

    # 5. Root Welcome Endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs",
            "health": f"{settings.API_PREFIX}/health",
            "endpoints": {
                "health": f"GET {settings.API_PREFIX}/health",
                "analyze_email": f"POST {settings.API_PREFIX}/analyze/email",
                "analyze_url": f"POST {settings.API_PREFIX}/analyze/url",
                "analyze_file": f"POST {settings.API_PREFIX}/analyze/file (.eml upload)",
                "list_history": f"GET {settings.API_PREFIX}/history",
                "get_history": f"GET {settings.API_PREFIX}/history/{{id}}",
                "delete_history": f"DELETE {settings.API_PREFIX}/history/{{id}}"
            }
        }

    return app

app = create_app()
