#!/usr/bin/env python3
"""
Local development and testing script for Lambda functions.
Run this script to test Lambda functions locally before deployment.
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_mock_event(method: str, path: str, body: dict = None, headers: dict = None, path_params: dict = None, query_params: dict = None) -> dict:
    """
    Create a mock API Gateway event for testing.
    """
    event = {
        "httpMethod": method,
        "path": path,
        "headers": headers or {},
        "queryStringParameters": query_params,
        "pathParameters": path_params,
        "body": json.dumps(body) if body else None,
        "isBase64Encoded": False,
        "requestContext": {
            "requestId": "test-request-id",
            "stage": "test",
            "httpMethod": method,
            "path": path,
            "identity": {
                "sourceIp": "127.0.0.1",
                "userAgent": "test-client"
            }
        }
    }
    return event


def test_register():
    """Test user registration."""
    print("\n" + "=" * 50)
    print("Testing: POST /auth/register")
    print("=" * 50)

    from lambdas.auth.register import lambda_handler

    event = create_mock_event(
        method="POST",
        path="/auth/register",
        body={
            "email": "test@example.com",
            "password": "TestPass123",
            "name": "Test User"
        }
    )

    response = lambda_handler(event, None)
    print(f"Status: {response.get('statusCode')}")
    print(f"Response: {json.dumps(response.get('body'), indent=2)}")
    return response


def test_login():
    """Test user login."""
    print("\n" + "=" * 50)
    print("Testing: POST /auth/login")
    print("=" * 50)

    from lambdas.auth.login import lambda_handler

    event = create_mock_event(
        method="POST",
        path="/auth/login",
        body={
            "email": "test@example.com",
            "password": "TestPass123"
        }
    )

    response = lambda_handler(event, None)
    print(f"Status: {response.get('statusCode')}")
    print(f"Response: {json.dumps(response.get('body'), indent=2)}")

    # Extract token for subsequent tests
    if response.get('statusCode') == 200:
        body = json.loads(response.get('body', '{}'))
        return body.get('data', {}).get('token')
    return None


def test_create_ticket(token: str):
    """Test ticket creation."""
    print("\n" + "=" * 50)
    print("Testing: POST /tickets")
    print("=" * 50)

    from lambdas.tickets.create_ticket import lambda_handler

    event = create_mock_event(
        method="POST",
        path="/tickets",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        body={
            "description": "I'm having trouble uploading files larger than 10MB. My credit card number is 4111-1111-1111-1111. Please help!",
            "user_priority": "high"
        }
    )

    response = lambda_handler(event, None)
    print(f"Status: {response.get('statusCode')}")
    print(f"Response: {json.dumps(response.get('body'), indent=2)}")
    return response


def test_list_tickets(token: str):
    """Test listing tickets."""
    print("\n" + "=" * 50)
    print("Testing: GET /tickets")
    print("=" * 50)

    from lambdas.tickets.list_tickets import lambda_handler

    event = create_mock_event(
        method="GET",
        path="/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        },
        query_params={
            "limit": "10"
        }
    )

    response = lambda_handler(event, None)
    print(f"Status: {response.get('statusCode')}")
    print(f"Response: {json.dumps(response.get('body'), indent=2)}")
    return response


def test_analyze_ticket():
    """Test ticket analysis workflow."""
    print("\n" + "=" * 50)
    print("Testing: Analyze Ticket (Step Function)")
    print("=" * 50)

    from lambdas.workflows.analyze_ticket import lambda_handler

    event = {
        "ticket_id": "test-ticket-123",
        "description": "I'm having trouble uploading files. My SSN is 123-45-6789. Please help urgently!",
        "user_priority": "high",
        "user_id": "test-user-123",
        "created_at": "2024-01-15T10:00:00"
    }

    response = lambda_handler(event, None)
    print(f"Response: {json.dumps(response, indent=2)}")
    return response


def test_send_notification():
    """Test notification workflow."""
    print("\n" + "=" * 50)
    print("Testing: Send Notification (Step Function)")
    print("=" * 50)

    from lambdas.workflows.send_notification import lambda_handler

    event = {
        "ticket_id": "test-ticket-123",
        "ticket": {
            "id": "test-ticket-123",
            "description": "Test ticket description",
            "status": "analyzed",
            "created_at": "2024-01-15T10:00:00"
        },
        "analysis": {
            "category": "security",
            "ai_priority": "critical",
            "risk_level": "critical",
            "sensitive_data_detected": True,
            "sensitive_data_types": ["pii", "credentials"],
            "summary": "High-risk security issue with sensitive data exposure",
            "recommended_action": "Immediate escalation required"
        },
        "needs_notification": True
    }

    response = lambda_handler(event, None)
    print(f"Response: {json.dumps(response, indent=2)}")
    return response


def test_generate_report():
    """Test report generation."""
    print("\n" + "=" * 50)
    print("Testing: Generate Reports (Scheduled)")
    print("=" * 50)

    from lambdas.scheduled.generate_reports import lambda_handler

    event = {
        "report_type": "weekly"
    }

    response = lambda_handler(event, None)
    print(f"Response: {json.dumps(response, indent=2)}")
    return response


def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "=" * 60)
    print("Running Local Lambda Function Tests")
    print("=" * 60)

    # Note: These tests require DynamoDB to be available
    # For local testing, use DynamoDB Local or moto

    print("\n⚠️  Note: These tests require:")
    print("   - DynamoDB tables created (or DynamoDB Local)")
    print("   - Environment variables set:")
    print("     - DYNAMODB_TABLE_TICKETS")
    print("     - DYNAMODB_TABLE_USERS")
    print("     - GROQ_API_KEY")
    print("     - SENDGRID_API_KEY")
    print("     - JWT_SECRET")

    try:
        # Test auth endpoints
        test_register()
        token = test_login()

        if token:
            # Test ticket endpoints
            test_create_ticket(token)
            test_list_tickets(token)

        # Test workflow functions
        test_analyze_ticket()
        test_send_notification()

        # Test scheduled function
        test_generate_report()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()