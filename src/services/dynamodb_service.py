import os
import boto3
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DynamoDBService:
    """Service for managing receipt data in DynamoDB."""

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE', 'Receipts')
        self.table = self.dynamodb.Table(self.table_name)

    def store_receipt(self, receipt_data):
        """
        Store extracted receipt data in DynamoDB.
        
        Args:
            receipt_data: Dictionary containing receipt information
            
        Raises:
            Exception: If storage operation fails
        """
        try:
            items_for_db = self._format_items_for_storage(receipt_data['items'])

            db_item = {
                'receipt_id': receipt_data['receipt_id'],
                'date': receipt_data['date'],
                'vendor': receipt_data['vendor'],
                'total': receipt_data['total'],
                'items': items_for_db,
                's3_path': receipt_data['s3_path'],
                'processed_timestamp': datetime.now().isoformat()
            }

            self.table.put_item(Item=db_item)
            logger.info(f"Receipt data stored in DynamoDB: {receipt_data['receipt_id']}")

        except Exception as e:
            logger.error(f"Error storing data in DynamoDB: {str(e)}")
            raise

    def _format_items_for_storage(self, items):
        """
        Format items for DynamoDB storage.
        
        Args:
            items: List of item dictionaries
            
        Returns:
            list: Formatted items for database storage
        """
        formatted_items = []
        for item in items:
            formatted_items.append({
                'name': item.get('name', 'Unknown Item'),
                'price': item.get('price', '0.00'),
                'quantity': item.get('quantity', '1')
            })
        return formatted_items

    def get_receipt(self, receipt_id):
        """
        Retrieve a receipt by ID.
        
        Args:
            receipt_id: Unique receipt identifier
            
        Returns:
            dict: Receipt data or None if not found
        """
        try:
            response = self.table.get_item(Key={'receipt_id': receipt_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error retrieving receipt {receipt_id}: {str(e)}")
            raise

    def query_receipts_by_date(self, start_date, end_date):
        """
        Query receipts within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            list: List of receipt records
        """
        try:
            # Note: This assumes you have a GSI on the date field
            # Implementation depends on your actual table structure
            logger.info(f"Querying receipts from {start_date} to {end_date}")
            # Add actual query implementation here
            pass
        except Exception as e:
            logger.error(f"Error querying receipts: {str(e)}")
            raise
