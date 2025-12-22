"""
Enhanced QR Code Processing for Lambda Environment

This module provides lightweight QR code processing that works within AWS Lambda constraints.
For advanced PDF OCR processing, consider using container deployment or ECS.
"""

import io
import base64
import logging
from typing import Tuple, List, Optional, Dict
from PIL import Image, ImageEnhance, ImageFilter
import qrcode
try:
    from pyzbar.pyzbar import decode as decode_qr
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    def decode_qr(image):
        return []  # Return empty list if pyzbar not available

logger = logging.getLogger(__name__)

class QRProcessor:
    """Lightweight QR code processor for Lambda environment"""
    
    @staticmethod
    def enhance_image_for_qr(image: Image.Image) -> Image.Image:
        """
        Enhance image quality for better QR code detection
        """
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
        
        return image
    
    @staticmethod
    def extract_qr_from_image(image_data: bytes, filename: str = "") -> Dict:
        """
        Extract QR codes from image data
        
        Returns:
            Dict with 'success', 'qr_codes', 'enhanced_image_data', 'error'
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # First attempt - try original image
            qr_codes = decode_qr(image)
            
            if not qr_codes:
                # Second attempt - enhance image
                enhanced_image = QRProcessor.enhance_image_for_qr(image)
                qr_codes = decode_qr(enhanced_image)
                
                # Save enhanced image for return
                buffer = io.BytesIO()
                enhanced_image.save(buffer, format='PNG')
                enhanced_image_data = buffer.getvalue()
            else:
                enhanced_image_data = image_data
            
            # Extract QR code data
            qr_data = []
            for qr in qr_codes:
                qr_info = {
                    'data': qr.data.decode('utf-8'),
                    'type': qr.type,
                    'rect': qr.rect._asdict(),
                    'polygon': [point._asdict() for point in qr.polygon] if qr.polygon else []
                }
                qr_data.append(qr_info)
            
            return {
                'success': True,
                'qr_codes': qr_data,
                'enhanced_image_data': enhanced_image_data,
                'error': None,
                'count': len(qr_data)
            }
            
        except Exception as e:
            logger.error(f"QR extraction failed for {filename}: {str(e)}")
            return {
                'success': False,
                'qr_codes': [],
                'enhanced_image_data': None,
                'error': str(e),
                'count': 0
            }
    
    @staticmethod
    def generate_qr_code(data: str, size: int = 10, border: int = 4) -> bytes:
        """
        Generate QR code from data
        
        Returns:
            PNG image data as bytes
        """
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
    
    @staticmethod
    def process_pdf_lightweight(pdf_data: bytes, filename: str) -> Dict:
        """
        Lightweight PDF processing for QR extraction
        Note: This is basic extraction - for advanced OCR use container deployment
        """
        try:
            from PyPDF2 import PdfReader
            
            # Read PDF
            pdf = PdfReader(io.BytesIO(pdf_data))
            
            # Extract text from first page
            if len(pdf.pages) == 0:
                return {
                    'success': False,
                    'error': 'PDF has no pages',
                    'qr_codes': [],
                    'text_found': False
                }
            
            page = pdf.pages[0]
            text = page.extract_text()
            
            # Check for "For Customer" text
            has_customer_text = "for customer" in text.lower()
            
            # Extract account number from filename
            account_number = filename.rsplit('.', 1)[0].strip()
            
            return {
                'success': True,
                'error': None,
                'qr_codes': [],  # Cannot extract QR from PDF without image processing
                'text_found': has_customer_text,
                'account_number': account_number,
                'extracted_text': text[:500],  # First 500 chars for verification
                'note': 'PDF text extracted. For QR extraction from PDF, upload as image or use container deployment.'
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'PyPDF2 not available',
                'qr_codes': [],
                'text_found': False
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'qr_codes': [],
                'text_found': False
            }

class PaymentQRProcessor:
    """
    Specific processor for Thai payment QR codes
    Handles QR codes that contain bank transfer information
    """
    
    @staticmethod
    def parse_thai_payment_qr(qr_data: str) -> Dict:
        """
        Parse Thai payment QR code data
        
        Thai QR codes typically follow PromptPay format
        Returns parsed payment information
        """
        try:
            # Basic PromptPay QR parsing
            # This is a simplified version - full implementation would need EMVCo spec
            
            if not qr_data:
                return {'success': False, 'error': 'Empty QR data'}
            
            # Check if it's a payment QR (starts with specific indicators)
            payment_indicators = ['00020101', '0002010102']
            is_payment_qr = any(qr_data.startswith(indicator) for indicator in payment_indicators)
            
            if not is_payment_qr:
                return {
                    'success': True,
                    'type': 'other',
                    'raw_data': qr_data,
                    'is_payment': False
                }
            
            # Extract basic information
            parsed_data = {
                'success': True,
                'type': 'thai_payment',
                'is_payment': True,
                'raw_data': qr_data,
                'bank_code': None,
                'account_id': None,
                'amount': None,
                'currency': 'THB'
            }
            
            # Try to extract account/phone number (simplified parsing)
            # This would need full EMVCo implementation for production
            if '2937' in qr_data:  # PromptPay identifier
                # Extract the account identifier
                start_idx = qr_data.find('2937')
                if start_idx != -1:
                    # This is simplified - real parsing would follow EMVCo TLV format
                    parsed_data['account_type'] = 'promptpay'
            
            return parsed_data
            
        except Exception as e:
            return {
                'success': False,
                'error': f'QR parsing failed: {str(e)}',
                'raw_data': qr_data
            }