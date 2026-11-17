"""
backend/app/services/ml_service.py
Thread-safe singleton service managing the ML pipeline artifacts in memory.
Eliminates overhead by preventing redundant disk I/O and deserialization across requests.
"""

import os
import threading
from typing import Dict, Any, Optional

from src.pipeline import SecurityAnalysisPipeline
from backend.app.config import settings
from backend.app.utils.logger import logger

class MLService:
    """Singleton service encapsulating SecurityAnalysisPipeline."""
    _instance: Optional["MLService"] = None
    _lock = threading.Lock()

    def __init__(self, models_dir: Optional[str] = None):
        target_dir = models_dir or settings.MODELS_DIR
        logger.info(f"Loading ML models into memory from: {target_dir}")
        
        if not os.path.isdir(target_dir):
            raise FileNotFoundError(f"Models directory not found at {target_dir}")
            
        self.pipeline = SecurityAnalysisPipeline(models_dir=target_dir)
        self.models_dir = target_dir
        logger.info("ML SecurityAnalysisPipeline loaded successfully and cached in memory.")

    @classmethod
    def get_instance(cls, models_dir: Optional[str] = None) -> "MLService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(models_dir=models_dir)
        return cls._instance

    def analyze_email(self, subject: str = "", message: str = "", sender: Optional[str] = None) -> Dict[str, Any]:
        """Runs the Multi-Representation Pipeline on email content."""
        return self.pipeline.analyze_email(subject=subject, message=message, sender=sender)

    def analyze_url(self, url: str) -> Dict[str, Any]:
        """Runs lexical phishing feature extraction and classification on a single URL."""
        return self.pipeline.analyze_url(url=url)

    def get_health_status(self) -> Dict[str, Any]:
        """Returns internal status of loaded ML models."""
        email_model_ok = hasattr(self.pipeline.email_predictor, "model") and self.pipeline.email_predictor.model is not None
        tfidf_ok = hasattr(self.pipeline.email_predictor, "tfidf") and self.pipeline.email_predictor.tfidf is not None
        url_model_ok = hasattr(self.pipeline.url_predictor, "model") and self.pipeline.url_predictor.model is not None
        
        return {
            "status": "operational" if (email_model_ok and tfidf_ok and url_model_ok) else "degraded",
            "models_dir": self.models_dir,
            "email_model_loaded": email_model_ok,
            "email_tfidf_loaded": tfidf_ok,
            "url_model_loaded": url_model_ok,
            "url_features_monitored": len(self.pipeline.url_predictor.feature_names),
        }
