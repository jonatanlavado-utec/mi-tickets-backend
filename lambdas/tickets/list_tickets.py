"""
Lambda handler for listing tickets.
GET /tickets
"""
import json
from typing import Any, Dict

from shared.response_utils import (
    create_response,
    bad_request_response,
    unauthorized_response,
    internal_error_response,
)
from shared.auth_utils import get_user_from_event
from shared.dynamodb_client import get_tickets_table


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle list tickets request.

    Query parameters:
        limit: Maximum number of items to return (default: 20, max: 100)
        status: Filter by status (optional)
        last_key: Pagination token (optional)

    Returns:
        API Gateway response with tickets list
    """
    try:
        # Get authenticated user
        user = get_user_from_event(event)
        if not user:
            return unauthorized_response("Authentication required")

        # Get query parameters
        query_params = event.get("queryStringParameters") or {}

        limit = min(int(query_params.get("limit", "20")), 100)
        status_filter = query_params.get("status")
        last_key_str = query_params.get("last_key")

        # Parse pagination key
        last_key = None
        if last_key_str:
            try:
                last_key = json.loads(last_key_str)
            except json.JSONDecodeError:
                return bad_request_response("Invalid pagination token")

        # Get tickets from DynamoDB
        tickets_table = get_tickets_table()
        result = tickets_table.get_tickets_by_user(
            user_id=user["user_id"],
            limit=limit,
            last_key=last_key,
        )

        # Apply status filter if provided
        tickets = result["items"]
        if status_filter:
            tickets = [
                t for t in tickets
                if t.get("status") == status_filter
            ]

        # Prepare response
        response_data = {
            "tickets": tickets,
            "count": len(tickets),
        }

        # Include pagination token if there are more results
        if result.get("last_key"):
            response_data["pagination"] = {
                "last_key": json.dumps(result["last_key"]),
                "has_more": True,
            }

        return create_response(200, {"success": True, "data": response_data})

    except ValueError as e:
        return bad_request_response(str(e))

    except Exception as e:
        print(f"List tickets error: {str(e)}")
        return internal_error_response("An unexpected error occurred")