from flask import jsonify

INTERNAL_ERROR_MESSAGE = "An unexpected server error occurred. Please try again."


def error_response(message, status_code=400):
    """Builds the standard JSON error payload used by every route."""
    return jsonify({"message": message}), status_code


def internal_error():
    """Generic 500 that never leaks exception details to the client."""
    return error_response(INTERNAL_ERROR_MESSAGE, 500)


def success_response(message=None, status_code=200, **payload):
    body = {"success": True}
    if message:
        body["message"] = message
    body.update(payload)
    return jsonify(body), status_code
