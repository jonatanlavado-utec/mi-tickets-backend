# Ticket Management System - Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Components](#components)
4. [Data Flow](#data-flow)
5. [API Reference](#api-reference)
6. [Security](#security)
7. [Scaling & Performance](#scaling--performance)
8. [Cost Considerations](#cost-considerations)
9. [Deployment Guide](#deployment-guide)
10. [Monitoring & Logging](#monitoring--logging)

---

## Overview

This serverless backend provides a ticket management system with AI-powered analysis. Key features:
- User authentication (register/login with JWT)
- Ticket CRUD operations
- AI-powered ticket analysis via Groq API
- Risk assessment and sensitive data detection
- Email notifications via SendGrid for high-risk tickets
- Scheduled reports (weekly/monthly)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   AWS CLOUD                                     │
│                                                                                 │
│  ┌─────────────────┐                                                            │
│  │   Client App   │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐      ┌────────────────────────────────────────────────┐    │
│  │  API Gateway    │      │                Lambda Functions               │    │
│  │   (REST API)    │      │                                                │    │
│  │                 │      │  ┌─────────────────┐  ┌─────────────────┐    │    │
│  │  /auth/register ├─────▶│  │ auth-register   │  │ auth-login      │    │    │
│  │  /auth/login    ├─────▶│  └─────────────────┘  └─────────────────┘    │    │
│  │                 │      │                                                │    │
│  │  /tickets       ├─────▶│  ┌─────────────────┐  ┌─────────────────┐    │    │
│  │  /tickets/{id}  ├─────▶│  │ tickets-create  │  │ tickets-get     │    │    │
│  │                 │      │  │ tickets-list    │  └─────────────────┘    │    │
│  │                 │      │  └─────────────────┘                          │    │
│  └─────────────────┘      │                │                               │    │
│                           │                │                               │    │
│                           │                ▼                               │    │
│                           │  ┌─────────────────────────────────────────┐ │    │
│                           │  │           Step Functions                │ │    │
│                           │  │          (Ticket Workflow)              │ │    │
│                           │  │                                          │ │    │
│                           │  │  ┌──────────┐   ┌──────────┐           │ │    │
│                           │  │  │ Analyze  │──▶│ Update   │──▶┌─────┐ │ │    │
│                           │  │  │ (Groq)   │   │ DynamoDB │   │Notify│ │ │    │
│                           │  │  └──────────┘   └──────────┘   │(Email│ │ │    │
│                           │  │         │                      │Send) │ │ │    │
│                           │  │         ▼                      └─────┘ │ │    │
│                           │  │  ┌──────────────┐               │      │ │    │
│                           │  │  │   Groq API   │               │      │ │    │
│                           │  │  │  (External)  │               │      │ │    │
│                           │  │  └──────────────┘               │      │ │    │
│                           │  │         │                       │      │ │    │
│                           │  │         ▼                       ▼      │ │    │
│                           │  └─────────────────────────────────────────┘ │    │
│                           │                                                │    │
│  ┌─────────────────┐      │                                                │    │
│  │  EventBridge    │      │  ┌─────────────────────────────────────────┐ │    │
│  │   (Scheduler)   ├─────▶│  │          Lambda Functions               │ │    │
│  │                 │      │  │                                        │ │    │
│  │  Weekly Reports │      │  │  ┌───────────────────────────────────┐ │ │    │
│  │  Monthly Reports├─────▶│  │  │  generate-reports (Scheduled)     │ │ │    │
│  └─────────────────┘      │  │  └───────────────────────────────────┘ │ │    │
│                           │  │                                        │ │    │
│                           │  │         │                              │ │    │
│                           │  │         ▼                              │ │    │
│                           │  │  ┌───────────────────────────────────┐ │ │    │
│                           │  │  │ SendGrid API (External)          │ │ │    │
│                           │  │  │ - Report Delivery                │ │ │    │
│                           │  │  └───────────────────────────────────┘ │ │    │
│                           │  └─────────────────────────────────────────┘ │    │
│                           └────────────────────────────────────────────────┘    │
│                                              │                                  │
│                                              ▼                                  │
│                           ┌────────────────────────────────────────────────┐    │
│                           │                   DynamoDB                      │    │
│                           │                                                  │    │
│                           │   ┌─────────────┐      ┌─────────────┐         │    │
│                           │   │   tickets   │      │    users    │         │    │
│                           │   │   table     │      │    table    │         │    │
│                           │   └─────────────┘      └─────────────┘         │    │
│                           │                                                  │    │
│                           │   GSI: user_id-created_at                       │    │
│                           │   GSI: status-created_at                        │    │
│                           │   GSI: email (users table)                      │    │
│                           │                                                  │    │
│                           └────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

External Services:
┌─────────────────┐      ┌─────────────────┐
│    Groq API     │      │   SendGrid      │
│  (AI Analysis)  │      │  (Email Sender) │
└─────────────────┘      └─────────────────┘
```

---

## Components

### 1. API Gateway
- **Type**: REST API
- **Authentication**: JWT Bearer tokens for protected endpoints
- **Endpoints**:
  - `POST /auth/register` - Public
  - `POST /auth/login` - Public
  - `POST /tickets` - Protected
  - `GET /tickets` - Protected
  - `GET /tickets/{id}` - Protected

### 2. Lambda Functions

| Function | Purpose | Trigger |
|----------|---------|---------|
| `auth-register` | User registration | API Gateway |
| `auth-login` | User authentication | API Gateway |
| `tickets-create` | Create ticket, trigger workflow | API Gateway |
| `tickets-get` | Get single ticket | API Gateway |
| `tickets-list` | List user tickets | API Gateway |
| `workflow-analyze` | AI analysis via Groq | Step Functions |
| `workflow-update` | Update ticket with results | Step Functions |
| `workflow-notify` | Send email notification | Step Functions |
| `scheduled-reports` | Generate reports | EventBridge |

### 3. DynamoDB Tables

#### Tickets Table
```json
{
  "id": "UUID",
  "user_id": "UUID",
  "description": "String",
  "user_priority": "low|medium|high|critical",
  "ai_priority": "low|medium|high|critical",
  "category": "technical|billing|security|general|feature_request|bug|account",
  "risk_level": "none|low|medium|high|critical",
  "sensitive_data_detected": "Boolean",
  "sensitive_data_types": ["Array"],
  "status": "pending_analysis|analyzed|in_progress|resolved|closed",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

#### Users Table
```json
{
  "id": "UUID",
  "email": "String (indexed)",
  "password_hash": "String (salted SHA-256)",
  "name": "String",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### 4. Step Functions Workflow

```
┌───────────────────────────────────────────────────────────────────┐
│                     Ticket Analysis Workflow                       │
│                                                                    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐  │
│  │              │     │              │     │                  │  │
│  │ AnalyzeTicket├────▶│ UpdateTicket ├────▶│Needs Notification│  │
│  │              │     │              │     │                  │  │
│  └──────────────┘     └──────────────┘     └────────┬─────────┘  │
│         │                                           │            │
│         │                                           ▼            │
│         │                                    ┌─────────────┐      │
│         │                                    │Yes: SendEmail│    │
│         │                                    └─────────────┘      │
│         │                                           │            │
│         │                                           ▼            │
│         │                                    ┌─────────────┐      │
│         │                                    │ WorkflowDone│      │
│         │                                    └─────────────┘      │
│         │                                                           │
│         │  [Error]                                                  │
│         │     │                                                     │
│         ▼     ▼                                                     │
│  ┌────────────────┐                                                │
│  │ HandleError    │                                                │
│  │ (Default values)│                                               │
│  └────────────────┘                                                │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### 5. EventBridge Scheduler

| Rule | Schedule | Purpose |
|------|----------|---------|
| Weekly Report | `cron(0 9 ? * MON *)` | Generate weekly ticket summary |
| Monthly Report | `cron(0 9 1 * ? *)` | Generate monthly ticket summary |

---

## Data Flow

### Ticket Creation Flow

```
1. Client → POST /tickets (with JWT)
   │
   ▼
2. API Gateway validates JWT
   │
   ▼
3. CreateTicket Lambda:
   - Validates input
   - Creates ticket in DynamoDB (status: pending_analysis)
   - Starts Step Functions execution
   - Returns ticket ID to client
   │
   ▼
4. Step Functions Workflow:
   │
   ├──▶ AnalyzeTicket Lambda:
   │    - Calls Groq API with ticket description
   │    - Extracts: category, priority, risk_level, sensitive_data
   │    - Returns analysis results
   │
   ├──▶ UpdateTicket Lambda:
   │    - Updates DynamoDB with analysis results
   │    - Determines if notification needed
   │    - Returns ticket + notification flag
   │
   └──▶ SendNotification Lambda (if needed):
        - Generates HTML email
        - Sends via SendGrid API
        - Returns status
   │
   ▼
5. Ticket status updated to 'analyzed'
```

---

## API Reference

### Authentication Endpoints

#### POST /auth/register
```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "name": "John Doe"
}

// Response (201)
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2024-01-15T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### POST /auth/login
```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

// Response (200)
{
  "success": true,
  "data": {
    "user": { ... },
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

### Ticket Endpoints

#### POST /tickets
```json
// Request (Header: Authorization: Bearer <token>)
{
  "description": "I cannot access my account after the update...",
  "user_priority": "high"  // optional, default: "medium"
}

// Response (201)
{
  "success": true,
  "data": {
    "ticket": {
      "id": "uuid",
      "user_id": "user-uuid",
      "description": "...",
      "user_priority": "high",
      "status": "pending_analysis",
      "created_at": "2024-01-15T10:00:00Z"
    },
    "message": "Ticket created. AI analysis in progress."
  }
}
```

#### GET /tickets
```json
// Request (Header: Authorization: Bearer <token>)
// Query params: limit=20, status=analyzed, last_key=...

// Response (200)
{
  "success": true,
  "data": {
    "tickets": [
      {
        "id": "uuid",
        "description": "...",
        "user_priority": "high",
        "ai_priority": "critical",
        "category": "security",
        "risk_level": "high",
        "status": "analyzed",
        "created_at": "..."
      }
    ],
    "count": 1,
    "pagination": {
      "last_key": "...",
      "has_more": false
    }
  }
}
```

#### GET /tickets/{id}
```json
// Request (Header: Authorization: Bearer <token>)

// Response (200)
{
  "success": true,
  "data": {
    "ticket": {
      "id": "uuid",
      "user_id": "user-uuid",
      "description": "...",
      "user_priority": "high",
      "ai_priority": "critical",
      "category": "security",
      "risk_level": "high",
      "sensitive_data_detected": true,
      "sensitive_data_types": ["credentials"],
      "status": "analyzed",
      "created_at": "...",
      "updated_at": "..."
    }
  }
}
```

---

## Security

### Authentication
- JWT tokens with configurable expiration (default: 24 hours)
- Tokens signed with HS256 algorithm
- Password hashing with salt (SHA-256)

### Authorization
- User can only access their own tickets
- JWT validation on protected endpoints
- Owner verification on ticket access

### Data Protection
- DynamoDB encryption at rest (SSE enabled)
- Point-in-time recovery enabled
- API keys stored in environment variables (recommend: AWS Secrets Manager)
- Sensitive data detection in ticket descriptions

### Best Practices
1. Use HTTPS in production
2. Rotate JWT secret regularly
3. Use AWS Secrets Manager for production API keys
4. Enable CloudTrail for audit logging
5. Implement rate limiting on API Gateway

---

## Scaling & Performance

### Lambda Concurrency
- Default: Unreserved concurrency
- Consider setting reserved concurrency for production
- Memory: 128MB - 512MB (adjust per function)

### DynamoDB
- On-demand billing mode (PAY_PER_REQUEST)
- Global Secondary Indexes for efficient queries
- Consider switching to provisioned capacity for predictable workloads

### Step Functions
- Concurrent execution limit: Default 1000
- Retry strategy: 3 attempts with exponential backoff
- Timeout: 60 seconds for analysis

### Expected Latency
| Operation | Expected Latency |
|-----------|-----------------|
| Register/Login | ~200-500ms |
| Create Ticket | ~300-600ms (async analysis) |
| List Tickets | ~100-200ms |
| Get Ticket | ~50-100ms |
| Analysis Workflow | ~5-15s (Groq API dependent) |

---

## Cost Considerations

### AWS Free Tier (Student Account)

| Service | Free Tier | Estimated Monthly Cost |
|---------|-----------|----------------------|
| API Gateway | 1M requests | $0 (within limits) |
| Lambda | 1M requests + 400k GB-seconds | $0 (within limits) |
| DynamoDB | 25GB storage, 25 WCUs/RCUs | $0 (within limits) |
| Step Functions | 4,000 state transitions | $0 (within limits) |
| EventBridge | 14M custom events | $0 (within limits) |

### External Services
- **Groq API**: Free tier available (rate limits apply)
- **SendGrid**: Free tier: 100 emails/day

### Estimated Costs (Low Traffic)
- **Free tier eligible**: $0-5/month
- **Production**: $10-50/month (depending on traffic)

---

## Deployment Guide

### Prerequisites
1. AWS CLI configured
2. Python 3.11+
3. Groq API key
4. SendGrid API key

### Environment Variables
```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=dev
export GROQ_API_KEY=your_groq_key
export SENDGRID_API_KEY=your_sendgrid_key
export JWT_SECRET=your_random_secret
export ADMIN_EMAIL=admin@yourdomain.com
export SENDER_EMAIL=noreply@yourdomain.com
```

### Deploy Steps
```bash
# 1. Clone repository
git clone <repo-url>
cd ticket-ya-backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create S3 bucket for Lambda code
aws s3 mb s3://ticket-lambda-deployments-$ENVIRONMENT

# 4. Deploy CloudFormation stack
./scripts/deploy.sh

# 5. Update Lambda code
aws lambda update-function-code ...

# 6. Test endpoints
./scripts/test_local.py
```

---

## Monitoring & Logging

### CloudWatch Logs
All Lambda functions output structured JSON logs:
```json
{
  "timestamp": "2024-01-15T10:00:00Z",
  "level": "INFO",
  "function": "tickets-create",
  "request_id": "uuid",
  "user_id": "user-uuid",
  "message": "Ticket created successfully"
}
```

### CloudWatch Alarms (Recommended)
- Lambda errors > 1% in 5 minutes
- DynamoDB throttling events
- API Gateway 5XX errors
- Step Functions execution failures

### X-Ray Tracing
Enable for:
- Request tracing through all components
- Latency analysis
- Error identification

### Metrics to Monitor
- API Gateway: Request count, latency, 4XX/5XX errors
- Lambda: Invocations, duration, errors, throttles
- DynamoDB: Consumed RCU/WCU, throttling
- Step Functions: Executions started/completed/failed