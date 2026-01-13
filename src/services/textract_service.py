import boto3
import uuid
import json
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TextractService:
    """Service for processing receipts using AWS Textract."""

    def __init__(self):
        self.textract_client = boto3.client('textract')

    def process_receipt(self, bucket, key):
        """
        Process receipt using Textract's AnalyzeExpense operation.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            dict: Extracted receipt data
        """
        try:
            logger.info(f"Calling Textract analyze_expense for {bucket}/{key}")
            response = self.textract_client.analyze_expense(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            logger.info("Textract analyze_expense call successful")
        except Exception as e:
            logger.error(f"Textract analyze_expense call failed: {str(e)}")
            raise

        receipt_data = self._extract_receipt_data(response, bucket, key)
        logger.info(f"Extracted receipt data: {json.dumps(receipt_data)}")
        
        return receipt_data

    def _extract_receipt_data(self, textract_response, bucket, key):
        """
        Extract structured data from Textract response.
        
        Args:
            textract_response: Raw response from Textract
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            dict: Structured receipt data
        """
        receipt_id = str(uuid.uuid4())

        receipt_data = {
            'receipt_id': receipt_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'vendor': 'Unknown',
            'total': '0.00',
            'items': [],
            's3_path': f"s3://{bucket}/{key}"
        }

        if 'ExpenseDocuments' not in textract_response or not textract_response['ExpenseDocuments']:
            logger.warning("No expense documents found in Textract response")
            return receipt_data

        expense_doc = textract_response['ExpenseDocuments'][0]

        # Extract summary fields
        self._extract_summary_fields(expense_doc, receipt_data)

        # Extract line items
        self._extract_line_items(expense_doc, receipt_data)

        return receipt_data

    def _extract_summary_fields(self, expense_doc, receipt_data):
        """Extract summary fields like TOTAL, DATE, and VENDOR."""
        if 'SummaryFields' not in expense_doc:
            return

        for field in expense_doc['SummaryFields']:
            field_type = field.get('Type', {}).get('Text', '')
            value = field.get('ValueDetection', {}).get('Text', '')

            if field_type == 'TOTAL':
                receipt_data['total'] = value
            elif field_type == 'INVOICE_RECEIPT_DATE':
                receipt_data['date'] = value
            elif field_type == 'VENDOR_NAME':
                receipt_data['vendor'] = value

    def _extract_line_items(self, expense_doc, receipt_data):
        """Extract line items from the receipt."""
        if 'LineItemGroups' not in expense_doc:
            return

        for group in expense_doc['LineItemGroups']:
            if 'LineItems' not in group:
                continue

            for line_item in group['LineItems']:
                item = {}
                
                for field in line_item.get('LineItemExpenseFields', []):
                    field_type = field.get('Type', {}).get('Text', '')
                    value = field.get('ValueDetection', {}).get('Text', '')

                    if field_type == 'ITEM':
                        item['name'] = value
                    elif field_type == 'PRICE':
                        item['price'] = value
                    elif field_type == 'QUANTITY':
                        item['quantity'] = value

                # Only add items with a name
                if 'name' in item:
                    receipt_data['items'].append(item)
