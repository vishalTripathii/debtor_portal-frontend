"""
Lambda-compatible QR Code Processing

This module provides QR code generation and basic processing that works within AWS Lambda constraints.
For QR code scanning from images, external services or container deployment is recommended.
"""

import io
import base64
import logging
from typing import Dict
from PIL import Image, ImageEnhance, ImageFilter
import qrcode

logger = logging.getLogger(__name__)

class LambdaQRProcessor:
    """QR code processor optimized for Lambda environment"""
    
    @staticmethod
    def generate_qr_code(data: str, size: int = 10, border: int = 4) -> bytes:
        """
        Generate QR code from data
        
        Returns:
            PNG image data as bytes
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"QR generation failed: {str(e)}")
            raise
    
    @staticmethod
    def enhance_image_quality(image_data: bytes) -> bytes:
        """
        Enhance image quality for better processing
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to grayscale for better contrast
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Image enhancement failed: {str(e)}")
            return image_data
    
    @staticmethod
    def process_image_for_qr_info(image_data: bytes, filename: str = "") -> Dict:
        """
        Process image and return enhanced version (QR scanning requires external service)
        
        Returns:
            Dict with image processing results and recommendations
        """
        try:
            # Load image for basic processing
            image = Image.open(io.BytesIO(image_data))
            
            # Get image info
            image_info = {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'size_bytes': len(image_data)
            }
            
            # Enhance image
            enhanced_data = LambdaQRProcessor.enhance_image_quality(image_data)
            
            return {
                'success': True,
                'filename': filename,
                'image_info': image_info,
                'enhanced_image_data': enhanced_data,
                'qr_scanning_note': 'QR code scanning requires external service or container deployment',
                'recommendations': {
                    'for_qr_scanning': 'Use Google Vision API, AWS Textract, or deploy with Docker container',
                    'image_enhanced': True,
                    'ready_for_external_processing': True
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': filename,
                'enhanced_image_data': None
            }

class PaymentQRGenerator:
    """
    Generate payment QR codes for Thai debt collection
    """
    
    @staticmethod
    def create_payment_qr(account_number: str, debtor_name: str, amount: float = None, 
                         case_id: str = None, bank_info: str = None) -> Dict:
        """
        Create payment QR code for debt collection
        
        Args:
            account_number: Debtor account number
            debtor_name: Name of debtor
            amount: Payment amount (optional)
            case_id: Case reference ID
            bank_info: Bank/payment information
        
        Returns:
            Dict with QR code data and image
        """
        try:
            # Prepare payment information
            payment_lines = [f"Account: {account_number}"]
            
            if debtor_name:
                payment_lines.append(f"Name: {debtor_name}")
            
            if amount:
                payment_lines.append(f"Amount: ฿{amount:,.2f}")
            
            if case_id:
                payment_lines.append(f"Ref: {case_id}")
            
            if bank_info:
                payment_lines.append(f"Pay to: {bank_info}")
            
            # Add instructions
            payment_lines.extend([
                "",
                "Please make payment and",
                "send proof to collection team"
            ])
            
            qr_text = "\n".join(payment_lines)
            
            # Generate QR code
            qr_image_data = LambdaQRProcessor.generate_qr_code(qr_text, size=8, border=2)
            qr_base64 = base64.b64encode(qr_image_data).decode('utf-8')
            
            return {
                'success': True,
                'qr_text': qr_text,
                'qr_image_base64': qr_base64,
                'qr_image_data': qr_image_data,
                'payment_info': {
                    'account_number': account_number,
                    'debtor_name': debtor_name,
                    'amount': amount,
                    'case_id': case_id,
                    'bank_info': bank_info
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'qr_text': None,
                'qr_image_base64': None
            }
    
    @staticmethod
    def create_info_qr(account_number: str, debtor_name: str, outstanding_balance: float,
                      contact_info: str = None) -> Dict:
        """
        Create information QR code for account details
        """
        try:
            info_lines = [
                "DEBT ACCOUNT INFO",
                f"Account: {account_number}",
                f"Name: {debtor_name}",
                f"Outstanding: ฿{outstanding_balance:,.2f}"
            ]
            
            if contact_info:
                info_lines.extend(["", f"Contact: {contact_info}"])
            
            qr_text = "\n".join(info_lines)
            qr_image_data = LambdaQRProcessor.generate_qr_code(qr_text, size=6, border=1)
            qr_base64 = base64.b64encode(qr_image_data).decode('utf-8')
            
            return {
                'success': True,
                'qr_text': qr_text,
                'qr_image_base64': qr_base64,
                'type': 'account_info'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'qr_text': None
            }