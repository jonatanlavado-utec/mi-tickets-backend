"""
Response utilities for Lambda functions.
"""
import json
from typing import Any, Dict, Optional


def create_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standard API Gateway Lambda response.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Optional additional headers

    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body) if not isinstance(body, str) else body,
    }


def success_response(data: Any) -> Dict[str, Any]:
    """Create a successful response (200)."""
    return create_response(200, {"success": True, "data": data})


def created_response(data: Any) -> Dict[str, Any]:
    """Create a created response (201)."""
    return create_response(201, {"success": True, "data": data})


def bad_request_response(message: str) -> Dict[str, Any]:
    """Create a bad request response (400)."""
    return create_response(400, {"success": False, "error": message})


def unauthorized_response(message: str = "Unauthorized") -> Dict[str, Any]:
    """Create an unauthorized response (401)."""
    return create_response(401, {"success": False, "error": message})


def forbidden_response(message: str = "Forbidden") -> Dict[str, Any]:
    """Create a forbidden response (403)."""
    return create_response(403, {"success": False, "error": message})


def not_found_response(message: str = "Not found") -> Dict[str, Any]:
    """Create a not found response (404)."""
    return create_response(404, {"success": False, "error": message})


def internal_error_response(message: str = "Internal server error") -> Dict[str, Any]:
    """Create an internal server error response (500)."""
    return create_response(500, {"success": False, "error": message})


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the body from a Lambda event.

    Args:
        event: Lambda event dictionary

    Returns:
        Parsed body as dictionary
    """
    body = event.get("body")
    if body is None:
        return {}

    if isinstance(body, str):
        return json.loads(body)

    return body