"""
Lambda handler for user login.
POST /auth/login
"""
import json
from typing import Any, Dict

from shared.response_utils import (
    create_response,
    bad_request_response,
    unauthorized_response,
    internal_error_response,
    parse_body,
)
from shared.auth_utils import verify_password, generate_token
from shared.dynamodb_client import get_users_table


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user login.

    Expected body:
    {
        "email": "user@example.com",
        "password": "securePassword123"
    }

    Returns:
        API Gateway response with user data and JWT token
    """
    try:
        body = parse_body(event)

        # Validate required fields
        email = body.get("email", "").strip().lower()
        password = body.get("password", "")

        if not email:
            return bad_request_response("Email is required")

        if not password:
            return bad_request_response("Password is required")

        # Get user from DynamoDB
        users_table = get_users_table()
        user = users_table.get_user_by_email(email)

        if not user:
            return unauthorized_response("Invalid email or password")

        # Verify password
        if not verify_password(password, user.get("password_hash", "")):
            return unauthorized_response("Invalid email or password")

        # Generate JWT token
        token = generate_token(user["id"], user["email"])

        # Return success (exclude password hash from response)
        return create_response(200, {
            "success": True,
            "data": {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "created_at": user["created_at"],
                },
                "token": token,
            },
        })

    except json.JSONDecodeError:
        return bad_request_response("Invalid JSON in request body")

    except Exception as e:
        print(f"Login error: {str(e)}")
        return internal_error_response("An unexpected error occurred")