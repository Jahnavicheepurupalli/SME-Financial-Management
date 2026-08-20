from flask import jsonify


def error_response(message, status_code=400):
    """Builds the standard JSON error payload used by every route."""
    return jsonify({"message": message}), status_code


def server_error(exc):
    return error_response(f"Server error: {str(exc)}", 500)


def success_response(message=None, status_code=200, **payload):
    body = {"success": True}
    if message:
        body["message"] = message
    body.update(payload)
    return jsonify(body), status_code
