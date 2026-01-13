import json
import os
import boto3
import uuid
from datetime import datetime
import urllib.parse

from ..services.textract_service import TextractService
from ..services.dynamodb_service import DynamoDBService
from ..services.ses_service import SESService
from ..utils.logger import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    AWS Lambda handler for processing receipt images uploaded to S3.
    
    Args:
        event: S3 event containing bucket and object information
        context: Lambda context object
        
    Returns:
        dict: Response with status code and message
    """
    try:
        # Extract S3 bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

        logger.info(f"Processing receipt from {bucket}/{key}")

        # Verify object exists
        _verify_s3_object(bucket, key)

        # Initialize services
        textract_service = TextractService()
        dynamodb_service = DynamoDBService()
        ses_service = SESService()

        # Step 1: Extract receipt data using Textract
        receipt_data = textract_service.process_receipt(bucket, key)

        # Step 2: Store in DynamoDB
        dynamodb_service.store_receipt(receipt_data)

        # Step 3: Send email notification
        ses_service.send_notification(receipt_data)

        logger.info(f"Successfully processed receipt: {receipt_data['receipt_id']}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Receipt processed successfully',
                'receipt_id': receipt_data['receipt_id']
            })
        }

    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _verify_s3_object(bucket, key):
    """
    Verify that the S3 object exists before processing.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Raises:
        Exception: If object cannot be accessed
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        logger.info(f"Object verification successful: {bucket}/{key}")
    except Exception as e:
        logger.error(f"Object verification failed: {str(e)}")
        raise Exception(f"Unable to access object {key} in bucket {bucket}: {str(e)}")
