import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from flask_bcrypt import Bcrypt
from backend.database.db import session_scope
from backend.models.models import User
from backend.utils.responses import error_response, server_error
from backend.utils.serializers import serialize_user

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
    """Maps a Google token verification failure onto a user-facing message."""
    err_str = str(exc).lower()
    if "client" in err_str or "audience" in err_str:
        return GOOGLE_UNAVAILABLE_MESSAGE
    if any(kw in err_str for kw in ("test", "access_denied", "unauthorized", "consent")):
        return GOOGLE_UNAUTHORIZED_MESSAGE
    return GOOGLE_VERIFY_FAILED_MESSAGE


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    print(f"[DEBUG] Incoming signup request: {data}")
    
    full_name = data.get('name') or data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([full_name, email, password]):
        print("[DEBUG] Signup validation failed: missing name, email, or password.")
        return error_response("Name, email, and password are required")

    if confirm_password and password != confirm_password:
        print("[DEBUG] Signup validation failed: password mismatch.")
        return error_response("Passwords do not match")

    if not validate_password(password):
        print("[DEBUG] Signup validation failed: password does not meet complexity rules.")
        return error_response(
            "Password must be at least 8 characters long, contain an uppercase letter, "
            "a lowercase letter, a number, and a special character."
        )

    try:
        with session_scope() as db:
            if get_user_by_email(db, email):
                print(f"[DEBUG] Signup failed: email {email} already registered.")
                return error_response("Email already registered")

            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(full_name=full_name, email=email, password_hash=pw_hash)

            db.add(new_user)
            db.commit()
            print(f"[DEBUG] Signup success: user {email} created.")
            return jsonify({
                "success": True,
                "message": "Registration successful",
                "user": serialize_user(new_user)
            }), 201
    except Exception as e:
        print(f"[DEBUG] Signup Exception: {str(e)}")
        return server_error(e)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return error_response("Email and password are required")

    try:
        with session_scope() as db:
            user = get_user_by_email(db, email)
            if not user or not user.password_hash:
                return error_response("Invalid email or password", 401)

            if not bcrypt.check_password_hash(user.password_hash, password):
                return error_response("Invalid email or password", 401)

            return auth_session_response(user, "Login successful")
    except Exception as e:
        return server_error(e)

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
    except Exception as e:
        print(f"[DEBUG OAUTH] Token verification failed: {e}")
        return error_response(google_error_message(e), 401)

    try:
        with session_scope() as db:
            user = get_user_by_email(db, email)
            if not user:
                # Create user on the fly
                user = User(full_name=full_name, email=email, password_hash=None)
                db.add(user)
                db.commit()
                db.refresh(user)

            return auth_session_response(user, "Google authentication successful")
    except Exception as e:
        return server_error(e)

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
        with session_scope() as db:
            user = get_user_by_email(db, email)
            if not user:
                return error_response("User not found with this email", 404)

            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.commit()
            return jsonify({"message": "Password has been reset successfully"}), 200
    except Exception as e:
        return server_error(e)

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    with session_scope() as db:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return error_response("User not found", 404)
        return jsonify({"user": serialize_user(user)}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(resp)
    return resp, 200
