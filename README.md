# AWS Lambda Receipt Processor

A serverless application for automated receipt processing using AWS Lambda, Textract, DynamoDB, and SES. This solution automatically extracts key information from receipt images uploaded to S3, stores the data in DynamoDB, and sends email notifications.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Usage](#usage)

## Architecture

This application follows a serverless event-driven architecture:

1. Receipt images are uploaded to an S3 bucket
2. S3 trigger invokes the Lambda function
3. Lambda uses AWS Textract to extract receipt data
4. Extracted data is stored in DynamoDB
5. Email notification is sent via Amazon SES

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   S3 Bucket │──────>│ Lambda       │──────>│  Textract   │
│  (Receipts) │       │  Function    │       │   Service   │
└─────────────┘       └──────┬───────┘       └─────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼──────┐   ┌─────▼──────┐
              │  DynamoDB  │   │    SES     │
              │   Table    │   │  (Email)   │
              └────────────┘   └────────────┘
```

## Features

- Automated receipt data extraction using AWS Textract
- Extraction of vendor name, date, total amount, and line items
- Persistent storage in DynamoDB with indexing for queries
- Email notifications with receipt details
- Comprehensive error handling and logging
- Support for multiple image formats (JPG, PNG)
- Scalable serverless architecture
- Infrastructure as Code using CloudFormation
- Unit and integration testing

## Prerequisites

- Python 3.11 or higher
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Verified email addresses in Amazon SES (for development/testing)
- Git (for version control)

### Required AWS Permissions

The deployment requires permissions for:
- Lambda (create, update functions)
- S3 (create buckets, configure notifications)
- DynamoDB (create tables, GSI)
- IAM (create roles and policies)
- CloudFormation (create, update stacks)
- Textract (analyze expense API)
- SES (send email)
- CloudWatch Logs (create log groups)

## Project Structure

```
AWS-Lambda/
├── src/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── receipt_processor.py      # Main Lambda handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── textract_service.py       # Textract integration
│   │   ├── dynamodb_service.py       # DynamoDB operations
│   │   └── ses_service.py            # Email notifications
│   └── utils/
│       ├── __init__.py
│       └── logger.py                 # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   └── test_textract_service.py
│   └── integration/
│       └── __init__.py
├── infrastructure/
│   └── cloudformation/
│       └── lambda-function.yaml      # CloudFormation template
├── scripts/
│   ├── deploy.sh                     # Deployment script
│   └── run-tests.sh                  # Test execution script
├── .env.example                      # Environment variables template
├── .gitignore
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies
├── pytest.ini                        # Pytest configuration
├── Makefile                          # Build automation
└── README.md                         # This file
```

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AWS-Lambda
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Production dependencies
make install

# Development dependencies (for testing and development)
make install-dev
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```env
AWS_REGION=us-east-1
DYNAMODB_TABLE=Receipts
SES_SENDER_EMAIL=your-verified-sender@example.com
SES_RECIPIENT_EMAIL=recipient@example.com
LOG_LEVEL=INFO
```

## Configuration

### DynamoDB Table

The application uses a DynamoDB table with the following schema:

- **Primary Key**: `receipt_id` (String)
- **GSI**: `date-index` on `date` attribute
- **Attributes**:
  - `receipt_id`: Unique identifier (UUID)
  - `date`: Receipt date (YYYY-MM-DD)
  - `vendor`: Vendor name
  - `total`: Total amount
  - `items`: List of line items
  - `s3_path`: S3 location of original image
  - `processed_timestamp`: Processing timestamp

### SES Configuration

Before sending emails, you must verify email addresses in Amazon SES:

1. Go to Amazon SES Console
2. Verify both sender and recipient email addresses
3. If in sandbox mode, both must be verified

## Deployment

### Using Make (Recommended)

```bash
# Deploy to development environment
make deploy ENV=dev

# Deploy to production environment
make deploy ENV=prod
```

### Using Deployment Script

```bash
# Set environment variables
export SES_SENDER_EMAIL=your-email@example.com
export SES_RECIPIENT_EMAIL=recipient@example.com

# Run deployment script
bash scripts/deploy.sh dev
```

### Manual Deployment

```bash
# Create deployment package
make package

# Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file infrastructure/cloudformation/lambda-function.yaml \
    --stack-name receipt-processor-dev \
    --parameter-overrides \
        EnvironmentName=dev \
        SenderEmail=your-email@example.com \
        RecipientEmail=recipient@example.com \
    --capabilities CAPABILITY_NAMED_IAM

# Update Lambda function code
aws lambda update-function-code \
    --function-name receipt-processor-dev \
    --zip-file fileb://lambda-deployment.zip
```

## Usage

### Upload Receipt

Upload a receipt image to the S3 bucket:

```bash
# Get bucket name from CloudFormation outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name receipt-processor-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ReceiptBucketName`].OutputValue' \
    --output text)

# Upload receipt
aws s3 cp receipt.jpg s3://${BUCKET_NAME}/receipts/
```

### Query Receipts

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Receipts')

# Get receipt by ID
response = table.get_item(Key={'receipt_id': 'your-receipt-id'})
receipt = response.get('Item')

# Query by date (using GSI)
response = table.query(
    IndexName='date-index',
    KeyConditionExpression='#date = :date',
    ExpressionAttributeNames={'#date': 'date'},
    ExpressionAttributeValues={':date': '2024-01-15'}
)
receipts = response.get('Items', [])
```
