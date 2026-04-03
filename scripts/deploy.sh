#!/bin/bash

# ================================================================
# Deployment Script for Ticket Management System
# ================================================================

set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
BUCKET_NAME="${S3_BUCKET:-ticket-lambda-deployments-${ENVIRONMENT}}"
STACK_NAME="ticket-system-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Ticket Management System Deployment${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Region: ${YELLOW}${REGION}${NC}"
echo -e "Stack Name: ${YELLOW}${STACK_NAME}${NC}"
echo ""

# ================================================================
# Step 1: Create S3 Bucket (if not exists)
# ================================================================
echo -e "${YELLOW}[1/6] Checking S3 bucket...${NC}"
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket: ${BUCKET_NAME}"
    aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"
else
    echo "S3 bucket already exists"
fi

# ================================================================
# Step 2: Package Lambda Functions
# ================================================================
echo -e "${YELLOW}[2/6] Packaging Lambda functions...${NC}"

LAMBDA_DIRS=(
    "lambdas/auth/register"
    "lambdas/auth/login"
    "lambdas/tickets/create_ticket"
    "lambdas/tickets/get_ticket"
    "lambdas/tickets/list_tickets"
    "lambdas/workflows/analyze_ticket"
    "lambdas/workflows/update_ticket"
    "lambdas/workflows/send_notification"
    "lambdas/scheduled/generate_reports"
)

for dir in "${LAMBDA_DIRS[@]}"; do
    function_name=$(basename "$dir")
    echo "Packaging: ${function_name}"

    # Create temp directory
    temp_dir=$(mktemp -d)

    # Copy Lambda function code
    cp "${dir}.py" "${temp_dir}/" 2>/dev/null || true

    # Copy shared modules
    cp -r shared "${temp_dir}/"
    cp -r config "${temp_dir}/"

    # Create zip file
    (cd "${temp_dir}" && zip -r "${function_name}.zip" .)

    # Upload to S3
    aws s3 cp "${temp_dir}/${function_name}.zip" "s3://${BUCKET_NAME}/${function_name}.zip"

    # Cleanup
    rm -rf "${temp_dir}"
done

echo -e "${GREEN}Lambda functions packaged${NC}"

# ================================================================
# Step 3: Deploy CloudFormation Stack
# ================================================================
echo -e "${YELLOW}[3/6] Deploying CloudFormation stack...${NC}"

# Check if stack exists
if aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${REGION}" 2>&1 | grep -q 'does not exist'; then
    CREATE_UPDATE="create-stack"
else
    CREATE_UPDATE="update-stack"
fi

aws cloudformation ${CREATE_UPDATE} \
    --stack-name "${STACK_NAME}" \
    --template-body file://infrastructure/cloudformation/template.yaml \
    --parameters \
        ParameterKey=Environment,ParameterValue="${ENVIRONMENT}" \
        ParameterKey=GroqApiKey,ParameterValue="${GROQ_API_KEY:-placeholder}" \
        ParameterKey=SendGridApiKey,ParameterValue="${SENDGRID_API_KEY:-placeholder}" \
        ParameterKey=JwtSecret,ParameterValue="${JWT_SECRET:-change-me-in-production}" \
        ParameterKey=AdminEmail,ParameterValue="${ADMIN_EMAIL:-admin@example.com}" \
        ParameterKey=SenderEmail,ParameterValue="${SENDER_EMAIL:-noreply@example.com}" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "${REGION}"

# ================================================================
# Step 4: Wait for Stack Completion
# ================================================================
echo -e "${YELLOW}[4/6] Waiting for stack to complete...${NC}"
aws cloudformation wait stack-${CREATE_UPDATE%%-stack}-complete \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}"

# ================================================================
# Step 5: Get Stack Outputs
# ================================================================
echo -e "${YELLOW}[5/6] Getting stack outputs...${NC}"

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

echo -e "${GREEN}API Endpoint: ${API_ENDPOINT}${NC}"

# ================================================================
# Step 6: Update Lambda Code
# ================================================================
echo -e "${YELLOW}[6/6] Updating Lambda code...${NC}"

for dir in "${LAMBDA_DIRS[@]}"; do
    function_name=$(basename "$dir")
    lambda_name=$(echo "${function_name}" | sed 's/_/-/g')

    aws lambda update-function-code \
        --function-name "${lambda_name}-${ENVIRONMENT}" \
        --s3-bucket "${BUCKET_NAME}" \
        --s3-key "${function_name}.zip" \
        --region "${REGION}" || true
done

# ================================================================
# Deployment Complete
# ================================================================
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "API Endpoint: ${YELLOW}${API_ENDPOINT}${NC}"
echo ""
echo -e "Test endpoints:"
echo -e "  Register: POST ${API_ENDPOINT}/auth/register"
echo -e "  Login:    POST ${API_ENDPOINT}/auth/login"
echo -e "  Tickets:  POST/GET ${API_ENDPOINT}/tickets"
echo -e "  Ticket:   GET ${API_ENDPOINT}/tickets/{id}"
echo ""
echo -e "${YELLOW}Note: Set environment variables for API keys:${NC}"
echo -e "  export GROQ_API_KEY=your_key"
echo -e "  export SENDGRID_API_KEY=your_key"
echo -e "  export JWT_SECRET=your_secret"
echo ""