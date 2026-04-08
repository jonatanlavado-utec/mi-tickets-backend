"""
Configuration settings for the Ticket Management System.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # API Keys
    groq_api_key: str
    sendgrid_api_key: str

    # DynamoDB Tables
    tickets_table: str
    users_table: str

    # SendGrid Configuration
    sendgrid_sender_email: str
    admin_email: str

    # Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # AWS Region
    aws_region: str = "us-east-1"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
            sendgrid_api_key=os.environ.get("SENDGRID_API_KEY", ""),
            tickets_table=os.environ.get("DYNAMODB_TABLE_TICKETS", "tickets"),
            users_table=os.environ.get("DYNAMODB_TABLE_USERS", "users"),
            jwt_secret=os.environ.get("JWT_SECRET", "change-me-in-production"),
            jwt_expiration_hours=int(os.environ.get("JWT_EXPIRATION_HOURS", "24")),
            sendgrid_sender_email=os.environ.get("SENDGRID_SENDER_EMAIL", "noreply@example.com"),
            admin_email=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings