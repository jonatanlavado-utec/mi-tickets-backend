"""
Lambda handler for user registration.
POST /auth/register
"""
import json
import re
from typing import Any, Dict

from shared.response_utils import (
    create_response,
    success_response,
    bad_request_response,
    internal_error_response,
    parse_body,
)
from shared.auth_utils import hash_password, generate_token
from shared.dynamodb_client import get_users_table
from botocore.exceptions import ClientError


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Requirements: Minimum 8 characters, at least one letter and one number.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    return True, ""


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user registration.

    Expected body:
    {
        "email": "user@example.com",
        "password": "securePassword123",
        "name": "John Doe"
    }

    Returns:
        API Gateway response with user data and JWT token
    """
    try:
        body = parse_body(event)

        # Validate required fields
        email = body.get("email", "").strip()
        password = body.get("password", "")
        name = body.get("name", "").strip()

        if not email:
            return bad_request_response("Email is required")

        if not password:
            return bad_request_response("Password is required")

        if not name:
            return bad_request_response("Name is required")

        # Validate email format
        if not validate_email(email):
            return bad_request_response("Invalid email format")

        # Validate password strength
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return bad_request_response(error_msg)

        # Hash password
        password_hash = hash_password(password)

        # Create user in DynamoDB
        users_table = get_users_table()
        user = users_table.create_user(
            email=email,
            password_hash=password_hash,
            name=name,
        )

        # Generate JWT token
        token = generate_token(user["id"], user["email"])

        # Return success (exclude password hash from response)
        return create_response(201, {
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

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")

        if error_code == "ConditionalCheckFailedException":
            return bad_request_response("Email already registered")

        return internal_error_response("Failed to create user")

    except json.JSONDecodeError:
        return bad_request_response("Invalid JSON in request body")

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return internal_error_response("An unexpected error occurred")