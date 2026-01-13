import os
import boto3

from ..utils.logger import get_logger

logger = get_logger(__name__)


class SESService:
    """Service for sending email notifications via AWS SES."""

    def __init__(self):
        self.ses_client = boto3.client('ses')
        self.sender_email = os.environ.get('SES_SENDER_EMAIL', 'your-email@example.com')
        self.recipient_email = os.environ.get('SES_RECIPIENT_EMAIL', 'recipient@example.com')

    def send_notification(self, receipt_data):
        """
        Send email notification with receipt details.
        
        Args:
            receipt_data: Dictionary containing receipt information
        """
        try:
            html_body = self._generate_email_body(receipt_data)

            self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [self.recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': f"Receipt Processed: {receipt_data['vendor']} - ${receipt_data['total']}"
                    },
                    'Body': {
                        'Html': {
                            'Data': html_body
                        }
                    }
                }
            )

            logger.info(f"Email notification sent to {self.recipient_email}")

        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            logger.info("Continuing execution despite email error")

    def _generate_email_body(self, receipt_data):
        """
        Generate HTML email body with receipt information.
        
        Args:
            receipt_data: Dictionary containing receipt information
            
        Returns:
            str: HTML formatted email body
        """
        items_html = self._format_items_html(receipt_data['items'])

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
                .detail {{ margin: 10px 0; }}
                .items-list {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Receipt Processing Notification</h2>
                </div>
                
                <div class="detail">
                    <p><strong>Receipt ID:</strong> {receipt_data['receipt_id']}</p>
                    <p><strong>Vendor:</strong> {receipt_data['vendor']}</p>
                    <p><strong>Date:</strong> {receipt_data['date']}</p>
                    <p><strong>Total Amount:</strong> ${receipt_data['total']}</p>
                    <p><strong>S3 Location:</strong> {receipt_data['s3_path']}</p>
                </div>

                <div class="items-list">
                    <h3>Items:</h3>
                    <ul>
                        {items_html}
                    </ul>
                </div>

                <p>The receipt has been successfully processed and stored in DynamoDB.</p>
            </div>
        </body>
        </html>
        """
        return html_body

    def _format_items_html(self, items):
        """
        Format items as HTML list items.
        
        Args:
            items: List of item dictionaries
            
        Returns:
            str: HTML formatted list items
        """
        if not items:
            return "<li>No items detected</li>"

        items_html = ""
        for item in items:
            name = item.get('name', 'Unknown Item')
            price = item.get('price', 'N/A')
            quantity = item.get('quantity', '1')
            items_html += f"<li>{name} - ${price} x {quantity}</li>"

        return items_html
