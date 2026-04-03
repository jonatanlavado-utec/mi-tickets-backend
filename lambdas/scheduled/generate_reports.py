"""
Lambda handler for scheduled ticket report generation.
Triggered by EventBridge (weekly/monthly).
"""
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Any, Dict, List

from config.settings import get_settings
from shared.dynamodb_client import get_tickets_table


def get_date_range(report_type: str) -> tuple[str, str]:
    """
    Get date range for the report.

    Args:
        report_type: 'weekly' or 'monthly'

    Returns:
        Tuple of (start_date, end_date) as ISO strings
    """
    now = datetime.utcnow()

    if report_type == "weekly":
        # Last 7 days
        start = now - timedelta(days=7)
    else:
        # Last 30 days
        start = now - timedelta(days=30)

    return start.isoformat(), now.isoformat()


def generate_report_html(
    report_data: Dict[str, Any],
    report_type: str,
    start_date: str,
    end_date: str,
) -> str:
    """
    Generate HTML email content for the report.

    Args:
        report_data: Report data dictionary
        report_type: 'weekly' or 'monthly'
        start_date: Report start date
        end_date: Report end date

    Returns:
        HTML email content
    """
    high_risk_tickets = report_data.get("high_risk_tickets", [])
    counts = report_data.get("counts", {})

    # Format high risk tickets table
    tickets_rows = ""
    for ticket in high_risk_tickets[:10]:  # Limit to 10
        tickets_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{ticket.get('id', 'N/A')[:8]}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{ticket.get('category', 'N/A')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">
                    {ticket.get('risk_level', 'N/A').upper()}
                </span>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{ticket.get('created_at', 'N/A')[:10]}</td>
        </tr>
        """

    if not high_risk_tickets:
        tickets_rows = '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #666;">No high-risk tickets in this period</td></tr>'

    # Format status breakdown
    status_items = ""
    for status, count in counts.get("by_status", {}).items():
        status_items += f'<span style="display: inline-block; background: #e9ecef; padding: 5px 12px; border-radius: 15px; margin: 3px;">{status}: {count}</span>'

    # Format category breakdown
    category_items = ""
    for category, count in counts.get("by_category", {}).items():
        category_items += f'<span style="display: inline-block; background: #d4edda; padding: 5px 12px; border-radius: 15px; margin: 3px;">{category}: {count}</span>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_type.title()} Ticket Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 700px;
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 25px -30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin: 25px 0;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .stat-number {{
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
            }}
            .stat-label {{
                color: #666;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section h2 {{
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background-color: #667eea;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #666;
                font-size: 12px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 {report_type.title()} Ticket Report</h1>
                <p>{start_date[:10]} to {end_date[:10]}</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{counts.get('total', 0)}</div>
                    <div class="stat-label">Total Tickets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #dc3545;">{len(high_risk_tickets)}</div>
                    <div class="stat-label">High Risk</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #28a745;">{counts.get('by_status', {}).get('resolved', 0)}</div>
                    <div class="stat-label">Resolved</div>
                </div>
            </div>

            <div class="section">
                <h2>Tickets by Status</h2>
                <div style="padding: 15px 0;">
                    {status_items}
                </div>
            </div>

            <div class="section">
                <h2>Tickets by Category</h2>
                <div style="padding: 15px 0;">
                    {category_items}
                </div>
            </div>

            <div class="section">
                <h2>⚠️ High Risk Tickets</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Category</th>
                            <th>Risk</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tickets_rows}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p>This report was automatically generated by the Ticket Management System.</p>
                <p>Generated on: {datetime.utcnow().isoformat()}</p>
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
    Generate and send scheduled ticket report.

    EventBridge input:
    {
        "report_type": "weekly" or "monthly"
    }

    Returns:
        Result dictionary
    """
    try:
        settings = get_settings()
        report_type = event.get("report_type", "weekly")

        # Get date range
        start_date, end_date = get_date_range(report_type)

        # Get tickets from DynamoDB
        tickets_table = get_tickets_table()

        # Get ticket counts
        counts = tickets_table.get_ticket_counts()

        # Get high-risk tickets
        high_risk_tickets = tickets_table.get_high_risk_tickets()

        # Get tickets in date range
        tickets_in_range = tickets_table.get_tickets_by_date_range(start_date, end_date)

        # Filter counts to only include tickets in date range
        period_counts = {
            "total": len(tickets_in_range),
            "by_status": {},
            "by_priority": {},
            "by_risk_level": {},
            "by_category": {},
        }

        for ticket in tickets_in_range:
            status = ticket.get("status", "unknown")
            period_counts["by_status"][status] = period_counts["by_status"].get(status, 0) + 1

            priority = ticket.get("ai_priority") or ticket.get("user_priority", "unknown")
            period_counts["by_priority"][priority] = period_counts["by_priority"].get(priority, 0) + 1

            risk = ticket.get("risk_level", "none")
            period_counts["by_risk_level"][risk] = period_counts["by_risk_level"].get(risk, 0) + 1

            category = ticket.get("category", "uncategorized")
            period_counts["by_category"][category] = period_counts["by_category"].get(category, 0) + 1

        # Generate report
        report_data = {
            "counts": period_counts,
            "high_risk_tickets": high_risk_tickets,
            "period": {
                "start": start_date,
                "end": end_date,
            },
        }

        html_content = generate_report_html(
            report_data,
            report_type,
            start_date,
            end_date,
        )

        # Send email
        if settings.sendgrid_api_key:
            subject = f"📊 {report_type.title()} Ticket Report - {datetime.utcnow().strftime('%Y-%m-%d')}"
            result = send_email_via_sendgrid(
                to_email=settings.admin_email,
                subject=subject,
                html_content=html_content,
                settings=settings,
            )

            return {
                "success": result.get("success", False),
                "report_type": report_type,
                "tickets_in_period": period_counts["total"],
                "high_risk_count": len(high_risk_tickets),
                "email_sent": result.get("success", False),
                "error": result.get("error"),
            }
        else:
            # Log report without sending email
            print(f"Report generated (no SendGrid key): {json.dumps(report_data, indent=2)}")
            return {
                "success": True,
                "report_type": report_type,
                "tickets_in_period": period_counts["total"],
                "high_risk_count": len(high_risk_tickets),
                "email_sent": False,
                "error": "SendGrid API key not configured",
            }

    except Exception as e:
        print(f"Report generation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }