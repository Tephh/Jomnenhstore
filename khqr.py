import qrcode
import requests
import json
import logging
import os
from config import KHQR_MERCHANT_ID, KHQR_API_KEY, KHQR_BASE_URL

logger = logging.getLogger(__name__)

class KHQRPayment:
    def __init__(self):
        self.merchant_id = KHQR_MERCHANT_ID
        self.api_key = KHQR_API_KEY
        self.base_url = KHQR_BASE_URL
        logger.info("KHQR Payment initialized")
    
    def generate_payment_qr(self, amount, order_id, currency="USD"):
        """
        Generate KHQR payment QR code
        Note: This is a simplified implementation. 
        You'll need to integrate with actual KHQR API from your bank.
        """
        try:
            # KHQR payload structure (simplified)
            khqr_data = {
                "merchant_id": self.merchant_id,
                "amount": f"{amount:.2f}",
                "currency": currency,
                "order_id": str(order_id),
                "description": f"Order #{order_id}",
                "terminal_id": "001",
                "country_code": "KH",
                "city": "Phnom Penh"
            }
            
            # Convert to KHQR string format
            qr_string = self._format_khqr_string(khqr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            qr_filename = f"khqr_{order_id}.png"
            img.save(qr_filename)
            
            logger.info(f"KHQR generated for order {order_id}")
            return qr_filename, qr_string
            
        except Exception as e:
            logger.error(f"Error generating KHQR: {e}")
            return None, None
    
    def _format_khqr_string(self, data):
        """Format data into KHQR standard string"""
        # This is a simplified version. Actual KHQR format is more complex.
        # Format: KHQR|MerchantID|Amount|Currency|OrderID|Description
        return f"KHQR|{data['merchant_id']}|{data['amount']}|{data['currency']}|{data['order_id']}|{data['description']}"
    
    def verify_payment(self, transaction_id):
        """
        Verify payment status with KHQR API
        You need to implement this based on your bank's API documentation
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # This is a placeholder - replace with actual API endpoint
            response = requests.get(
                f"{self.base_url}/transactions/{transaction_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Payment verification successful for {transaction_id}")
                return result
            else:
                logger.error(f"Payment verification failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return None

# For testing without real KHQR integration
class MockKHQRPayment:
    def __init__(self):
        logger.info("Mock KHQR Payment initialized (for testing)")
    
    def generate_payment_qr(self, amount, order_id, currency="USD"):
        """Mock KHQR implementation for testing"""
        try:
            qr_data = f"MOCK_KHQR|ORDER_{order_id}|AMOUNT_{amount}|{currency}|TIMESTAMP_{os.urandom(4).hex()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            qr_filename = f"khqr_{order_id}.png"
            img.save(qr_filename)
            
            logger.info(f"Mock KHQR generated for order {order_id}")
            return qr_filename, qr_data
            
        except Exception as e:
            logger.error(f"Error generating mock KHQR: {e}")
            return None, None
    
    def verify_payment(self, transaction_id):
        """Mock payment verification - always returns success for testing"""
        logger.info(f"Mock payment verification for {transaction_id}")
        return {"status": "success", "transaction_id": transaction_id, "amount": "15.99", "currency": "USD"}