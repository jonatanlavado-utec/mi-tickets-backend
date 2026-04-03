# Ticket Management System - Serverless Backend

AWS serverless architecture for intelligent ticket management with AI-powered analysis.

## Architecture Overview

```
                                    ┌─────────────────────────────────────────────────────────────────┐
                                    │                        AWS Cloud                                │
                                    │                                                                 │
┌──────────────┐                   │  ┌──────────────┐         ┌─────────────────────────────────┐ │
│              │                   │  │ API Gateway  │         │        Step Functions          │ │
│   Client     │ ─────────────────┼──▶   (REST)     ├────────▶│     (Ticket Workflow)          │ │
│  (Frontend)  │                   │  └──────┬───────┘         │                                 │ │
│              │                   │         │                 │  ┌─────────────────────────┐   │ │
└──────────────┘                   │         │                 │  │ 1. Analyze (Groq API)   │   │ │
                                   │         ▼                 │  │ 2. Update DynamoDB      │   │ │
                                   │  ┌──────┴───────┐         │  │ 3. Send Email (SendGrid)│   │ │
                                   │  │   Lambda     │         │  └─────────────────────────┘   │ │
                                   │  │  Functions   │         │                                 │ │
                                   │  └──────┬───────┘         └────────────────┬────────────────┘ │
                                   │         │                                  │                  │
                                   │         ▼                                  ▼                  │
                                   │  ┌──────┴──────────────────────────────────┴───────┐        │
                                   │  │                   DynamoDB                       │        │
                                   │  │              (Tickets Table)                     │        │
                                   │  └────────────────────────────────────────────────┘        │
                                   │                                                                 │
                                   │  ┌──────────────┐         ┌──────────────┐                │
                                   │  │ EventBridge  │────────▶│   Lambda     │                │
                                   │  │  (Schedule)  │         │   (Reports)  │                │
                                   │  └──────────────┘         └──────┬───────┘                │
                                   │                                    │                        │
                                   │                                    ▼                        │
                                   │                           ┌──────────────┐                │
                                   │                           │   SendGrid   │                │
                                   │                           │  (Reports)   │                │
                                   │                           └──────────────┘                │
                                   │                                                                 │
                                   └─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Method | Endpoint          | Description              |
|--------|-------------------|--------------------------|
| POST   | /auth/register    | Register new user        |
| POST   | /auth/login       | Authenticate user        |
| POST   | /tickets          | Create new ticket        |
| GET    | /tickets          | List user's tickets      |
| GET    | /tickets/{id}     | Get ticket details       |

## Project Structure

```
ticket-ya-backend/
├── lambdas/
│   ├── auth/
│   │   ├── register.py
│   │   └── login.py
│   ├── tickets/
│   │   ├── create_ticket.py
│   │   ├── get_ticket.py
│   │   └── list_tickets.py
│   ├── workflows/
│   │   ├── analyze_ticket.py
│   │   ├── update_ticket.py
│   │   └── send_notification.py
│   └── scheduled/
│       └── generate_reports.py
├── step_functions/
│   └── ticket_workflow.asl.json
├── infrastructure/
│   ├── dynamodb/
│   │   └── table_schema.json
│   ├── api_gateway/
│   │   └── openapi.yaml
│   └── cloudformation/
│       └── template.yaml
├── shared/
│   ├── __init__.py
│   ├── dynamodb_client.py
│   ├── auth_utils.py
│   └── response_utils.py
├── config/
│   └── settings.py
├── requirements.txt
└── README.md
```

## Deployment Requirements

1. **AWS Student Account** with LabRole permissions
2. **API Keys**:
   - GROQ_API_KEY - For AI ticket analysis
   - SENDGRID_API_KEY - For email notifications
3. **AWS Services Used**:
   - API Gateway (REST API)
   - Lambda (Python 3.11)
   - DynamoDB (On-demand)
   - Step Functions
   - EventBridge (Scheduler)

## Environment Variables

Set these in Lambda environment variables or AWS Secrets Manager:

```bash
GROQ_API_KEY=your_groq_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
DYNAMODB_TABLE_TICKETS=tickets
DYNAMODB_TABLE_USERS=users
JWT_SECRET=your_jwt_secret
SENDGRID_SENDER_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
```

## Quick Start

1. Deploy DynamoDB tables
2. Create IAM roles for Lambda execution
3. Deploy Lambda functions
4. Configure API Gateway with Lambda integrations
5. Deploy Step Functions state machine
6. Set up EventBridge scheduled rules
