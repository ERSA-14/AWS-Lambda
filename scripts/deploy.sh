#!/bin/bash

set -e

# Configuration
ENVIRONMENT=${1:-dev}
STACK_NAME="receipt-processor-${ENVIRONMENT}"
TEMPLATE_FILE="infrastructure/cloudformation/lambda-function.yaml"
PACKAGE_DIR="lambda-package"

echo "Deploying Receipt Processor Lambda to ${ENVIRONMENT} environment..."

# Create package directory
echo "Creating deployment package..."
rm -rf ${PACKAGE_DIR}
mkdir -p ${PACKAGE_DIR}

# Install dependencies
pip install -r requirements.txt -t ${PACKAGE_DIR}

# Copy source code
cp -r src ${PACKAGE_DIR}/

# Create deployment package
cd ${PACKAGE_DIR}
zip -r ../lambda-deployment.zip .
cd ..

# Upload to S3 (if using S3 for deployment)
# aws s3 cp lambda-deployment.zip s3://your-deployment-bucket/

echo "Validating CloudFormation template..."
aws cloudformation validate-template --template-body file://${TEMPLATE_FILE}

echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file ${TEMPLATE_FILE} \
    --stack-name ${STACK_NAME} \
    --parameter-overrides \
        EnvironmentName=${ENVIRONMENT} \
        SenderEmail=${SES_SENDER_EMAIL} \
        RecipientEmail=${SES_RECIPIENT_EMAIL} \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

echo "Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs'

# Update function code
FUNCTION_NAME="receipt-processor-${ENVIRONMENT}"
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name ${FUNCTION_NAME} \
    --zip-file fileb://lambda-deployment.zip

echo "Deployment complete!"
