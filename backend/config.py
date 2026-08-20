import os
import logging
from dotenv import load_dotenv
from backend.logging_config import configure_logging

# Load environment variables
load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)

class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sme-fintech-jwt-secret-key-1029384756")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
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
