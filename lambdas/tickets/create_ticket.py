"""
Lambda handler for creating a new ticket.
POST /tickets
"""
import os
import json
import boto3
from typing import Any, Dict
from datetime import datetime

from shared.response_utils import (
    create_response,
    bad_request_response,
    unauthorized_response,
    internal_error_response,
    parse_body,
)
from shared.auth_utils import get_user_from_event
from shared.dynamodb_client import get_tickets_table
from config.settings import get_settings

# Initialize Step Functions client
stepfunctions = boto3.client("stepfunctions")


def validate_priority(priority: str) -> bool:
    """Validate priority value."""
    valid_priorities = ["low", "medium", "high", "critical"]
    return priority.lower() in valid_priorities


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle ticket creation.

    Expected body:
    {
        "description": "Issue description here...",
        "user_priority": "high"  // optional, default: "medium"
    }

    Returns:
        API Gateway response with created ticket
    """
    try:
        # Get authenticated user
        user = get_user_from_event(event)
        if not user:
            return unauthorized_response("Authentication required")

        body = parse_body(event)

        # Validate required fields
        description = body.get("description", "").strip()
        user_priority = body.get("user_priority", "medium").lower()

        if not description:
            return bad_request_response("Description is required")

        if len(description) < 10:
            return bad_request_response("Description must be at least 10 characters")

        if len(description) > 5000:
            return bad_request_response("Description must not exceed 5000 characters")

        if not validate_priority(user_priority):
            return bad_request_response(
                "Invalid priority. Must be one of: low, medium, high, critical"
            )

        # Create ticket in DynamoDB
        tickets_table = get_tickets_table()
        ticket = tickets_table.create_ticket(
            user_id=user["user_id"],
            description=description,
            user_priority=user_priority,
        )

        # Trigger Step Functions workflow for AI analysis
        try:
            settings = get_settings()

            # Get the state machine ARN from environment
            state_machine_arn = settings.__dict__.get(
                "STEP_FUNCTION_ARN",
                os.environ.get("STEP_FUNCTION_ARN", "")
            )

            if state_machine_arn:
                stepfunctions.start_execution(
                    stateMachineArn=state_machine_arn,
                    name=f"analyze-{ticket['id']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    input=json.dumps({
                        "ticket_id": ticket["id"],
                        "description": description,
                        "user_priority": user_priority,
                        "user_id": user["user_id"],
                        "created_at": ticket["created_at"],
                    }),
                )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to start Step Function: {str(e)}")

        # Return success
        return create_response(201, {
            "success": True,
            "data": {
                "ticket": ticket,
                "message": "Ticket created. AI analysis in progress.",
            },
        })

    except json.JSONDecodeError:
        return bad_request_response("Invalid JSON in request body")

    except Exception as e:
        print(f"Create ticket error: {str(e)}")
        return internal_error_response("An unexpected error occurred")


