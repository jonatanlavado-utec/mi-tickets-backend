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

Create a `.env` file in the project root with the following variables:

```bash
# AWS Configuration
AWS_REGION=us-east-1
ENVIRONMENT=dev

# API Keys
GROQ_API_KEY=your_groq_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here

# Authentication
JWT_SECRET=your_random_secret_here
JWT_EXPIRATION_HOURS=24

# Email Configuration
ADMIN_EMAIL=admin@yourdomain.com
SENDER_EMAIL=noreply@yourdomain.com
SENDGRID_SENDER_EMAIL=noreply@yourdomain.com

# DynamoDB Tables
DYNAMODB_TABLE_TICKETS=tickets-dev
DYNAMODB_TABLE_USERS=users-dev
```

## Deployment

### Prerequisites

1. **AWS Student Account** with LabRole permissions
2. **API Keys** from Groq and SendGrid
3. **Python 3.11** and pip installed locally

### Steps

1. **Clone the repository and navigate to the backend directory:**
   ```bash
   git clone <repository-url>
   cd mi-tickets-backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` (if available) or create `.env` file
   - Fill in your actual API keys and configuration values

4. **Deploy to AWS:**
   ```bash
   bash scripts/deploy.sh
   ```

   The deployment script will:
   - Validate required environment variables
   - Package Lambda functions
   - Deploy CloudFormation stack
   - Update Lambda function code
   - Validate deployment

5. **Verify deployment:**
   - Check CloudFormation stack status in AWS Console
   - Test API endpoints using the provided API Gateway URL

### Environment Variable Validation

The deployment script automatically validates that all required environment variables are set before proceeding. If any are missing, it will display an error message and exit.

Required variables:
- `GROQ_API_KEY`
- `SENDGRID_API_KEY`
- `JWT_SECRET`
