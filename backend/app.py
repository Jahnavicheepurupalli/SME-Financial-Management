import os
import sys
import logging

# Ensure the project root is on sys.path so that `from backend.xxx import ...`
# works whether this file is run directly (python backend/app.py) or as a module
# (python -m backend.app / via run.py).
import site
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

_user_site = site.getusersitepackages()
if _user_site and _user_site not in sys.path:
    sys.path.append(_user_site)

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from backend.config import Config
from backend.database.db import engine, Base
from backend.routes.auth import auth_bp
from backend.routes.document import doc_bp
from backend.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

# Initialize database schemas
try:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")
except Exception:
    logger.exception("Could not create database tables during startup; aborting.")
    raise

# Validate Google OAuth credentials on startup
Config.validate_oauth_config()

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = Config.SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600 * 24  # 24 hours expiry

# Configure CORS to allow frontend requests
CORS(
    app, 
    resources={r"/*": {"origins": "*"}}, 
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# Initialize JWT Manager
jwt = JWTManager(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(doc_bp, url_prefix='/api')
# Home & Health check routes
@app.route("/")
def home():
    return {
        "status": "success",
        "message": "Financial Document Intelligence API is running"
    }

@app.route("/api/health")
def health():
    return {
        "status": "healthy",
        "backend": "running"
    }

if __name__ == '__main__':
    # Start flask application
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
