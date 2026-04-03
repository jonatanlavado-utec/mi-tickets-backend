"""
Lambda handler for updating ticket with AI analysis results.
Part of Step Functions workflow.
"""
from typing import Any, Dict

from shared.dynamodb_client import get_tickets_table


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update ticket with AI analysis results.

    Input:
    {
        "ticket_id": "...",
        "analysis": {
            "category": "...",
            "ai_priority": "...",
            "risk_level": "...",
            "sensitive_data_detected": true/false,
            "sensitive_data_types": [...],
            ...
        },
        "error": null or "...",
        "user_id": "..."
    }

    Output:
    {
        "ticket_id": "...",
        "ticket": {...},
        "analysis": {...},
        "needs_notification": true/false,
        "error": null or "..."
    }
    """
    try:
        ticket_id = event.get("ticket_id")
        analysis = event.get("analysis", {})

        if not ticket_id:
            return {
                "error": "Missing ticket_id",
                "needs_notification": False,
            }

        # Update ticket in DynamoDB
        tickets_table = get_tickets_table()

        updated_ticket = tickets_table.update_ticket_analysis(
            ticket_id=ticket_id,
            ai_priority=analysis.get("ai_priority", "medium"),
            category=analysis.get("category", "general"),
            risk_level=analysis.get("risk_level", "none"),
            sensitive_data_detected=analysis.get("sensitive_data_detected", False),
            sensitive_data_types=analysis.get("sensitive_data_types", []),
        )

        if not updated_ticket:
            return {
                "ticket_id": ticket_id,
                "error": f"Ticket not found: {ticket_id}",
                "needs_notification": False,
            }

        # Determine if notification is needed
        needs_notification = should_send_notification(analysis)

        return {
            "ticket_id": ticket_id,
            "ticket": updated_ticket,
            "analysis": analysis,
            "needs_notification": needs_notification,
            "error": event.get("error"),
        }

    except Exception as e:
        print(f"Update ticket error: {str(e)}")
        return {
            "ticket_id": event.get("ticket_id"),
            "error": str(e),
            "needs_notification": False,
        }


def should_send_notification(analysis: Dict[str, Any]) -> bool:
    """
    Determine if email notification should be sent.

    Args:
        analysis: AI analysis results

    Returns:
        True if notification should be sent
    """
    # Send notification for high/critical risk
    risk_level = analysis.get("risk_level", "none")
    if risk_level in ["high", "critical"]:
        return True

    # Send notification if sensitive data detected
    if analysis.get("sensitive_data_detected", False):
        return True

    return False