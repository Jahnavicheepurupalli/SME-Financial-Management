import re
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from flask_bcrypt import Bcrypt
from backend.database.db import SessionLocal, session_scope
from backend.models.models import User
from backend.utils.responses import error_response, internal_error, success_response
from backend.utils.serializers import serialize_user
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Password validation regex
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

GOOGLE_UNAVAILABLE_MESSAGE = "Google authentication is temporarily unavailable. Please contact the administrator."
GOOGLE_UNAUTHORIZED_MESSAGE = "This Google account is not authorized for the current OAuth testing configuration."
GOOGLE_VERIFY_FAILED_MESSAGE = "Unable to verify your Google account. Please try again."

def validate_password(password):
    return re.match(PASSWORD_REGEX, password) is not None

def get_user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()

def auth_session_response(user, message):
    return jsonify({
        "message": message,
        "token": create_access_token(identity=str(user.id)),
        "user": serialize_user(user)
    }), 200

def google_error_message(exc):
    """Maps a Google verification failure onto the user-facing message."""
    err_str = str(exc).lower()
    if "client" in err_str or "audience" in err_str:
        return GOOGLE_UNAVAILABLE_MESSAGE
    if any(token in err_str for token in ("test", "access_denied", "unauthorized", "consent")):
        return GOOGLE_UNAUTHORIZED_MESSAGE
    return GOOGLE_VERIFY_FAILED_MESSAGE

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    
    full_name = data.get('name') or data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([full_name, email, password]):
        return error_response("Name, email, and password are required")

    if confirm_password and password != confirm_password:
        return error_response("Passwords do not match")

    if not validate_password(password):
        return error_response(
            "Password must be at least 8 characters long, contain an uppercase letter, "
            "a lowercase letter, a number, and a special character."
        )

    try:
        with session_scope(SessionLocal) as db:
            if get_user_by_email(db, email):
                return error_response("Email already registered")

            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(full_name=full_name, email=email, password_hash=pw_hash)

            db.add(new_user)
            db.commit()
            return success_response(
                "Registration successful",
                status_code=201,
                user=serialize_user(new_user)
            )
    except Exception:
        logger.exception("Unexpected error during signup.")
        return internal_error()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return error_response("Email and password are required")

    try:
        with session_scope(SessionLocal) as db:
            user = get_user_by_email(db, email)
            if not user or not user.password_hash:
                return error_response("Invalid email or password", 401)

            if not bcrypt.check_password_hash(user.password_hash, password):
                return error_response("Invalid email or password", 401)

            return auth_session_response(user, "Login successful")
    except Exception:
        logger.exception("Unexpected error during login.")
        return internal_error()

@auth_bp.route('/google', methods=['POST'])
def google_login():
    """Verify Google token received from the React frontend and create or login the user."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    from backend.config import Config

    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return error_response(GOOGLE_UNAVAILABLE_MESSAGE, 401)

    data = request.get_json() or {}
    token = data.get('credential')

    if not token:
        return error_response("Google credential token is missing")

    try:
        # Verify the Google Token JWT payload sent by client using Config.GOOGLE_CLIENT_ID
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            Config.GOOGLE_CLIENT_ID
        )
        email = idinfo.get('email', '').strip().lower()
        full_name = idinfo.get('name', 'Google User')

        if not email:
            return error_response(GOOGLE_VERIFY_FAILED_MESSAGE, 401)
    except ValueError as ve:
        logger.warning("Google token verification rejected.", exc_info=True)
        return error_response(google_error_message(ve), 401)
    except Exception as e:
        logger.exception("Unexpected Google token verification error.")
        return error_response(google_error_message(e), 401)

    try:
        with session_scope(SessionLocal) as db:
            user = get_user_by_email(db, email)
            if not user:
                # Create user on the fly
                user = User(full_name=full_name, email=email, password_hash=None)
                db.add(user)
                db.commit()
                db.refresh(user)

            return auth_session_response(user, "Google authentication successful")
    except Exception:
        logger.exception("Unexpected error during Google login.")
        return internal_error()

@auth_bp.route('/forgot-password', methods=['POST'])
@auth_bp.route('/reset-password', methods=['POST'])
def forgot_password():
    """No OTP/verification flow. Verifies email, then updates password directly."""
    data = request.get_json() or {}
    email = data.get('email')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([email, new_password, confirm_password]):
        return error_response("Email and new passwords are required")

    if new_password != confirm_password:
        return error_response("Passwords do not match")

    if not validate_password(new_password):
        return error_response("Password must meet complexity rules.")

    try:
        with session_scope(SessionLocal) as db:
            user = get_user_by_email(db, email)
            if not user:
                return error_response("User not found with this email", 404)

            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.commit()
            return jsonify({"message": "Password has been reset successfully"}), 200
    except Exception:
        logger.exception("Unexpected error while resetting password.")
        return internal_error()

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    try:
        with session_scope(SessionLocal) as db:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                return error_response("User not found", 404)
            return jsonify({"user": serialize_user(user)}), 200
    except Exception:
        logger.exception("Unexpected error while loading the user profile.")
        return internal_error()

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(resp)
    return resp, 200
