"""
backend/run.py
Entry point script to start the FastAPI server with Uvicorn.
"""

import os
import sys
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import settings

def main():
    print("=" * 60)
    print(f" Starting {settings.PROJECT_NAME}")
    print(f" Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    print(f" Swagger UI: http://{settings.HOST}:{settings.PORT}/docs")
    print(f" Health Check: http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}/health")
    print("=" * 60)

    reload_dirs = [
        os.path.join(PROJECT_ROOT, "backend"),
        os.path.join(PROJECT_ROOT, "src"),
    ]

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        reload_dirs=reload_dirs,
        log_level="info"
    )

if __name__ == "__main__":
    main()
