"""
backend/app/routers/__init__.py
"""
from backend.app.routers.health import router as health_router
from backend.app.routers.analyze_email import router as email_router
from backend.app.routers.analyze_url import router as url_router
from backend.app.routers.analyze_file import router as file_router
from backend.app.routers.history import router as history_router

__all__ = [
    "health_router",
    "email_router",
    "url_router",
    "file_router",
    "history_router",
]
