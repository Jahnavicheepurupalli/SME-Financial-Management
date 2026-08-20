import re
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from flask_bcrypt import Bcrypt
from backend.database.db import SessionLocal
from backend.models.models import User
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Password validation regex
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

def validate_password(password):
    return isinstance(password, str) and re.match(PASSWORD_REGEX, password) is not None


def normalize_email(email):
    return email.strip().lower() if isinstance(email, str) else ""


def valid_email(email):
    return len(email) <= 255 and re.fullmatch(EMAIL_REGEX, email) is not None

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    
    full_name = data.get('name') or data.get('full_name')
    email = normalize_email(data.get('email'))
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not isinstance(full_name, str) or not full_name.strip() or len(full_name.strip()) > 255:
        return jsonify({"message": "Name is required and must be 255 characters or fewer"}), 400

    full_name = full_name.strip()
    if not email or not valid_email(email):
        return jsonify({"message": "A valid email address is required"}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"message": "Name, email, and password are required"}), 400

    if confirm_password and password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400

    if not validate_password(password):
        return jsonify({
            "message": "Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character."
        }), 400

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return jsonify({"message": "Email already registered"}), 400

        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(full_name=full_name, email=email, password_hash=pw_hash)
        
        db.add(new_user)
        db.commit()
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name
            }
        }), 201
    except Exception:
        db.rollback()
        logger.exception("Unexpected error during signup.")
        return jsonify({"message": "An unexpected server error occurred. Please try again."}), 500
    finally:
        db.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = normalize_email(data.get('email'))
    password = data.get('password')

    if not email or not valid_email(email) or not isinstance(password, str) or not password:
        return jsonify({"message": "Email and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            return jsonify({"message": "Invalid email or password"}), 401

        if not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({"message": "Invalid email or password"}), 401

        # Emit JWT token
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }), 200
    except Exception:
        logger.exception("Unexpected error during login.")
        return jsonify({"message": "An unexpected server error occurred. Please try again."}), 500
    finally:
        db.close()

@auth_bp.route('/google', methods=['POST'])
def google_login():
    """Verify Google token received from the React frontend and create or login the user."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    from backend.config import Config

    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return jsonify({"message": "Google authentication is temporarily unavailable. Please contact the administrator."}), 401

    data = request.get_json() or {}
    token = data.get('credential')

    if not token:
        return jsonify({"message": "Google credential token is missing"}), 400

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
            return jsonify({"message": "Unable to verify your Google account. Please try again."}), 401
    except ValueError as ve:
        err_str = str(ve).lower()
        logger.warning("Google token verification rejected.", exc_info=True)
        if "client" in err_str or "audience" in err_str:
            return jsonify({"message": "Google authentication is temporarily unavailable. Please contact the administrator."}), 401
        elif "test" in err_str or "access_denied" in err_str or "unauthorized" in err_str or "consent" in err_str:
            return jsonify({"message": "This Google account is not authorized for the current OAuth testing configuration."}), 401
        else:
            return jsonify({"message": "Unable to verify your Google account. Please try again."}), 401
    except Exception as e:
        err_str = str(e).lower()
        logger.exception("Unexpected Google token verification error.")
        if "client" in err_str or "audience" in err_str:
            return jsonify({"message": "Google authentication is temporarily unavailable. Please contact the administrator."}), 401
        elif "test" in err_str or "access_denied" in err_str or "unauthorized" in err_str or "consent" in err_str:
            return jsonify({"message": "This Google account is not authorized for the current OAuth testing configuration."}), 401
        return jsonify({"message": "Unable to verify your Google account. Please try again."}), 401

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Create user on the fly
            user = User(full_name=full_name, email=email, password_hash=None)
            db.add(user)
            db.commit()
            db.refresh(user)

        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message": "Google authentication successful",
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }), 200
    except Exception:
        db.rollback()
        logger.exception("Unexpected error during Google login.")
        return jsonify({"message": "An unexpected server error occurred. Please try again."}), 500
    finally:
        db.close()

@auth_bp.route('/forgot-password', methods=['POST'])
@auth_bp.route('/reset-password', methods=['POST'])
def forgot_password():
    """Self-service password reset is unavailable without email verification."""
    return jsonify({
        "message": "Self-service password reset is unavailable. Please contact the administrator."
    }), 503


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json() or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all(isinstance(value, str) and value for value in (
        current_password, new_password, confirm_password
    )):
        return jsonify({"message": "Current and new passwords are required"}), 400

    if new_password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400

    if not validate_password(new_password):
        return jsonify({"message": "Password must meet complexity rules."}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(get_jwt_identity())).first()
        if not user:
            return jsonify({"message": "Account not found"}), 404
        if not user.password_hash:
            return jsonify({
                "message": "Password changes are unavailable for Google-only accounts."
            }), 400
        if not bcrypt.check_password_hash(user.password_hash, current_password):
            return jsonify({"message": "Current password is incorrect"}), 401

        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.commit()
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while changing password.")
        return jsonify({"message": "An unexpected server error occurred. Please try again."}), 500
    finally:
        db.close()

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return jsonify({"message": "User not found"}), 404
        return jsonify({
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }), 200
    except Exception:
        logger.exception("Unexpected error while loading the user profile.")
        return jsonify({"message": "An unexpected server error occurred. Please try again."}), 500
    finally:
        db.close()

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(resp)
    return resp, 200
