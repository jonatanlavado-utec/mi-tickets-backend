"""
Lambda handler for AI ticket analysis using Groq API.
Part of Step Functions workflow.
"""
import json
import urllib.request
import urllib.error
from typing import Any, Dict

from config.settings import get_settings


# Prompt template for ticket analysis
ANALYSIS_PROMPT = """
You are a ticket analysis assistant. Analyze the following support ticket and provide a structured assessment.

Ticket Description:
{description}

User-assigned Priority: {user_priority}

Analyze and respond with ONLY a valid JSON object (no markdown, no explanation) with these fields:
{{
    "category": one of ["technical", "billing", "security", "general", "feature_request", "bug", "account"],
    "ai_priority": one of ["low", "medium", "high", "critical"],
    "risk_level": one of ["none", "low", "medium", "high", "critical"],
    "sensitive_data_detected": boolean (true if PII, credentials, financial data, or security info detected),
    "sensitive_data_types": array of detected types from ["pii", "credentials", "financial", "health", "security", "legal", "none"],
    "summary": brief 1-2 sentence summary of the issue,
    "recommended_action": suggested next step,
    "confidence_score": number between 0 and 1
}}

Consider:
- Category: Match to the most appropriate category
- AI Priority: Based on urgency and impact (higher than user priority if security/financial)
- Risk Level: Higher if sensitive data detected or security implications
- Sensitive Data: Look for emails, phone numbers, SSN, credit cards, passwords, API keys, health info
"""


def call_groq_api(prompt: str, settings: Any) -> Dict[str, Any]:
    """
    Call Groq API for ticket analysis.

    Args:
        prompt: Analysis prompt
        settings: Application settings

    Returns:
        Analysis result dictionary
    """
    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a structured data extraction assistant. Always respond with valid JSON only, no other text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.groq_api_key}",
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

            # Extract content from response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

            # Parse JSON response
            # Clean up potential markdown code blocks
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            analysis = json.loads(content)

            return {
                "success": True,
                "analysis": analysis,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "Unknown error"
        return {
            "success": False,
            "error": f"Groq API error: {e.code} - {error_body}",
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse API response: {str(e)}",
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle ticket analysis as part of Step Functions workflow.

    Input:
    {
        "ticket_id": "...",
        "description": "...",
        "user_priority": "...",
        "user_id": "...",
        "created_at": "..."
    }

    Output:
    {
        "ticket_id": "...",
        "analysis": {...},
        "error": null  // or error message if failed
    }
    """
    try:
        settings = get_settings()

        # Validate API key
        if not settings.groq_api_key:
            return {
                "ticket_id": event.get("ticket_id"),
                "error": "Groq API key not configured",
                "analysis": get_default_analysis(event.get("user_priority", "medium")),
            }

        # Prepare prompt
        prompt = ANALYSIS_PROMPT.format(
            description=event.get("description", ""),
            user_priority=event.get("user_priority", "medium"),
        )

        # Call Groq API
        result = call_groq_api(prompt, settings)

        if result.get("success"):
            return {
                "ticket_id": event.get("ticket_id"),
                "analysis": result["analysis"],
                "error": None,
            }
        else:
            # Return default analysis on failure
            return {
                "ticket_id": event.get("ticket_id"),
                "error": result.get("error"),
                "analysis": get_default_analysis(event.get("user_priority", "medium")),
            }

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return {
            "ticket_id": event.get("ticket_id"),
            "error": str(e),
            "analysis": get_default_analysis(event.get("user_priority", "medium")),
        }


def get_default_analysis(user_priority: str) -> Dict[str, Any]:
    """
    Get default analysis when AI fails.

    Args:
        user_priority: User-assigned priority

    Returns:
        Default analysis dictionary
    """
    return {
        "category": "general",
        "ai_priority": user_priority,
        "risk_level": "none",
        "sensitive_data_detected": False,
        "sensitive_data_types": [],
        "summary": "Analysis unavailable - manual review recommended",
        "recommended_action": "Manual review required",
        "confidence_score": 0,
    }