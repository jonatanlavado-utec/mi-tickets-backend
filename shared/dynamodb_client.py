"""
DynamoDB client utilities.
"""
import boto3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
from config.settings import get_settings

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name=get_settings().aws_region)


class TicketsTable:
    """DynamoDB tickets table operations."""

    def __init__(self):
        self.table = dynamodb.Table(get_settings().tickets_table)

    def create_ticket(
        self,
        user_id: str,
        description: str,
        user_priority: str = "medium",
    ) -> Dict[str, Any]:
        """
        Create a new ticket.

        Args:
            user_id: ID of the user creating the ticket
            description: Ticket description
            user_priority: Priority set by user (low, medium, high, critical)

        Returns:
            Created ticket dictionary
        """
        ticket_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        ticket = {
            "id": ticket_id,
            "user_id": user_id,
            "description": description,
            "user_priority": user_priority,
            "ai_priority": None,  # Filled by AI analysis
            "category": None,  # Filled by AI analysis
            "risk_level": None,  # Filled by AI analysis
            "sensitive_data_detected": False,
            "sensitive_data_types": [],
            "status": "pending_analysis",
            "created_at": now,
            "updated_at": now,
        }

        self.table.put_item(Item=ticket)
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a ticket by ID.

        Args:
            ticket_id: Ticket ID

        Returns:
            Ticket dictionary or None if not found
        """
        try:
            response = self.table.get_item(Key={"id": ticket_id})
            return response.get("Item")
        except ClientError:
            return None

    def get_tickets_by_user(
        self,
        user_id: str,
        limit: int = 20,
        last_key: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get all tickets for a user with pagination.

        Args:
            user_id: User ID
            limit: Maximum number of items to return
            last_key: Last evaluated key for pagination

        Returns:
            Dictionary with items and pagination info
        """
        query_params = {
            "IndexName": "user_id-created_at-index",
            "KeyConditionExpression": "user_id = :uid",
            "ExpressionAttributeValues": {":uid": user_id},
            "Limit": limit,
            "ScanIndexForward": False,  # Sort by created_at descending
        }

        if last_key:
            query_params["ExclusiveStartKey"] = last_key

        response = self.table.query(**query_params)

        return {
            "items": response.get("Items", []),
            "count": response.get("Count", 0),
            "last_key": response.get("LastEvaluatedKey"),
        }

    def update_ticket_analysis(
        self,
        ticket_id: str,
        ai_priority: str,
        category: str,
        risk_level: str,
        sensitive_data_detected: bool,
        sensitive_data_types: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Update ticket with AI analysis results.

        Args:
            ticket_id: Ticket ID
            ai_priority: Priority determined by AI
            category: Ticket category
            risk_level: Risk level assessment
            sensitive_data_detected: Whether sensitive data was detected
            sensitive_data_types: List of sensitive data types found

        Returns:
            Updated ticket dictionary or None if not found
        """
        try:
            response = self.table.update_item(
                Key={"id": ticket_id},
                UpdateExpression="""
                    SET ai_priority = :ai_priority,
                        category = :category,
                        risk_level = :risk_level,
                        sensitive_data_detected = :sensitive,
                        sensitive_data_types = :sensitive_types,
                        status = :status,
                        updated_at = :updated_at
                """,
                ExpressionAttributeValues={
                    ":ai_priority": ai_priority,
                    ":category": category,
                    ":risk_level": risk_level,
                    ":sensitive": sensitive_data_detected,
                    ":sensitive_types": sensitive_data_types,
                    ":status": "analyzed",
                    ":updated_at": datetime.utcnow().isoformat(),
                },
                ReturnValues="ALL_NEW",
            )
            return response.get("Attributes")
        except ClientError:
            return None

    def update_status(self, ticket_id: str, status: str) -> Optional[Dict[str, Any]]:
        """
        Update ticket status.

        Args:
            ticket_id: Ticket ID
            status: New status

        Returns:
            Updated ticket dictionary or None if not found
        """
        try:
            response = self.table.update_item(
                Key={"id": ticket_id},
                UpdateExpression="SET #s = :status, updated_at = :updated_at",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":status": status,
                    ":updated_at": datetime.utcnow().isoformat(),
                },
                ReturnValues="ALL_NEW",
            )
            return response.get("Attributes")
        except ClientError:
            return None

    def get_tickets_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all tickets with a specific status."""
        response = self.table.scan(
            FilterExpression="#s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": status},
        )
        return response.get("Items", [])

    def get_tickets_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Get tickets within a date range."""
        response = self.table.scan(
            FilterExpression="created_at BETWEEN :start AND :end",
            ExpressionAttributeValues={
                ":start": start_date,
                ":end": end_date,
            },
        )
        return response.get("Items", [])

    def get_high_risk_tickets(self) -> List[Dict[str, Any]]:
        """Get all high-risk tickets."""
        response = self.table.scan(
            FilterExpression="risk_level = :high OR risk_level = :critical",
            ExpressionAttributeValues={
                ":high": "high",
                ":critical": "critical",
            },
        )
        return response.get("Items", [])

    def get_ticket_counts(self) -> Dict[str, int]:
        """Get ticket counts by various dimensions."""
        response = self.table.scan()

        counts = {
            "total": 0,
            "by_status": {},
            "by_priority": {},
            "by_risk_level": {},
            "by_category": {},
        }

        for item in response.get("Items", []):
            counts["total"] += 1

            status = item.get("status", "unknown")
            counts["by_status"][status] = counts["by_status"].get(status, 0) + 1

            priority = item.get("ai_priority") or item.get("user_priority", "unknown")
            counts["by_priority"][priority] = counts["by_priority"].get(priority, 0) + 1

            risk = item.get("risk_level", "none")
            counts["by_risk_level"][risk] = counts["by_risk_level"].get(risk, 0) + 1

            category = item.get("category", "uncategorized")
            counts["by_category"][category] = counts["by_category"].get(category, 0) + 1

        return counts


class UsersTable:
    """DynamoDB users table operations."""

    def __init__(self):
        self.table = dynamodb.Table(get_settings().users_table)

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            email: User email
            password_hash: Hashed password
            name: User name

        Returns:
            Created user dictionary
        """
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        user = {
            "id": user_id,
            "email": email.lower(),
            "password_hash": password_hash,
            "name": name,
            "created_at": now,
            "updated_at": now,
        }

        self.table.put_item(
            Item=user,
            ConditionExpression="attribute_not_exists(email)",
        )
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            response = self.table.get_item(Key={"email": email.lower()})
            return response.get("Item")
        except ClientError:
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = self.table.get_item(Key={"id": user_id})
            return response.get("Item")
        except ClientError:
            return None


# Singleton instances
_tickets_table: Optional[TicketsTable] = None
_users_table: Optional[UsersTable] = None


def get_tickets_table() -> TicketsTable:
    """Get or create tickets table instance."""
    global _tickets_table
    if _tickets_table is None:
        _tickets_table = TicketsTable()
    return _tickets_table


def get_users_table() -> UsersTable:
    """Get or create users table instance."""
    global _users_table
    if _users_table is None:
        _users_table = UsersTable()
    return _users_table