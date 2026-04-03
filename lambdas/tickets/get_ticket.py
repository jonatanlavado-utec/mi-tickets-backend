"""
Lambda handler for getting a single ticket.
GET /tickets/{id}
"""
from typing import Any, Dict

from shared.response_utils import (
    not_found_response,
    unauthorized_response,
    forbidden_response,
    internal_error_response,
)
from shared.auth_utils import get_user_from_event
from shared.dynamodb_client import get_tickets_table


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle get ticket request.

    Path parameters:
        id: Ticket ID

    Returns:
        API Gateway response with ticket data
    """
    try:
        # Get authenticated user
        user = get_user_from_event(event)
        if not user:
            return unauthorized_response("Authentication required")

        # Get ticket ID from path parameters
        path_params = event.get("pathParameters") or {}
        ticket_id = path_params.get("id")

        if not ticket_id:
            return not_found_response("Ticket ID is required")

        # Get ticket from DynamoDB
        tickets_table = get_tickets_table()
        ticket = tickets_table.get_ticket(ticket_id)

        if not ticket:
            return not_found_response("Ticket not found")

        # Verify user owns the ticket
        if ticket.get("user_id") != user["user_id"]:
            return forbidden_response("You do not have access to this ticket")

        # Return success
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": {
                "success": True,
                "data": {"ticket": ticket},
            },
        }

    except Exception as e:
        print(f"Get ticket error: {str(e)}")
        return internal_error_response("An unexpected error occurred")