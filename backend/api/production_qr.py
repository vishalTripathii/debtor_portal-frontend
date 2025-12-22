"""
Production-Ready QR Code and PDF Processing for AWS Lambda

This module provides robust, Lambda-optimized processing capabilities with:
- Perfect error handling and graceful degradation
- Memory-efficient image processing
- Comprehensive logging and monitoring
- Production-ready QR code generation
- PDF text extraction and analysis
"""

import io
import os
import gc
import base64
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import qrcode
from qrcode.image.pil import PilImage

# Configure logging
logger = logging.getLogger(__name__)

class RobustQRProcessor:
    """
    Production-ready QR code processor with comprehensive error handling
    """
    
    # QR Code generation settings
    DEFAULT_QR_SETTINGS = {
        'version': 1,
        'error_correction': qrcode.constants.ERROR_CORRECT_M,
        'box_size': 10,
        'border': 4,
        'fill_color': 'black',
        'back_color': 'white'
    }
    
    # Image processing limits for Lambda
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSION = 4096  # 4K max width/height
    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP'}
    
    @staticmethod
    def validate_image_input(image_data: bytes, filename: str = "") -> Dict[str, Any]:
        """
        Comprehensive image validation with detailed error reporting
        """
        try:
            if not image_data:
                return {'valid': False, 'error': 'Empty image data', 'details': None}
            
            # Size check
            size_mb = len(image_data) / (1024 * 1024)
            if len(image_data) > RobustQRProcessor.MAX_IMAGE_SIZE:
                return {
                    'valid': False, 
                    'error': f'Image too large: {size_mb:.1f}MB (max {RobustQRProcessor.MAX_IMAGE_SIZE/(1024*1024)}MB)',
                    'details': {'size_bytes': len(image_data), 'size_mb': size_mb}
                }
            
            # Try to load image
            image = Image.open(io.BytesIO(image_data))
            
            # Format check
            if image.format not in RobustQRProcessor.SUPPORTED_FORMATS:
                return {
                    'valid': False,
                    'error': f'Unsupported format: {image.format}',
                    'details': {'format': image.format, 'supported': list(RobustQRProcessor.SUPPORTED_FORMATS)}
                }
            
            # Dimension check
            if image.width > RobustQRProcessor.MAX_DIMENSION or image.height > RobustQRProcessor.MAX_DIMENSION:
                return {
                    'valid': False,
                    'error': f'Image too large: {image.width}x{image.height} (max {RobustQRProcessor.MAX_DIMENSION}x{RobustQRProcessor.MAX_DIMENSION})',
                    'details': {'width': image.width, 'height': image.height}
                }
            
            # Image info
            info = {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'size_bytes': len(image_data),
                'size_mb': round(size_mb, 2),
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            image.close()
            return {'valid': True, 'error': None, 'details': info}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Image validation failed: {str(e)}',
                'details': {'exception_type': type(e).__name__}
            }
    
    @staticmethod
    def enhance_image_for_processing(image_data: bytes, enhance_level: str = 'medium') -> bytes:
        """
        Advanced image enhancement with multiple quality levels
        
        Args:
            image_data: Raw image bytes
            enhance_level: 'light', 'medium', 'heavy'
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            original_mode = image.mode
            
            # Convert to RGB for processing
            if image.mode not in ('RGB', 'L'):
                if image.mode == 'RGBA':
                    # Handle transparency by adding white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Enhancement settings based on level
            enhancement_settings = {
                'light': {'contrast': 1.2, 'brightness': 1.0, 'sharpness': 1.1},
                'medium': {'contrast': 1.5, 'brightness': 1.1, 'sharpness': 1.3},
                'heavy': {'contrast': 2.0, 'brightness': 1.2, 'sharpness': 1.5}
            }
            
            settings = enhancement_settings.get(enhance_level, enhancement_settings['medium'])
            
            # Apply enhancements
            if settings['contrast'] != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(settings['contrast'])
            
            if settings['brightness'] != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(settings['brightness'])
            
            if settings['sharpness'] != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(settings['sharpness'])
            
            # Noise reduction for heavy enhancement
            if enhance_level == 'heavy':
                image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Auto-level for better contrast
            image = ImageOps.autocontrast(image)
            
            # Save enhanced image
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', optimize=True)
            enhanced_data = buffer.getvalue()
            
            image.close()
            gc.collect()  # Force cleanup
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {str(e)}")
            return image_data  # Return original on failure\n    \n    @staticmethod\n    def generate_robust_qr(data: str, **kwargs) -> Dict[str, Any]:\n        \"\"\"\n        Generate QR code with comprehensive error handling and optimization\n        \"\"\"\n        try:\n            # Validate input data\n            if not data or not isinstance(data, str):\n                return {'success': False, 'error': 'Invalid QR data provided'}\n            \n            if len(data) > 4296:  # QR code data limit\n                return {\n                    'success': False, \n                    'error': f'Data too long: {len(data)} chars (max 4296)',\n                    'data_length': len(data)\n                }\n            \n            # Merge settings\n            settings = {**RobustQRProcessor.DEFAULT_QR_SETTINGS, **kwargs}\n            \n            # Create QR code\n            qr = qrcode.QRCode(\n                version=settings['version'],\n                error_correction=settings['error_correction'],\n                box_size=settings['box_size'],\n                border=settings['border'],\n            )\n            \n            qr.add_data(data)\n            qr.make(fit=True)\n            \n            # Generate image\n            qr_image = qr.make_image(\n                fill_color=settings['fill_color'],\n                back_color=settings['back_color'],\n                image_factory=PilImage\n            )\n            \n            # Convert to bytes\n            buffer = io.BytesIO()\n            qr_image.save(buffer, format='PNG', optimize=True)\n            qr_bytes = buffer.getvalue()\n            \n            # Generate metadata\n            qr_hash = hashlib.md5(qr_bytes).hexdigest()[:8]\n            \n            return {\n                'success': True,\n                'qr_image_data': qr_bytes,\n                'qr_image_base64': base64.b64encode(qr_bytes).decode('utf-8'),\n                'data_text': data,\n                'metadata': {\n                    'version': qr.version,\n                    'error_correction': settings['error_correction'],\n                    'data_length': len(data),\n                    'image_size': len(qr_bytes),\n                    'dimensions': qr_image.size,\n                    'hash': qr_hash,\n                    'created_at': datetime.utcnow().isoformat()\n                }\n            }\n            \n        except Exception as e:\n            logger.error(f\"QR generation failed: {str(e)}\")\n            return {\n                'success': False,\n                'error': f'QR generation failed: {str(e)}',\n                'exception_type': type(e).__name__\n            }\n        finally:\n            gc.collect()\n\n\nclass ProductionPDFProcessor:\n    \"\"\"\n    Production-ready PDF processing with robust error handling\n    \"\"\"\n    \n    MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB\n    MAX_PAGES = 100\n    \n    @staticmethod\n    def validate_pdf(pdf_data: bytes, filename: str = \"\") -> Dict[str, Any]:\n        \"\"\"\n        Comprehensive PDF validation\n        \"\"\"\n        try:\n            if not pdf_data:\n                return {'valid': False, 'error': 'Empty PDF data'}\n            \n            size_mb = len(pdf_data) / (1024 * 1024)\n            if len(pdf_data) > ProductionPDFProcessor.MAX_PDF_SIZE:\n                return {\n                    'valid': False,\n                    'error': f'PDF too large: {size_mb:.1f}MB (max {ProductionPDFProcessor.MAX_PDF_SIZE/(1024*1024)}MB)',\n                    'size_mb': size_mb\n                }\n            \n            # Check PDF header\n            if not pdf_data.startswith(b'%PDF-'):\n                return {'valid': False, 'error': 'Invalid PDF format - missing PDF header'}\n            \n            return {\n                'valid': True,\n                'size_bytes': len(pdf_data),\n                'size_mb': round(size_mb, 2)\n            }\n            \n        except Exception as e:\n            return {'valid': False, 'error': f'PDF validation failed: {str(e)}'}\n    \n    @staticmethod\n    def extract_pdf_info(pdf_data: bytes, filename: str = \"\") -> Dict[str, Any]:\n        \"\"\"\n        Extract comprehensive PDF information and text\n        \"\"\"\n        try:\n            from PyPDF2 import PdfReader\n            \n            # Validate first\n            validation = ProductionPDFProcessor.validate_pdf(pdf_data, filename)\n            if not validation['valid']:\n                return {'success': False, **validation}\n            \n            # Read PDF\n            pdf_reader = PdfReader(io.BytesIO(pdf_data))\n            \n            # Get basic info\n            num_pages = len(pdf_reader.pages)\n            \n            if num_pages > ProductionPDFProcessor.MAX_PAGES:\n                return {\n                    'success': False,\n                    'error': f'Too many pages: {num_pages} (max {ProductionPDFProcessor.MAX_PAGES})'\n                }\n            \n            # Extract metadata\n            metadata = pdf_reader.metadata if pdf_reader.metadata else {}\n            \n            # Extract text from all pages\n            extracted_text = []\n            total_text_length = 0\n            \n            for page_num, page in enumerate(pdf_reader.pages, 1):\n                try:\n                    page_text = page.extract_text()\n                    extracted_text.append({\n                        'page_number': page_num,\n                        'text': page_text,\n                        'text_length': len(page_text),\n                        'has_text': bool(page_text.strip())\n                    })\n                    total_text_length += len(page_text)\n                except Exception as e:\n                    extracted_text.append({\n                        'page_number': page_num,\n                        'text': '',\n                        'text_length': 0,\n                        'has_text': False,\n                        'error': str(e)\n                    })\n            \n            # Extract account number from filename\n            account_number = None\n            if filename:\n                account_number = filename.rsplit('.', 1)[0].strip()\n            \n            # Analyze content for debt collection keywords\n            full_text = ' '.join([p['text'] for p in extracted_text]).lower()\n            \n            keywords_found = {\n                'for_customer': 'for customer' in full_text,\n                'payment': any(word in full_text for word in ['payment', 'pay', 'amount']),\n                'account': any(word in full_text for word in ['account', 'acc']),\n                'debt': any(word in full_text for word in ['debt', 'outstanding', 'balance']),\n                'bank': any(word in full_text for word in ['bank', 'financial', 'credit'])\n            }\n            \n            return {\n                'success': True,\n                'filename': filename,\n                'account_number': account_number,\n                'pdf_info': {\n                    'num_pages': num_pages,\n                    'total_text_length': total_text_length,\n                    'has_metadata': bool(metadata),\n                    'metadata': dict(metadata),\n                    'file_size': validation['size_bytes'],\n                    'file_size_mb': validation['size_mb']\n                },\n                'pages': extracted_text,\n                'content_analysis': {\n                    'keywords_found': keywords_found,\n                    'is_debt_document': sum(keywords_found.values()) >= 2,\n                    'has_customer_section': keywords_found['for_customer']\n                },\n                'processing_note': 'PDF text extracted. For QR/barcode extraction, use image conversion or specialized OCR service.'\n            }\n            \n        except ImportError:\n            return {\n                'success': False,\n                'error': 'PyPDF2 library not available',\n                'filename': filename\n            }\n        except Exception as e:\n            logger.error(f\"PDF processing failed for {filename}: {str(e)}\")\n            return {\n                'success': False,\n                'error': f'PDF processing failed: {str(e)}',\n                'filename': filename,\n                'exception_type': type(e).__name__\n            }\n        finally:\n            gc.collect()\n\n\nclass ThaiPaymentQRGenerator:\n    \"\"\"\n    Specialized QR code generator for Thai debt collection payments\n    \"\"\"\n    \n    # Thai payment QR standards\n    THAI_QR_SETTINGS = {\n        'version': 1,\n        'error_correction': qrcode.constants.ERROR_CORRECT_M,\n        'box_size': 8,\n        'border': 2\n    }\n    \n    @staticmethod\n    def create_payment_qr(account_number: str, debtor_name: str, \n                         outstanding_balance: float = None, amount: float = None,\n                         case_id: str = None, contact_info: str = None,\n                         due_date: str = None) -> Dict[str, Any]:\n        \"\"\"\n        Create comprehensive payment QR code for Thai debt collection\n        \"\"\"\n        try:\n            # Validate inputs\n            if not account_number or not debtor_name:\n                return {\n                    'success': False,\n                    'error': 'Account number and debtor name are required'\n                }\n            \n            # Build payment information\n            payment_lines = [\n                \"💳 DEBT PAYMENT INFO\",\n                f\"📋 Account: {account_number}\",\n                f\"👤 Name: {debtor_name[:30]}...\" if len(debtor_name) > 30 else f\"👤 Name: {debtor_name}\"\n            ]\n            \n            # Add financial information\n            if outstanding_balance:\n                payment_lines.append(f\"💰 Outstanding: ฿{outstanding_balance:,.2f}\")\n            \n            if amount:\n                payment_lines.append(f\"💵 Payment Amount: ฿{amount:,.2f}\")\n            \n            # Add reference information\n            if case_id:\n                payment_lines.append(f\"🔖 Case ID: {case_id}\")\n            \n            if due_date:\n                payment_lines.append(f\"📅 Due Date: {due_date}\")\n            \n            # Add contact and instructions\n            payment_lines.extend([\n                \"\",\n                \"📞 Contact Collection Team:\"\n            ])\n            \n            if contact_info:\n                payment_lines.append(f\"   {contact_info}\")\n            else:\n                payment_lines.append(\"   hello@poweramc.co\")\n            \n            payment_lines.extend([\n                \"\",\n                \"📋 Instructions:\",\n                \"1. Make payment to account\",\n                \"2. Take screenshot of receipt\",\n                \"3. Send proof to collection team\",\n                \"\",\n                f\"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\"\n            ])\n            \n            qr_text = \"\\n\".join(payment_lines)\n            \n            # Generate QR code\n            qr_result = RobustQRProcessor.generate_robust_qr(\n                qr_text, \n                **ThaiPaymentQRGenerator.THAI_QR_SETTINGS\n            )\n            \n            if not qr_result['success']:\n                return qr_result\n            \n            # Add payment-specific metadata\n            qr_result.update({\n                'payment_info': {\n                    'account_number': account_number,\n                    'debtor_name': debtor_name,\n                    'outstanding_balance': outstanding_balance,\n                    'payment_amount': amount,\n                    'case_id': case_id,\n                    'contact_info': contact_info,\n                    'due_date': due_date,\n                    'qr_type': 'thai_payment',\n                    'currency': 'THB'\n                }\n            })\n            \n            return qr_result\n            \n        except Exception as e:\n            logger.error(f\"Payment QR generation failed: {str(e)}\")\n            return {\n                'success': False,\n                'error': f'Payment QR generation failed: {str(e)}',\n                'exception_type': type(e).__name__\n            }\n    \n    @staticmethod\n    def create_contact_qr(contact_info: str, company_name: str = \"PowerAMC Collection\") -> Dict[str, Any]:\n        \"\"\"\n        Create contact information QR code\n        \"\"\"\n        try:\n            contact_lines = [\n                f\"🏢 {company_name}\",\n                \"📞 Contact Information\",\n                \"\",\n                f\"📧 Email: {contact_info}\",\n                \"⏰ Business Hours: Mon-Fri 9AM-6PM\",\n                \"\",\n                \"💬 For payment inquiries and\",\n                \"   debt settlement discussions\",\n                \"\",\n                f\"📅 {datetime.now().strftime('%Y-%m-%d')}\"\n            ]\n            \n            qr_text = \"\\n\".join(contact_lines)\n            \n            return RobustQRProcessor.generate_robust_qr(\n                qr_text,\n                box_size=6,\n                border=1\n            )\n            \n        except Exception as e:\n            return {\n                'success': False,\n                'error': f'Contact QR generation failed: {str(e)}'\n            }"