import os
import logging
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    APP_ENV = os.getenv("FLASK_ENV", os.getenv("APP_ENV", "development")).strip().lower()
    DEBUG = _env_flag("FLASK_DEBUG", False)
    _configured_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not _configured_secret:
        if APP_ENV == "production":
            raise RuntimeError(
                "JWT_SECRET_KEY (or SECRET_KEY) must be set in production."
            )
        _configured_secret = secrets.token_urlsafe(32)
        logger.warning(
            "JWT secret is not configured; using an ephemeral development secret. "
            "Tokens will not survive restarts."
        )
    SECRET_KEY = _configured_secret
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # MySQL Config
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "sme_financials")
    
    # MongoDB Config
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/sme_financials")
    
    # Google OAuth Config
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Directories
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

    @classmethod
    def validate_oauth_config(cls):
        """Validates Google OAuth configuration at startup without crashing the application."""
        if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
            logger.warning("Google OAuth credentials are missing or incomplete. Google login will be disabled.")
            return False
        if "apps.googleusercontent.com" not in cls.GOOGLE_CLIENT_ID:
            logger.warning("GOOGLE_CLIENT_ID format appears malformed. Google login might fail.")
            return False
        logger.info("Google OAuth configuration validated successfully.")
        return True

# Ensure required directories exist
for folder in [Config.UPLOAD_FOLDER, Config.STATIC_FOLDER, Config.REPORTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)
