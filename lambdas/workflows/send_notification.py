"""
Lambda handler for sending email notifications via SendGrid.
Part of Step Functions workflow.
"""
import json
import urllib.request
import urllib.error
from typing import Any, Dict

from config.settings import get_settings


def generate_email_html(ticket: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    Generate HTML email content for ticket notification.

    Args:
        ticket: Ticket data
        analysis: AI analysis results

    Returns:
        HTML email content
    """
    risk_colors = {
        "none": "#28a745",
        "low": "#17a2b8",
        "medium": "#ffc107",
        "high": "#fd7e14",
        "critical": "#dc3545",
    }

    risk_color = risk_colors.get(analysis.get("risk_level", "none"), "#6c757d")
    sensitive_text = "Yes" if analysis.get("sensitive_data_detected") else "No"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ticket Alert - Action Required</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: {risk_color};
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 20px -30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .alert-badge {{
                background-color: rgba(255,255,255,0.2);
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .content {{
                padding: 20px 0;
            }}
            .info-grid {{
                display: table;
                width: 100%;
                border-collapse: collapse;
            }}
            .info-row {{
                display: table-row;
            }}
            .info-label {{
                display: table-cell;
                padding: 10px 15px;
                background-color: #f8f9fa;
                font-weight: 600;
                width: 40%;
                border-bottom: 1px solid #eee;
            }}
            .info-value {{
                display: table-cell;
                padding: 10px 15px;
                border-bottom: 1px solid #eee;
            }}
            .risk-badge {{
                background-color: {risk_color};
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }}
            .description-box {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid {risk_color};
            }}
            .warning-box {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #666;
                font-size: 12px;
                text-align: center;
            }}
            .action-button {{
                display: inline-block;
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                text-decoration: none;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="alert-badge">⚠️ High Priority Alert</span>
                <h1>Ticket Requires Attention</h1>
            </div>

            <div class="content">
                <p>A ticket has been flagged for immediate review based on AI analysis.</p>

                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Ticket ID</div>
                        <div class="info-value">{ticket.get('id', 'N/A')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Status</div>
                        <div class="info-value">{ticket.get('status', 'N/A')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Category</div>
                        <div class="info-value">{analysis.get('category', 'N/A').title()}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">AI Priority</div>
                        <div class="info-value">{analysis.get('ai_priority', 'N/A').upper()}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Risk Level</div>
                        <div class="info-value">
                            <span class="risk-badge">{analysis.get('risk_level', 'N/A').upper()}</span>
                        </div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Sensitive Data</div>
                        <div class="info-value">{sensitive_text}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Created</div>
                        <div class="info-value">{ticket.get('created_at', 'N/A')}</div>
                    </div>
                </div>

                <h3 style="margin-top: 25px;">Description</h3>
                <div class="description-box">
                    {ticket.get('description', 'No description provided')}
                </div>

                <h3>AI Summary</h3>
                <p>{analysis.get('summary', 'No summary available')}</p>

                <h3>Recommended Action</h3>
                <p>{analysis.get('recommended_action', 'Review ticket manually')}</p>

                {''.join([f'''
                <div class="warning-box" style="background-color: #f8d7da; border-color: #dc3545;">
                    <strong>⚠️ Sensitive Data Detected</strong><br>
                    Types found: {', '.join(analysis.get('sensitive_data_types', []))}
                </div>
                ''') if analysis.get('sensitive_data_detected') else ''}
            </div>

            <div class="footer">
                <p>This is an automated notification from the Ticket Management System.</p>
                <p>Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_email_via_sendgrid(
    to_email: str,
    subject: str,
    html_content: str,
    settings: Any,
) -> Dict[str, Any]:
    """
    Send email using SendGrid API.

    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML email content
        settings: Application settings

    Returns:
        Result dictionary with success status
    """
    url = "https://api.sendgrid.com/v3/mail/send"

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject,
            }
        ],
        "from": {"email": settings.sendgrid_sender_email},
        "content": [
            {
                "type": "text/html",
                "value": html_content,
            }
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.sendgrid_api_key}",
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            return {
                "success": True,
                "status_code": response.status,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "Unknown error"
        return {
            "success": False,
            "error": f"SendGrid API error: {e.code} - {error_body}",
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Send email notification for high-risk tickets.

    Input:
    {
        "ticket_id": "...",
        "ticket": {...},
        "analysis": {...},
        "needs_notification": true/false,
        "error": null or "..."
    }

    Output:
    {
        "ticket_id": "...",
        "notification_sent": true/false,
        "notification_error": null or "..."
    }
    """
    try:
        # Check if notification is needed
        if not event.get("needs_notification", False):
            return {
                "ticket_id": event.get("ticket_id"),
                "notification_sent": False,
                "notification_error": None,
                "reason": "Notification not required",
            }

        settings = get_settings()

        # Validate API key
        if not settings.sendgrid_api_key:
            return {
                "ticket_id": event.get("ticket_id"),
                "notification_sent": False,
                "notification_error": "SendGrid API key not configured",
            }

        ticket = event.get("ticket", {})
        analysis = event.get("analysis", {})

        # Generate email content
        html_content = generate_email_html(ticket, analysis)

        # Determine subject
        risk_level = analysis.get("risk_level", "unknown")
        subject = f"[{risk_level.upper()}] Ticket Alert - {ticket.get('id', 'Unknown')[:8]}"

        # Send email to admin
        result = send_email_via_sendgrid(
            to_email=settings.admin_email,
            subject=subject,
            html_content=html_content,
            settings=settings,
        )

        return {
            "ticket_id": event.get("ticket_id"),
            "notification_sent": result.get("success", False),
            "notification_error": result.get("error"),
        }

    except Exception as e:
        print(f"Send notification error: {str(e)}")
        return {
            "ticket_id": event.get("ticket_id"),
            "notification_sent": False,
            "notification_error": str(e),
        }