import pytest
from unittest.mock import Mock, patch
from src.services.textract_service import TextractService


class TestTextractService:
    """Unit tests for TextractService."""

    @pytest.fixture
    def textract_service(self):
        """Create a TextractService instance for testing."""
        return TextractService()

    @pytest.fixture
    def mock_textract_response(self):
        """Mock Textract API response."""
        return {
            'ExpenseDocuments': [{
                'SummaryFields': [
                    {
                        'Type': {'Text': 'TOTAL'},
                        'ValueDetection': {'Text': '125.50'}
                    },
                    {
                        'Type': {'Text': 'VENDOR_NAME'},
                        'ValueDetection': {'Text': 'Test Store'}
                    },
                    {
                        'Type': {'Text': 'INVOICE_RECEIPT_DATE'},
                        'ValueDetection': {'Text': '2024-01-15'}
                    }
                ],
                'LineItemGroups': [{
                    'LineItems': [
                        {
                            'LineItemExpenseFields': [
                                {
                                    'Type': {'Text': 'ITEM'},
                                    'ValueDetection': {'Text': 'Product A'}
                                },
                                {
                                    'Type': {'Text': 'PRICE'},
                                    'ValueDetection': {'Text': '50.00'}
                                },
                                {
                                    'Type': {'Text': 'QUANTITY'},
                                    'ValueDetection': {'Text': '2'}
                                }
                            ]
                        }
                    ]
                }]
            }]
        }

    @patch('boto3.client')
    def test_process_receipt_success(self, mock_boto_client, textract_service, mock_textract_response):
        """Test successful receipt processing."""
        # Setup
        mock_client = Mock()
        mock_client.analyze_expense.return_value = mock_textract_response
        mock_boto_client.return_value = mock_client
        textract_service.textract_client = mock_client

        # Execute
        result = textract_service.process_receipt('test-bucket', 'test-key.jpg')

        # Assert
        assert result['vendor'] == 'Test Store'
        assert result['total'] == '125.50'
        assert result['date'] == '2024-01-15'
        assert len(result['items']) == 1
        assert result['items'][0]['name'] == 'Product A'
        assert result['s3_path'] == 's3://test-bucket/test-key.jpg'
        assert 'receipt_id' in result

    @patch('boto3.client')
    def test_process_receipt_textract_failure(self, mock_boto_client, textract_service):
        """Test handling of Textract API failure."""
        # Setup
        mock_client = Mock()
        mock_client.analyze_expense.side_effect = Exception('Textract API Error')
        mock_boto_client.return_value = mock_client
        textract_service.textract_client = mock_client

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            textract_service.process_receipt('test-bucket', 'test-key.jpg')
        
        assert 'Textract API Error' in str(exc_info.value)
