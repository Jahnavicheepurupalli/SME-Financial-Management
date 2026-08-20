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

def validate_password(password):
    return re.match(PASSWORD_REGEX, password) is not None

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    
    full_name = data.get('name') or data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([full_name, email, password]):
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
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
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
    """No OTP/verification flow. Verifies email, then updates password directly."""
    data = request.get_json() or {}
    email = data.get('email')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([email, new_password, confirm_password]):
        return jsonify({"message": "Email and new passwords are required"}), 400

    if new_password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400

    if not validate_password(new_password):
        return jsonify({
            "message": "Password must meet complexity rules."
        }), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"message": "User not found with this email"}), 404

        pw_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password_hash = pw_hash
        db.commit()
        return jsonify({"message": "Password has been reset successfully"}), 200
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while resetting password.")
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
