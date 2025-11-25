#!/bin/bash
# LEH AI Worker Deployment Script
# Usage: ./scripts/deploy.sh [dev|staging|prod]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-dev}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  LEH AI Worker Deployment${NC}"
echo -e "${GREEN}  Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment. Use: dev, staging, or prod${NC}"
    exit 1
fi

# Check prerequisites
echo -e "\n${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not installed${NC}"
    echo "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo -e "${RED}Error: SAM CLI not installed${NC}"
    echo "Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "ap-northeast-2")
echo -e "${GREEN}✓ AWS Account: ${AWS_ACCOUNT}${NC}"
echo -e "${GREEN}✓ AWS Region: ${AWS_REGION}${NC}"

# Check OpenAI API Key
echo -e "\n${YELLOW}[2/6] Checking environment variables...${NC}"

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable not set${NC}"
    echo "Set it with: export OPENAI_API_KEY=your-api-key"
    exit 1
fi
echo -e "${GREEN}✓ OPENAI_API_KEY is set${NC}"

# Run tests
echo -e "\n${YELLOW}[3/6] Running tests...${NC}"

if ! pytest --cov=src --cov-fail-under=80 -q; then
    echo -e "${RED}Error: Tests failed or coverage below 80%${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Tests passed with 80%+ coverage${NC}"

# Validate SAM template
echo -e "\n${YELLOW}[4/6] Validating SAM template...${NC}"

if ! sam validate --lint; then
    echo -e "${RED}Error: SAM template validation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SAM template is valid${NC}"

# Build the application
echo -e "\n${YELLOW}[5/6] Building application...${NC}"

sam build --use-container

echo -e "${GREEN}✓ Build successful${NC}"

# Deploy
echo -e "\n${YELLOW}[6/6] Deploying to ${ENVIRONMENT}...${NC}"

if [ "$ENVIRONMENT" = "prod" ]; then
    echo -e "${RED}WARNING: Deploying to PRODUCTION!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 0
    fi
fi

sam deploy \
    --config-env "$ENVIRONMENT" \
    --parameter-overrides "Environment=$ENVIRONMENT OpenAIApiKey=$OPENAI_API_KEY"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Get stack outputs
echo -e "\n${YELLOW}Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name "leh-ai-worker-${ENVIRONMENT}" \
    --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
    --output table

echo -e "\n${GREEN}Done!${NC}"
