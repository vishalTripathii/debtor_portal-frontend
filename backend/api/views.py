"""
API Views for Debtor Portal
"""
import json
import random
import string
import os
import re
import tempfile
import gc
from datetime import datetime, timedelta, timezone
from pathlib import Path
from io import BytesIO

import bcrypt
import jwt
import pandas as pd
import numpy as np
from bson import ObjectId
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import boto3

# PDF QR Code Extraction imports (optional - graceful fallback if not installed)
PDF_PROCESSING_AVAILABLE = False
OCR_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    import cv2
    from PIL import Image
    from pyzbar.pyzbar import decode as decode_qr
    PDF_PROCESSING_AVAILABLE = True

    # Tesseract OCR is optional - barcode extraction is primary method
    try:
        import pytesseract
        # Configure Tesseract path from environment variable or use defaults
        tesseract_path = os.getenv('TESSERACT_PATH')
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"[OK] Tesseract configured from TESSERACT_PATH: {tesseract_path}")
        elif os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
            # Windows default
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            print("[OK] Tesseract configured from Windows default path")
        elif os.path.exists("/usr/bin/tesseract"):
            # Linux default
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
            print("[OK] Tesseract configured from Linux default path")
        OCR_AVAILABLE = True
        print("[OK] PDF processing available with OCR support")
    except ImportError:
        print("[OK] PDF processing available (OCR disabled - Tesseract not installed)")

except ImportError as e:
    print(f"Warning: PDF processing libraries not installed ({e}). PDF QR extraction disabled.")

# Bangkok timezone (UTC+7)
BANGKOK_TZ = timezone(timedelta(hours=7))

def format_thai_currency(amount):
    """Format amount in Thai Baht"""
    return f"฿{amount:,.2f}"

def parse_currency_value(value, default=0):
    """
    Safely parse currency/number values from Excel.
    Handles: spaces, commas, currency symbols, etc.
    Examples: " 13,354 " -> 13354.0, "฿1,000.50" -> 1000.5
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        # Convert to string and clean up
        str_value = str(value).strip()
        # Remove currency symbols and common formatting
        str_value = str_value.replace('฿', '').replace('$', '').replace(',', '').strip()
        if str_value == '' or str_value.lower() == 'nan':
            return default
        return float(str_value)
    except (ValueError, TypeError):
        return default

def get_bangkok_time():
    """Get current time in Bangkok timezone"""
    return datetime.now(BANGKOK_TZ).strftime('%Y-%m-%d %H:%M:%S')

def send_otp_via_lambda(email, otp, name="Customer"):
    """
    Send OTP email via the email Lambda function instead of Django send_mail
    """
    try:
        lambda_client = boto3.client('lambda', region_name=os.getenv('S3_REGION', 'ap-southeast-1'))
        
        payload = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'action': 'send-otp',
                'email': email,
                'otp': otp,
                'name': name
            })
        }
        
        response = lambda_client.invoke(
            FunctionName=f"debtor-portal-api-{os.getenv('STAGE', 'dev')}-email",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        response_body = json.loads(response_payload.get('body', '{}'))
        
        if response_body.get('success'):
            print(f"✅ OTP email sent successfully via Lambda to {email}")
            return True
        else:
            print(f"❌ Email Lambda failed: {response_body.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send OTP via Lambda: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_date_only(value):
    """
    Format date value to only show date (YYYY-MM-DD), removing any time component.
    Handles: pandas Timestamp, datetime objects, strings with time, etc.
    """
    if value is None:
        return ''

    # Handle pandas NaT (Not a Time)
    if str(value).lower() in ('nat', 'nan', ''):
        return ''

    # If it's already a datetime-like object
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')

    # Convert to string and extract date part
    str_value = str(value).strip()
    if not str_value:
        return ''

    # If string contains time component (space or T separator), extract just the date
    if ' ' in str_value:
        str_value = str_value.split(' ')[0]
    elif 'T' in str_value:
        str_value = str_value.split('T')[0]

    return str_value

# Email templates for both languages
EMAIL_TEMPLATES = {
    'en': {
        'otp_subject': 'Your OTP for Customer Portal Login',
        'otp_body': """
Dear Customer,

Your One-Time Password (OTP) for logging into the Customer Self-Service Portal is:

    {otp}

This OTP is valid for 5 minutes. Please do not share this code with anyone.

You have {account_count} account(s) linked to your National ID.

If you did not request this OTP, please ignore this email.

Best regards,
Collections Team
""",
        'payment_subject': 'Payment Notification - Account {account_number} - Transaction: {transaction_number}',
        'payment_body': """
PAYMENT NOTIFICATION
====================

A customer has submitted a payment through the Self-Service Portal.

CUSTOMER DETAILS
----------------
Account Number: {account_number}
Name: {name}
National ID: {national_id}
Phone: {phone}
Email: {email}

DEBT INFORMATION
----------------
Original Creditor: {original_creditor}
Debt Type: {debt_type}
Outstanding Balance: {outstanding_balance}
Loan Contract Date: {loan_contract_date}

PAYMENT DETAILS
---------------
Payment Type: {payment_type}
Payment Amount: {payment_amount}
Transaction Number: {transaction_number}

TIMESTAMP
---------
Date/Time: {timestamp} (Bangkok)

---
This is an automated notification from the Customer Self-Service Portal.
Please verify the transaction and update the payment status.
""",
        'not_ready_subject': 'Need Support to Pay - Account {account_number}',
        'not_ready_body': """
NEED SUPPORT TO PAY NOTIFICATION
================================

A customer needs support to make a payment.

CUSTOMER DETAILS
----------------
Account Number: {account_number}
Name: {name}
National ID: {national_id}
Phone: {phone}
Email: {email}

DEBT INFORMATION
----------------
Original Creditor: {original_creditor}
Debt Type: {debt_type}
Outstanding Balance: {outstanding_balance}
Loan Contract Date: {loan_contract_date}

SUPPORT REQUEST DETAILS
-----------------------
Instalment Plan: {instalment_plan}
Unable to Pay Now: {reason}

Customer Notes:
{notes}

CONTACT PREFERENCES
-------------------
Preferred Date: {preferred_contact_date}
Preferred Time: {preferred_contact_time}
Preferred Contact Method: {preferred_contact_method}

TIMESTAMP
---------
Date/Time: {timestamp} (Bangkok)

---
This is an automated notification from the Customer Self-Service Portal.
Please review this case and follow up with the customer as appropriate.
"""
    },
    'th': {
        'otp_subject': 'รหัส OTP สำหรับเข้าสู่ระบบพอร์ทัลลูกค้า',
        'otp_body': """
เรียน ลูกค้า

รหัสผ่านครั้งเดียว (OTP) สำหรับเข้าสู่ระบบพอร์ทัลบริการตนเองสำหรับลูกค้าของคุณคือ:

    {otp}

รหัส OTP นี้ใช้ได้ภายใน 5 นาที กรุณาอย่าแชร์รหัสนี้กับผู้อื่น

คุณมี {account_count} บัญชีที่เชื่อมโยงกับเลขประจำตัวประชาชนของคุณ

หากคุณไม่ได้ขอรหัส OTP นี้ กรุณาเพิกเฉยอีเมลนี้

ด้วยความเคารพ
ทีมเรียกเก็บหนี้
""",
        'payment_subject': 'แจ้งเตือนการชำระเงิน - บัญชี {account_number} - ธุรกรรม: {transaction_number}',
        'payment_body': """
แจ้งเตือนการชำระเงิน
====================

ลูกค้าได้ส่งการชำระเงินผ่านพอร์ทัลบริการตนเอง

รายละเอียดลูกค้า
----------------
เลขที่บัญชี: {account_number}
ชื่อ: {name}
เลขประจำตัวประชาชน: {national_id}
โทรศัพท์: {phone}
อีเมล: {email}

ข้อมูลหนี้
----------------
เจ้าหนี้เดิม: {original_creditor}
ประเภทหนี้: {debt_type}
ยอดคงค้าง: {outstanding_balance}
วันที่ทำสัญญาเงินกู้: {loan_contract_date}

รายละเอียดการชำระเงิน
---------------
ประเภทการชำระ: {payment_type}
จำนวนเงินที่ชำระ: {payment_amount}
เลขที่ธุรกรรม: {transaction_number}

เวลา
---------
วันที่/เวลา: {timestamp} (กรุงเทพฯ)

---
นี่คือการแจ้งเตือนอัตโนมัติจากพอร์ทัลบริการตนเองสำหรับลูกค้า
กรุณาตรวจสอบธุรกรรมและอัปเดตสถานะการชำระเงิน
""",
        'not_ready_subject': 'ต้องการความช่วยเหลือในการชำระ - บัญชี {account_number}',
        'not_ready_body': """
แจ้งเตือนต้องการความช่วยเหลือในการชำระเงิน
==========================================

ลูกค้าต้องการความช่วยเหลือในการชำระเงิน

รายละเอียดลูกค้า
----------------
เลขที่บัญชี: {account_number}
ชื่อ: {name}
เลขประจำตัวประชาชน: {national_id}
โทรศัพท์: {phone}
อีเมล: {email}

ข้อมูลหนี้
----------------
เจ้าหนี้เดิม: {original_creditor}
ประเภทหนี้: {debt_type}
ยอดคงค้าง: {outstanding_balance}
วันที่ทำสัญญาเงินกู้: {loan_contract_date}

รายละเอียดคำขอความช่วยเหลือ
---------------------------
โปรแกรมผ่อนชำระ: {instalment_plan}
ไม่สามารถจ่ายชำระได้ ณ ตอนนี้: {reason}

หมายเหตุจากลูกค้า:
{notes}

ความต้องการในการติดต่อ
----------------------
วันที่ต้องการให้ติดต่อ: {preferred_contact_date}
เวลาที่ต้องการให้ติดต่อ: {preferred_contact_time}
ช่องทางการติดต่อที่ต้องการ: {preferred_contact_method}

เวลา
---------
วันที่/เวลา: {timestamp} (กรุงเทพฯ)

---
นี่คือการแจ้งเตือนอัตโนมัติจากพอร์ทัลบริการตนเองสำหรับลูกค้า
กรุณาตรวจสอบกรณีนี้และติดตามลูกค้าตามความเหมาะสม
"""
    }
}

def get_email_template(template_key, language='en'):
    """Get email template in the specified language, fallback to English"""
    lang = language if language in EMAIL_TEMPLATES else 'en'
    return EMAIL_TEMPLATES[lang].get(template_key, EMAIL_TEMPLATES['en'].get(template_key, ''))

# Production QR Processing imports with graceful fallback
try:
    from .production_qr import RobustQRProcessor, ProductionPDFProcessor, ThaiPaymentQRGenerator
    PRODUCTION_QR_AVAILABLE = True
    print("[OK] Production QR processing available")
except ImportError:
    print("[Fallback] Using Lambda QR processor")
    try:
        from .lambda_qr import LambdaQRProcessor, PaymentQRGenerator
        PRODUCTION_QR_AVAILABLE = False
    except ImportError:
        print("[Error] No QR processor available")
        PRODUCTION_QR_AVAILABLE = False
from .database import (
    get_debtors_collection,
    get_admins_collection,
    get_notifications_collection,
    get_settings_collection,
    get_upload_history_collection,
    get_system_settings_collection,
    get_debtor_images_collection,
    get_otp_collection,
    get_processing_jobs_collection
)
import base64

# Import storage module for S3/local file operations
from api.aws_storage import storage
from api.storage_utils import (
    get_upload_key, get_image_key, get_receipt_key, get_pdf_staging_key,
    generate_receipt_filename, generate_upload_id,
    save_uploaded_file, save_receipt, save_debtor_image, save_pdf_to_staging,
    get_file, get_receipt,
    get_debtor_image as fetch_debtor_image_data,  # Renamed to avoid conflict with view function
    get_presigned_receipt_url, get_presigned_image_url,
    file_exists, receipt_exists, debtor_image_exists,
    delete_file, delete_receipt,
    delete_debtor_image as remove_debtor_image_from_storage,  # Renamed to avoid conflict with view function
    delete_staging_folder,
    list_staging_files,
    MEDIA_DIR, IMAGES_DIR, UPLOADS_DIR, RECEIPTS_DIR, PDF_STAGING_DIR,
    UPLOADS_PREFIX, IMAGES_PREFIX, RECEIPTS_PREFIX, PDF_STAGING_PREFIX
)

# SQS integration for PDF processing (optional)
SQS_AVAILABLE = False
sqs_client = None
try:
    import boto3
    if settings.USE_SQS_FOR_PDF and settings.PDF_QUEUE_URL:
        sqs_client = boto3.client('sqs', region_name=settings.AWS_REGION)
        SQS_AVAILABLE = True
        print(f"[OK] SQS integration enabled for PDF processing")
except Exception as e:
    print(f"[INFO] SQS not available: {e}")


# ============================================
# PDF QR CODE EXTRACTION FUNCTIONS
# ============================================

def extract_ref1_from_barcode(barcode_data):
    """Extracts Ref1 number from barcode data string.
    Barcode format: |010556503082900 202111000201554 3820100052883 0
    The second number (15 digits) is the Ref1 (account number).
    First number is the biller ID, second is Ref1, third is Ref2.
    """
    if not barcode_data:
        return None

    try:
        print(f"Extracting Ref1 from barcode: {barcode_data}")
        # Remove leading pipe and split by space
        parts = barcode_data.replace('|', '').strip().split()

        # Collect all 15-digit numbers
        fifteen_digit_numbers = [part for part in parts if len(part) == 15 and part.isdigit()]

        # The second 15-digit number is Ref1 (index 1)
        if len(fifteen_digit_numbers) >= 2:
            ref1 = fifteen_digit_numbers[1]
            print(f"[OK] Ref1 extracted from barcode (2nd 15-digit): {ref1}")
            return ref1

        # Fallback: if only one 15-digit number, use it
        if len(fifteen_digit_numbers) == 1:
            ref1 = fifteen_digit_numbers[0]
            print(f"[OK] Ref1 extracted from barcode (only 15-digit): {ref1}")
            return ref1

        # Fallback: look for any number between 10-20 digits
        for part in parts:
            if 10 <= len(part) <= 20 and part.isdigit():
                print(f"[OK] Ref1 extracted from barcode (fallback): {part}")
                return part

        print("✗ Ref1 not found in barcode data")
        return None
    except Exception as e:
        print(f"Barcode parsing error: {e}")
        return None


def extract_ref1_from_image(img):
    """Extracts Ref1 number from OCR text (requires Tesseract)"""
    if not OCR_AVAILABLE:
        print("OCR not available - skipping image text extraction")
        return None

    try:
        # Use English only - Thai traineddata may not be installed
        text = pytesseract.image_to_string(img, lang="eng")
        print(f"OCR Text: {text[:500]}...")  # Debug - first 500 chars

        # Try different patterns for Ref1
        patterns = [
            r"\(Ref1\)[^\d]*(\d{10,20})",  # (Ref1) followed by digits - exact format in PDF
            r"Ref1[)\s]*(\d{10,20})",  # Ref1) or Ref1 followed by digits
            r"เลขท[ีi]่?บ[ัa]ญช[ีi][^\d]*(\d{10,20})",  # Thai: เลขที่บัญชี followed by digits
            r"Ref1[^\d]*(\d{6,20})",  # Ref1 followed by digits
            r"Ref\.?\s*1[^\d]*(\d{6,20})",  # Ref.1 or Ref 1
            r"Reference\s*1?[^\d]*(\d{6,20})",  # Reference or Reference1
            r"REF1[^\d]*(\d{6,20})",  # REF1 uppercase
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref1 = match.group(1)
                print(f"[OK] Ref1 extracted via OCR: {ref1}")
                return ref1

        # Fallback: Look for a 15-digit number (common Ref1 format)
        long_numbers = re.findall(r'\b(\d{15})\b', text)
        if long_numbers:
            ref1 = long_numbers[0]
            print(f"[OK] Ref1 extracted via OCR (fallback 15-digit): {ref1}")
            return ref1

        print("✗ Ref1 not found in OCR text")
        return None
    except Exception as e:
        print(f"OCR Error: {e}")
        return None


def process_pdf_for_qr(pdf_file, filename):
    """
    Process a PDF file to extract QR codes.
    Account number is derived from the PDF filename (e.g., "211024PAY00000067.pdf" -> "211024PAY00000067").
    PDF must contain "For Customer" text to be valid for QR extraction.
    Returns a list of tuples: [(account_number, qr_image_bytes), ...]
    """
    if not PDF_PROCESSING_AVAILABLE:
        return [], ["PDF processing libraries not installed"]

    results = []
    errors = []
    doc = None
    pix = None
    img = None
    top_half = None
    qr_crop = None
    opencv_img = None
    opencv_full = None

    # Extract account number from filename (remove .pdf extension)
    account_number = filename.rsplit('.', 1)[0].strip()

    try:
        # Read PDF content
        pdf_content = pdf_file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        # Process first page to extract QR and verify "For Customer" text
        if len(doc) == 0:
            errors.append(f"{filename}: PDF has no pages")
            return results, errors

        page = doc[0]
        # Render page at 200 DPI (reduced from 300 for memory efficiency)
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Clear pixmap data immediately
        pix = None

        h, w = img.size[1], img.size[0]

        # The PDF has 2 identical sections per page. Process only top half (For Customer)
        top_half = img.crop((0, 0, w, int(h * 0.50)))

        # Clear original image
        img.close() if hasattr(img, 'close') else None
        img = None

        top_h = top_half.size[1]

        # STEP 1: Verify "For Customer" text is present using OCR
        for_customer_found = False
        if OCR_AVAILABLE:
            try:
                text = pytesseract.image_to_string(top_half)
                # Check for "For Customer" text (case-insensitive)
                if "for customer" in text.lower():
                    for_customer_found = True
            except Exception as e:
                pass  # Silently continue if OCR fails
        else:
            # If OCR is not available, assume it's valid (rely on filename matching only)
            for_customer_found = True

        if not for_customer_found:
            errors.append(f"{filename}: 'For Customer' text not found in PDF")
            return results, errors

        # STEP 2: Detect and extract QR/barcode
        # QR/Barcode area: Bottom-left portion of the top half
        qr_crop = top_half.crop((0, int(top_h * 0.55), int(w * 0.60), top_h))
        opencv_img = cv2.cvtColor(np.array(qr_crop), cv2.COLOR_RGB2BGR)

        # Clear PIL crop
        qr_crop.close() if hasattr(qr_crop, 'close') else None
        qr_crop = None

        qr_codes = decode_qr(opencv_img)

        qr_img = None

        if qr_codes:
            qr = qr_codes[0]
            x, y, wbox, hbox = qr.rect
            # Add padding around barcode for better scanning
            padding = 20
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(opencv_img.shape[1], x + wbox + padding)
            y2 = min(opencv_img.shape[0], y + hbox + padding)
            qr_img = opencv_img[y1:y2, x1:x2].copy()
            opencv_img = None
        else:
            # Try with the full top half if no barcode found in cropped area
            opencv_img = None  # Clear previous
            opencv_full = cv2.cvtColor(np.array(top_half), cv2.COLOR_RGB2BGR)
            qr_codes = decode_qr(opencv_full)
            if qr_codes:
                qr = qr_codes[0]
                x, y, wbox, hbox = qr.rect
                padding = 20
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(opencv_full.shape[1], x + wbox + padding)
                y2 = min(opencv_full.shape[0], y + hbox + padding)
                qr_img = opencv_full[y1:y2, x1:x2].copy()
            else:
                errors.append(f"{filename}: No barcode/QR detected")
            opencv_full = None

        # Clear top_half
        top_half.close() if hasattr(top_half, 'close') else None
        top_half = None

        if qr_img is not None:
            # Encode QR image to PNG (better quality than JPG for QR codes)
            _, buffer = cv2.imencode('.png', qr_img)
            qr_bytes = buffer.tobytes()
            results.append((account_number, qr_bytes))
            qr_img = None

    except Exception as e:
        errors.append(f"{filename}: {str(e)}")
    finally:
        # Clean up resources
        if doc:
            doc.close()
        # Force garbage collection
        gc.collect()

    return results, errors


# Secret key for JWT
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'

# OTPs are now stored in MongoDB for multi-worker support (see get_otp_collection)


def create_notification(notification_type, title, message, debtor_data, metadata=None):
    """Create a notification for admin portal"""
    notifications = get_notifications_collection()

    notification = {
        'type': notification_type,  # 'payment_request', 'not_ready_to_pay'
        'title': title,
        'message': message,
        'debtor': {
            'account_number': debtor_data.get('account_number', 'N/A'),
            'name': debtor_data.get('name', 'N/A'),
            'phone': debtor_data.get('phone', 'N/A'),
            'email': debtor_data.get('email', 'N/A'),
            'outstanding_balance': debtor_data.get('outstanding_balance', 0),
        },
        'metadata': metadata or {},
        'read': False,
        'created_at': datetime.utcnow(),
    }

    result = notifications.insert_one(notification)
    notification['_id'] = str(result.inserted_id)
    return notification


def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def create_jwt_token(payload, expires_hours=24):
    """Create JWT token"""
    payload['exp'] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        print("JWT Error: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"JWT Error: Invalid token - {e}")
        return None


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'ok', 'message': 'API is running'})


@csrf_exempt
@require_http_methods(["POST"])
def admin_login(request):
    """Admin login endpoint - simple username/password authentication"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        admins = get_admins_collection()
        admin = admins.find_one({'username': username})

        if not admin:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
            role = admin.get('role', 'admin')
            token = create_jwt_token({'username': username, 'role': role}, expires_hours=72)
            return JsonResponse({
                'success': True,
                'token': token,
                'username': username,
                'role': role
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_admin_otp(request):
    """Verify admin login OTP"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        otp = data.get('otp')

        if not username or not otp:
            return JsonResponse({'error': 'Username and OTP are required'}, status=400)

        admins = get_admins_collection()
        admin = admins.find_one({'username': username})

        if not admin:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        stored_otp = admin.get('otp')
        otp_expiry = admin.get('otp_expiry')

        if not stored_otp or not otp_expiry:
            return JsonResponse({'error': 'No OTP found. Please login again.'}, status=400)

        # Check OTP expiry
        if datetime.utcnow() > otp_expiry:
            return JsonResponse({'error': 'OTP has expired. Please login again.'}, status=400)

        # Verify OTP
        if otp != stored_otp:
            return JsonResponse({'error': 'Invalid OTP'}, status=401)

        # Clear OTP and mark as verified
        admins.update_one(
            {'username': username},
            {'$unset': {'otp': '', 'otp_expiry': ''}, '$set': {'otp_verified': True}}
        )

        # Generate token
        role = admin.get('role', 'admin')
        token = create_jwt_token({'username': username, 'role': role}, expires_hours=72)

        return JsonResponse({
            'success': True,
            'token': token,
            'username': username,
            'role': role
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_upload_id():
    """Generate a unique Upload ID in format UPL-YYYYMMDD-NNN"""
    import random
    upload_history = get_upload_history_collection()
    today = datetime.utcnow().strftime('%Y%m%d')
    today_prefix = f'UPL-{today}-'

    # Try to find a unique ID with retries
    max_retries = 10
    for attempt in range(max_retries):
        # Find the highest sequence number for today
        latest = upload_history.find_one(
            {'upload_id': {'$regex': f'^{today_prefix}'}},
            sort=[('upload_id', -1)]
        )

        if latest and latest.get('upload_id'):
            # Extract sequence number and increment
            try:
                seq = int(latest['upload_id'].split('-')[-1]) + 1
            except:
                seq = 1
        else:
            seq = 1

        # Add attempt number to avoid collisions in race conditions
        seq += attempt

        upload_id = f'UPL-{today}-{seq:03d}'

        # Check if this ID already exists
        existing = upload_history.find_one({'upload_id': upload_id})
        if not existing:
            return upload_id

    # Fallback: add random suffix if all retries fail
    random_suffix = random.randint(100, 999)
    return f'UPL-{today}-{random_suffix}'


def generate_case_id():
    """Generate a unique Case ID in format CASE-NNNNN"""
    debtors = get_debtors_collection()

    # Find the highest case_id
    latest = debtors.find_one(
        {'case_id': {'$exists': True, '$ne': None}},
        sort=[('case_id', -1)]
    )

    if latest and latest.get('case_id'):
        # Extract sequence number and increment
        try:
            seq = int(latest['case_id'].split('-')[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1

    return f'CASE-{seq:05d}'


@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """Upload Excel or CSV file with debtor data"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Debug: Log request info for troubleshooting
        print(f"Content-Type: {request.content_type}")
        print(f"FILES keys: {list(request.FILES.keys())}")
        print(f"POST keys: {list(request.POST.keys())}")

        # Get uploaded file
        if 'file' not in request.FILES:
            return JsonResponse({
                'error': 'No file uploaded',
                'debug': {
                    'content_type': request.content_type,
                    'files_keys': list(request.FILES.keys()),
                    'post_keys': list(request.POST.keys())
                }
            }, status=400)

        file = request.FILES['file']
        filename = file.name.lower()
        original_filename = file.name  # Keep original name with case

        # Generate Upload ID for this batch
        upload_id = generate_upload_id()

        # Read file content
        file_content = file.read()
        file_size = len(file_content)

        # Create BytesIO object for pandas to read
        from io import BytesIO
        file_buffer = BytesIO(file_content)

        # Determine file extension
        file_ext = Path(original_filename).suffix.lower()

        # Save file to storage with upload_id as filename
        saved_filename = f"{upload_id}{file_ext}"
        upload_key = get_upload_key(saved_filename)
        save_uploaded_file(file_content, upload_key)

        # Read file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(file_buffer)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_buffer)
        else:
            return JsonResponse({'error': 'Unsupported file format. Please upload .csv, .xlsx, or .xls file'}, status=400)

        # Expected columns mapping
        column_mapping = {
            'Account Number': 'account_number',
            'National ID': 'national_id',
            'Original Creditor': 'original_creditor',
            'Outstanding Balance': 'outstanding_balance',
            'Debt Type': 'debt_type',
            'Loan CONTRACT DATE': 'loan_contract_date',
            'Name': 'name',
            'Phone': 'phone',
            'Email': 'email'
        }

        # Validate required columns
        required_columns = list(column_mapping.keys())
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return JsonResponse({
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            }, status=400)

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Convert to records
        records = df.to_dict('records')

        # Process each record
        debtors = get_debtors_collection()
        inserted_count = 0
        updated_count = 0

        for record in records:
            # Clean and format data
            account_number = str(record.get('account_number', '')).strip()

            if not account_number:
                continue

            # Check if debtor already exists
            existing_debtor = debtors.find_one({'account_number': account_number})

            debtor_data = {
                'account_number': account_number,
                'national_id': str(record.get('national_id', '')).strip(),
                'original_creditor': str(record.get('original_creditor', '')).strip(),
                'outstanding_balance': parse_currency_value(record.get('outstanding_balance', 0)),
                'debt_type': str(record.get('debt_type', '')).strip(),
                'loan_contract_date': format_date_only(record.get('loan_contract_date', '')),
                'name': str(record.get('name', '')).strip(),
                'phone': str(record.get('phone', '')).strip(),
                'email': str(record.get('email', '')).strip(),
                'upload_id': upload_id,  # Link to upload batch
                'updated_at': datetime.utcnow(),
            }

            # Set on insert fields
            set_on_insert = {
                'created_at': datetime.utcnow(),
            }

            # Generate case_id only for new records
            if not existing_debtor:
                set_on_insert['case_id'] = generate_case_id()

            # Upsert (update if exists, insert if not)
            result = debtors.update_one(
                {'account_number': account_number},
                {'$set': debtor_data, '$setOnInsert': set_on_insert},
                upsert=True
            )

            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count > 0:
                updated_count += 1

        # Save upload history with file path (not content)
        upload_history = get_upload_history_collection()
        history_record = {
            'upload_id': upload_id,
            'filename': original_filename,
            'saved_filename': saved_filename,
            'file_path': str(saved_file_path),
            'file_size': file_size,
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if filename.endswith('.xlsx') else 'application/vnd.ms-excel' if filename.endswith('.xls') else 'text/csv',
            'total_records': len(records),
            'inserted_count': inserted_count,
            'updated_count': updated_count,
            'uploaded_by': payload.get('username', 'admin'),
            'uploaded_at': datetime.utcnow(),
            'status': 'success'
        }
        upload_history.insert_one(history_record)

        return JsonResponse({
            'success': True,
            'message': f'Successfully processed {len(records)} records',
            'upload_id': upload_id,
            'inserted': inserted_count,
            'updated': updated_count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_file_base64(request):
    """Upload Excel or CSV file with base64 encoded data (workaround for API Gateway)"""
    import base64
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Parse JSON body
        data = json.loads(request.body)
        
        # Get base64 file data
        if 'file_data' not in data or 'filename' not in data:
            return JsonResponse({'error': 'Missing file_data or filename'}, status=400)

        filename = data['filename'].lower()
        original_filename = data['filename']
        file_data_b64 = data['file_data']

        # Decode base64 data
        try:
            file_content = base64.b64decode(file_data_b64)
        except Exception as e:
            return JsonResponse({'error': f'Invalid base64 data: {str(e)}'}, status=400)

        file_size = len(file_content)

        # Generate Upload ID for this batch
        upload_id = generate_upload_id()

        # Create BytesIO object for pandas to read
        file_buffer = BytesIO(file_content)

        # Determine file extension
        file_ext = Path(original_filename).suffix.lower()

        # Save file to storage with upload_id as filename
        saved_filename = f"{upload_id}{file_ext}"
        upload_key = get_upload_key(saved_filename)
        save_uploaded_file(file_content, upload_key)

        # Read file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(file_buffer)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_buffer)
        else:
            return JsonResponse({'error': 'Unsupported file format. Please upload .csv, .xlsx, or .xls file'}, status=400)

        # Process the data (same logic as original upload_file)
        # Expected columns mapping
        column_mapping = {
            'Account Number': 'account_number',
            'National ID': 'national_id',
            'Original Creditor': 'original_creditor',
            'Outstanding Balance': 'outstanding_balance',
            'Debt Type': 'debt_type',
            'Loan CONTRACT DATE': 'loan_contract_date',
            'Name': 'name',
            'Phone': 'phone',
            'Email': 'email'
        }

        # Validate required columns
        required_columns = list(column_mapping.keys())
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return JsonResponse({
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            }, status=400)

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Convert to records
        records = df.to_dict('records')

        # Process each record
        debtors = get_debtors_collection()
        inserted_count = 0
        updated_count = 0

        for record in records:
            # Clean and format data
            account_number = str(record.get('account_number', '')).strip()

            if not account_number:
                continue

            # Check if debtor already exists
            existing_debtor = debtors.find_one({'account_number': account_number})

            debtor_data = {
                'account_number': account_number,
                'national_id': str(record.get('national_id', '')).strip(),
                'original_creditor': str(record.get('original_creditor', '')).strip(),
                'outstanding_balance': parse_currency_value(record.get('outstanding_balance', 0)),
                'debt_type': str(record.get('debt_type', '')).strip(),
                'loan_contract_date': format_date_only(record.get('loan_contract_date', '')),
                'name': str(record.get('name', '')).strip(),
                'phone': str(record.get('phone', '')).strip(),
                'email': str(record.get('email', '')).strip(),
                'upload_id': upload_id,  # Link to upload batch
                'updated_at': datetime.utcnow(),
            }

            # Set on insert fields
            set_on_insert = {
                'created_at': datetime.utcnow(),
            }

            # Generate case_id only for new records
            if not existing_debtor:
                set_on_insert['case_id'] = generate_case_id()

            # Upsert (update if exists, insert if not)
            result = debtors.update_one(
                {'account_number': account_number},
                {'$set': debtor_data, '$setOnInsert': set_on_insert},
                upsert=True
            )

            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count > 0:
                updated_count += 1

        # Save upload history with file path (not content)
        upload_history = get_upload_history_collection()
        history_record = {
            'upload_id': upload_id,
            'filename': original_filename,
            'saved_filename': saved_filename,
            'file_path': upload_key,
            'file_size': file_size,
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if filename.endswith('.xlsx') else 'application/vnd.ms-excel' if filename.endswith('.xls') else 'text/csv',
            'total_records': len(records),
            'inserted_count': inserted_count,
            'updated_count': updated_count,
            'uploaded_by': payload.get('username', 'admin'),
            'uploaded_at': datetime.utcnow(),
            'status': 'success'
        }
        upload_history.insert_one(history_record)

        return JsonResponse({
            'success': True,
            'message': f'Successfully processed {len(records)} records',
            'upload_id': upload_id,
            'inserted': inserted_count,
            'updated': updated_count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_upload_presigned_url(request):
    """
    Get a presigned URL for direct S3 upload (for files > 10MB)
    This bypasses API Gateway's 10MB payload limit
    """
    import boto3
    
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Parse request
        data = json.loads(request.body)
        filename = data.get('filename')
        file_size = data.get('file_size', 0)
        
        if not filename:
            return JsonResponse({'error': 'Filename is required'}, status=400)

        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return JsonResponse({'error': 'Unsupported file format'}, status=400)

        # Generate job ID
        job_id = f"UPLOAD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        staging_filename = f"{job_id}{file_ext}"
        staging_key = f"excel_staging/{staging_filename}"

        # Create presigned URL for S3 upload
        s3_client = boto3.client('s3', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'power-amc-debtor-media-dev')
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': staging_key,
                'ContentType': 'application/octet-stream'
            },
            ExpiresIn=3600  # 1 hour
        )

        # Create job record with 'pending_upload' status
        jobs_collection = get_processing_jobs_collection()
        job_record = {
            'job_id': job_id,
            'type': 'excel_upload',
            'status': 'pending_upload',
            'original_filename': filename,
            'staged_filename': staging_filename,
            'file_size': file_size,
            'file_extension': file_ext,
            'staging_key': staging_key,
            'total_records': 0,
            'processed_records': 0,
            'inserted_count': 0,
            'updated_count': 0,
            'error_count': 0,
            'errors': [],
            'created_at': datetime.utcnow(),
            'created_by': payload.get('username', 'admin'),
            'started_at': None,
            'completed_at': None,
            'percentage': 0
        }
        jobs_collection.insert_one(job_record)

        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'presigned_url': presigned_url,
            'staging_key': staging_key,
            'expires_in': 3600
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_processing(request):
    """
    Start processing after direct S3 upload completes (for files > 10MB)
    """
    import boto3
    
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Parse request
        data = json.loads(request.body)
        job_id = data.get('job_id')
        
        if not job_id:
            return JsonResponse({'error': 'job_id is required'}, status=400)

        # Get job record
        jobs_collection = get_processing_jobs_collection()
        job = jobs_collection.find_one({'job_id': job_id})
        
        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)

        if job.get('status') != 'pending_upload':
            return JsonResponse({'error': f'Job is not in pending_upload status, current: {job.get("status")}'}, status=400)

        # Update status to queued
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {'status': 'queued'}}
        )

        # Invoke the excelProcessor Lambda ASYNCHRONOUSLY
        lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
        stage = os.environ.get('STAGE', 'dev')
        processor_function_name = f"debtor-portal-api-{stage}-excelProcessor"
        
        processor_payload = {
            'job_id': job_id,
            'staging_key': job.get('staging_key'),
            'file_extension': job.get('file_extension'),
            'original_filename': job.get('original_filename'),
            'created_by': job.get('created_by', 'admin')
        }
        
        lambda_client.invoke(
            FunctionName=processor_function_name,
            InvocationType='Event',
            Payload=json.dumps(processor_payload)
        )

        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'status': 'queued',
            'message': 'Processing started'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_file_async(request):
    """
    Asynchronously upload and process large Excel/CSV files (supports 1,000,000+ records)
    
    This endpoint:
    1. Quickly stages the file to S3 (fast, returns within 30s)
    2. Invokes the excelProcessor Lambda ASYNCHRONOUSLY (bypasses API Gateway 30s limit)
    3. Returns job_id immediately for status polling
    
    The excelProcessor Lambda runs for up to 15 minutes (900s) to process the file.
    """
    import base64
    import boto3
    
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Parse JSON body
        data = json.loads(request.body)
        
        # Get base64 file data
        if 'file_data' not in data or 'filename' not in data:
            return JsonResponse({'error': 'Missing file_data or filename'}, status=400)

        original_filename = data['filename']
        file_data_b64 = data['file_data']

        # Decode base64 data
        try:
            file_content = base64.b64decode(file_data_b64)
        except Exception as e:
            return JsonResponse({'error': f'Invalid base64 data: {str(e)}'}, status=400)

        file_size = len(file_content)

        # Generate job ID for this upload
        job_id = f"UPLOAD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        # Determine file extension
        file_ext = Path(original_filename).suffix.lower()

        # Validate file format
        if not file_ext in ['.csv', '.xlsx', '.xls']:
            return JsonResponse({'error': 'Unsupported file format. Please upload .csv, .xlsx, or .xls file'}, status=400)

        # Save file to staging storage (S3)
        staging_filename = f"{job_id}{file_ext}"
        staging_key = f"excel_staging/{staging_filename}"
        storage.upload_file(file_content, staging_key, 'application/octet-stream')

        # Create job record with 'queued' status
        jobs_collection = get_processing_jobs_collection()
        job_record = {
            'job_id': job_id,
            'type': 'excel_upload',
            'status': 'queued',  # queued -> processing -> completed/failed
            'original_filename': original_filename,
            'staged_filename': staging_filename,
            'file_size': file_size,
            'file_extension': file_ext,
            'staging_key': staging_key,
            'total_records': 0,
            'processed_records': 0,
            'inserted_count': 0,
            'updated_count': 0,
            'error_count': 0,
            'errors': [],
            'created_at': datetime.utcnow(),
            'created_by': payload.get('username', 'admin'),
            'started_at': None,
            'completed_at': None,
            'percentage': 0
        }
        jobs_collection.insert_one(job_record)

        # Invoke the excelProcessor Lambda ASYNCHRONOUSLY
        # This bypasses API Gateway's 30-second timeout limit
        try:
            lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
            
            # Get function name from environment or construct it
            stage = os.environ.get('STAGE', 'dev')
            processor_function_name = f"debtor-portal-api-{stage}-excelProcessor"
            
            # Payload for the processor
            processor_payload = {
                'job_id': job_id,
                'staging_key': staging_key,
                'file_extension': file_ext,
                'original_filename': original_filename,
                'created_by': payload.get('username', 'admin')
            }
            
            # Invoke ASYNCHRONOUSLY (InvocationType='Event')
            # This returns immediately and Lambda runs in background for up to 900s
            lambda_client.invoke(
                FunctionName=processor_function_name,
                InvocationType='Event',  # Async invocation - returns immediately!
                Payload=json.dumps(processor_payload)
            )
            
            print(f"Async invocation triggered for job {job_id}")
            
        except Exception as lambda_err:
            # If Lambda invocation fails, mark job as failed
            print(f"Lambda invocation failed: {str(lambda_err)}")
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'failed',
                    'errors': [f'Failed to start processor: {str(lambda_err)}'],
                    'completed_at': datetime.utcnow()
                }}
            )
            return JsonResponse({
                'error': f'Failed to start background processor: {str(lambda_err)}'
            }, status=500)

        # Return immediately with job_id for status polling
        return JsonResponse({
            'success': True,
            'message': 'Upload received! Processing in background (up to 15 minutes for large files).',
            'job_id': job_id,
            'status': 'queued',
            'file_size': file_size,
            'polling_url': f'/api/admin/upload-status/{job_id}/',
            'note': 'Use the polling_url to check progress. Processing large files (100K+ records) may take several minutes.'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt  
@require_http_methods(["GET"])
def get_upload_status(request, job_id):
    """Get the status of an async upload job"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Get job status
        jobs_collection = get_processing_jobs_collection()
        job = jobs_collection.find_one({'job_id': job_id})

        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)

        # Return flat structure for frontend polling
        return JsonResponse({
            'success': True,
            'job_id': job.get('job_id'),
            'status': job.get('status'),
            'total_records': job.get('total_records', 0),
            'processed_records': job.get('processed_records', 0),
            'inserted_count': job.get('inserted_count', 0),
            'updated_count': job.get('updated_count', 0),
            'error_count': job.get('error_count', 0),
            'errors': job.get('errors', []),
            'percentage': job.get('percentage', 0),
            'original_filename': job.get('original_filename'),
            'created_at': str(job.get('created_at')) if job.get('created_at') else None,
            'started_at': str(job.get('started_at')) if job.get('started_at') else None,
            'completed_at': str(job.get('completed_at')) if job.get('completed_at') else None,
            # QR-specific fields
            'total_images': job.get('total_images', 0),
            'processed_images': job.get('processed_images', 0),
            'uploaded_count': job.get('uploaded_count', 0),
            'not_found_count': job.get('not_found_count', 0),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# QR CODE ASYNC UPLOAD ENDPOINTS (Unlimited timeout - same pattern as Excel)
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def upload_qr_async(request):
    """
    Asynchronously upload and process bulk QR code images (ZIP, PDF, or individual images)
    
    Supports:
    - ZIP files containing PNG/JPG images
    - PDF files with embedded images
    - Individual PNG/JPG/JPEG/GIF/WEBP images
    
    Filename matching (case-insensitive):
    - filename.png -> matches debtor with account_number=filename OR national_id=filename OR case_id=filename
    
    This endpoint:
    1. Quickly stages the file to S3 (fast, returns within 30s)
    2. Invokes the qrProcessor Lambda ASYNCHRONOUSLY (bypasses API Gateway 30s limit)
    3. Returns job_id immediately for status polling
    """
    import base64
    import boto3
    
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Parse JSON body
        data = json.loads(request.body)
        
        # Get base64 file data
        if 'file_data' not in data or 'filename' not in data:
            return JsonResponse({'error': 'Missing file_data or filename'}, status=400)

        original_filename = data['filename']
        file_data_b64 = data['file_data']

        # Decode base64 data
        try:
            file_content = base64.b64decode(file_data_b64)
        except Exception as e:
            return JsonResponse({'error': f'Invalid base64 data: {str(e)}'}, status=400)

        file_size = len(file_content)

        # Generate job ID for this upload
        job_id = f"QR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        # Determine file type
        file_lower = original_filename.lower()
        if file_lower.endswith('.zip'):
            file_type = 'zip'
            file_ext = '.zip'
        elif file_lower.endswith('.pdf'):
            file_type = 'pdf'
            file_ext = '.pdf'
        elif any(file_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']):
            file_type = 'image'
            file_ext = Path(original_filename).suffix.lower()
        else:
            return JsonResponse({
                'error': 'Unsupported file format. Please upload ZIP, PDF, PNG, JPG, JPEG, GIF, WEBP, or BMP files'
            }, status=400)

        # Save file to staging storage (S3)
        staging_filename = f"{job_id}{file_ext}"
        staging_key = f"qr_staging/{staging_filename}"
        storage.upload_file(file_content, staging_key, 'application/octet-stream')

        # Create job record with 'queued' status
        jobs_collection = get_processing_jobs_collection()
        job_record = {
            'job_id': job_id,
            'type': 'qr_upload',
            'status': 'queued',
            'original_filename': original_filename,
            'staged_filename': staging_filename,
            'file_size': file_size,
            'file_type': file_type,
            'staging_key': staging_key,
            'total_images': 0,
            'processed_images': 0,
            'uploaded_count': 0,
            'not_found_count': 0,
            'error_count': 0,
            'errors': [],
            'created_at': datetime.utcnow(),
            'created_by': payload.get('username', 'admin'),
            'started_at': None,
            'completed_at': None,
            'percentage': 0
        }
        jobs_collection.insert_one(job_record)

        # Invoke the qrProcessor Lambda ASYNCHRONOUSLY
        # For large ZIP files, we'll split into parallel chunks for faster processing
        try:
            lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
            
            stage = os.environ.get('STAGE', 'dev')
            processor_function_name = f"debtor-portal-api-{stage}-qrProcessor"
            
            # For ZIP files, extract image count and split into chunks
            chunk_size = 3000  # Process 3000 images per Lambda
            chunks_invoked = 0
            
            if file_type == 'zip':
                # Quick extraction of filenames only (no image data) to determine chunks
                import zipfile
                from io import BytesIO
                
                try:
                    with zipfile.ZipFile(BytesIO(file_content)) as zip_file:
                        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
                        image_filenames = [
                            name for name in zip_file.namelist()
                            if name.lower().endswith(image_extensions) and not name.startswith('__MACOSX')
                        ]
                        total_images = len(image_filenames)
                        
                        # Update job with total count
                        jobs_collection.update_one(
                            {'job_id': job_id},
                            {'$set': {'total_images': total_images}}
                        )
                        
                        # Calculate number of chunks
                        num_chunks = (total_images + chunk_size - 1) // chunk_size  # Ceiling division
                        
                        print(f"ZIP file has {total_images} images, splitting into {num_chunks} chunks of {chunk_size}")
                        
                        # Invoke parallel Lambdas for each chunk
                        for chunk_idx in range(num_chunks):
                            start_idx = chunk_idx * chunk_size
                            end_idx = min(start_idx + chunk_size, total_images)
                            
                            chunk_payload = {
                                'job_id': job_id,
                                'staging_key': staging_key,
                                'file_type': file_type,
                                'original_filename': original_filename,
                                'created_by': payload.get('username', 'admin'),
                                'start_index': start_idx,
                                'end_index': end_idx,
                                'chunk_id': chunk_idx + 1,
                                'total_chunks': num_chunks
                            }
                            
                            # Invoke asynchronously
                            lambda_client.invoke(
                                FunctionName=processor_function_name,
                                InvocationType='Event',
                                Payload=json.dumps(chunk_payload)
                            )
                            chunks_invoked += 1
                            
                        print(f"Invoked {chunks_invoked} parallel Lambda chunks for job {job_id}")
                        
                except Exception as zip_err:
                    print(f"Failed to extract ZIP filenames: {str(zip_err)}")
                    # Fallback: invoke single Lambda without chunks
                    processor_payload = {
                        'job_id': job_id,
                        'staging_key': staging_key,
                        'file_type': file_type,
                        'original_filename': original_filename,
                        'created_by': payload.get('username', 'admin')
                    }
                    lambda_client.invoke(
                        FunctionName=processor_function_name,
                        InvocationType='Event',
                        Payload=json.dumps(processor_payload)
                    )
                    chunks_invoked = 1
            else:
                # Non-ZIP files: single invocation
                processor_payload = {
                    'job_id': job_id,
                    'staging_key': staging_key,
                    'file_type': file_type,
                    'original_filename': original_filename,
                    'created_by': payload.get('username', 'admin')
                }
                lambda_client.invoke(
                    FunctionName=processor_function_name,
                    InvocationType='Event',
                    Payload=json.dumps(processor_payload)
                )
                chunks_invoked = 1
            
            print(f"QR async invocation triggered: {chunks_invoked} parallel chunks for job {job_id}")
            
        except Exception as lambda_err:
            print(f"QR Lambda invocation failed: {str(lambda_err)}")
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'failed',
                    'errors': [f'Failed to start processor: {str(lambda_err)}'],
                    'completed_at': datetime.utcnow()
                }}
            )
            return JsonResponse({
                'error': f'Failed to start background processor: {str(lambda_err)}'
            }, status=500)

        return JsonResponse({
            'success': True,
            'message': 'QR images received! Processing in background.',
            'job_id': job_id,
            'status': 'queued',
            'file_size': file_size,
            'file_type': file_type,
            'polling_url': f'/api/admin/qr-upload-status/{job_id}/',
            'note': 'Use the polling_url to check progress. Large ZIP files may take several minutes.'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_qr_presigned_url(request):
    """
    Get a presigned URL for uploading large QR files directly to S3
    Used for files > 10MB to bypass API Gateway payload limits
    """
    import boto3
    
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        data = json.loads(request.body)
        filename = data.get('filename')
        file_size = data.get('file_size', 0)
        content_type = data.get('content_type', 'application/octet-stream')
        
        if not filename:
            return JsonResponse({'error': 'filename is required'}, status=400)

        # Generate job ID
        job_id = f"QR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        # Determine file type
        file_lower = filename.lower()
        if file_lower.endswith('.zip'):
            file_type = 'zip'
            file_ext = '.zip'
        elif file_lower.endswith('.pdf'):
            file_type = 'pdf'
            file_ext = '.pdf'
        else:
            file_type = 'image'
            file_ext = Path(filename).suffix.lower() or '.png'

        staging_key = f"qr_staging/{job_id}{file_ext}"
        
        # Generate presigned URL
        s3_client = boto3.client('s3', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
        bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': staging_key,
                'ContentType': content_type
            },
            ExpiresIn=3600  # 1 hour
        )

        # Create job record
        jobs_collection = get_processing_jobs_collection()
        job_record = {
            'job_id': job_id,
            'type': 'qr_upload',
            'status': 'pending_upload',
            'original_filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'staging_key': staging_key,
            'total_images': 0,
            'processed_images': 0,
            'uploaded_count': 0,
            'not_found_count': 0,
            'error_count': 0,
            'errors': [],
            'created_at': datetime.utcnow(),
            'created_by': payload.get('username', 'admin'),
            'percentage': 0
        }
        jobs_collection.insert_one(job_record)

        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'upload_url': presigned_url,
            'staging_key': staging_key,
            'expires_in': 3600
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_qr_processing(request):
    """
    Start processing after file has been uploaded via presigned URL
    """
    import boto3
    
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        data = json.loads(request.body)
        job_id = data.get('job_id')
        
        if not job_id:
            return JsonResponse({'error': 'job_id is required'}, status=400)

        # Get job record
        jobs_collection = get_processing_jobs_collection()
        job = jobs_collection.find_one({'job_id': job_id})
        
        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)

        # Update status to queued
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {'status': 'queued'}}
        )

        # For ZIP files with parallel chunking support
        staging_key = job.get('staging_key')
        file_type = job.get('file_type')
        
        if file_type == 'zip':
            # Extract image count from ZIP to determine chunks
            import zipfile
            from io import BytesIO
            
            try:
                s3_client = boto3.client('s3', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
                bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
                
                # Download ZIP to count images
                response = s3_client.get_object(Bucket=bucket, Key=staging_key)
                zip_data = response['Body'].read()
                
                with zipfile.ZipFile(BytesIO(zip_data)) as zip_file:
                    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
                    image_filenames = [
                        name for name in zip_file.namelist()
                        if name.lower().endswith(image_extensions) and not name.startswith('__MACOSX')
                    ]
                    total_images = len(image_filenames)
                    
                    # Update total count
                    jobs_collection.update_one(
                        {'job_id': job_id},
                        {'$set': {'total_images': total_images}}
                    )
                    
                    # Calculate chunks
                    chunk_size = 3000
                    num_chunks = (total_images + chunk_size - 1) // chunk_size
                    
                    # Invoke parallel Lambda chunks
                    lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
                    stage = os.environ.get('STAGE', 'dev')
                    processor_function_name = f"debtor-portal-api-{stage}-qrProcessor"
                    
                    for chunk_idx in range(num_chunks):
                        start_idx = chunk_idx * chunk_size
                        end_idx = min(start_idx + chunk_size, total_images)
                        
                        chunk_payload = {
                            'job_id': job_id,
                            'staging_key': staging_key,
                            'file_type': file_type,
                            'original_filename': job.get('original_filename'),
                            'created_by': job.get('created_by', 'admin'),
                            'start_index': start_idx,
                            'end_index': end_idx,
                            'chunk_id': chunk_idx + 1,
                            'total_chunks': num_chunks
                        }
                        
                        lambda_client.invoke(
                            FunctionName=processor_function_name,
                            InvocationType='Event',
                            Payload=json.dumps(chunk_payload)
                        )
                    
                    print(f"Invoked {num_chunks} parallel Lambda chunks for {total_images} images")
                    
            except Exception as e:
                print(f"Error extracting ZIP: {str(e)}, falling back to single Lambda")
                # Fallback to single Lambda invocation
                lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
                stage = os.environ.get('STAGE', 'dev')
                processor_function_name = f"debtor-portal-api-{stage}-qrProcessor"
                
                processor_payload = {
                    'job_id': job_id,
                    'staging_key': staging_key,
                    'file_type': file_type,
                    'original_filename': job.get('original_filename'),
                    'created_by': job.get('created_by', 'admin')
                }
                
                lambda_client.invoke(
                    FunctionName=processor_function_name,
                    InvocationType='Event',
                    Payload=json.dumps(processor_payload)
                )
        else:
            # Non-ZIP files: single Lambda invocation
            lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
            stage = os.environ.get('STAGE', 'dev')
            processor_function_name = f"debtor-portal-api-{stage}-qrProcessor"
            
            processor_payload = {
                'job_id': job_id,
                'staging_key': staging_key,
                'file_type': file_type,
                'original_filename': job.get('original_filename'),
                'created_by': job.get('created_by', 'admin')
            }
            
            lambda_client.invoke(
                FunctionName=processor_function_name,
                InvocationType='Event',
                Payload=json.dumps(processor_payload)
            )

        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'status': 'queued',
            'message': 'Processing started'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_qr_upload_status(request, job_id):
    """Get the status of an async QR upload job"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        jobs_collection = get_processing_jobs_collection()
        job = jobs_collection.find_one({'job_id': job_id})

        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)

        return JsonResponse({
            'success': True,
            'job_id': job.get('job_id'),
            'status': job.get('status'),
            'total_images': job.get('total_images', 0),
            'processed_images': job.get('processed_images', 0),
            'uploaded_count': job.get('uploaded_count', 0),
            'not_found_count': job.get('not_found_count', 0),
            'skipped_count': job.get('skipped_count', 0),
            'error_count': job.get('error_count', 0),
            'errors': job.get('errors', []) if isinstance(job.get('errors'), list) else [],  # Always return array
            'percentage': job.get('percentage', 0),
            'original_filename': job.get('original_filename'),
            'file_type': job.get('file_type'),
            'created_at': str(job.get('created_at')) if job.get('created_at') else None,
            'started_at': str(job.get('started_at')) if job.get('started_at') else None,
            'completed_at': str(job.get('completed_at')) if job.get('completed_at') else None,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_debtors(request):
    """Get all debtors with pagination, search, and filtering (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))

        # Limit page size to prevent abuse
        page_size = min(page_size, 100)

        # Get search and filter parameters
        search = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')
        debt_type = request.GET.get('debt_type', '')
        upload_id = request.GET.get('upload_id', '')

        debtors = get_debtors_collection()

        # Build query
        query = {}

        # Text search across multiple fields
        if search:
            # Use regex for flexible search (works without text index too)
            search_regex = {'$regex': search, '$options': 'i'}
            query['$or'] = [
                {'account_number': search_regex},
                {'national_id': search_regex},
                {'name': search_regex},
                {'case_id': search_regex},
                {'email': search_regex},
                {'phone': search_regex},
            ]

        # Filter by debt type
        if debt_type:
            query['debt_type'] = debt_type

        # Filter by upload ID
        if upload_id:
            query['upload_id'] = upload_id

        # Get total count for pagination
        total_count = debtors.count_documents(query)
        total_pages = (total_count + page_size - 1) // page_size

        # Calculate total outstanding balance for all matching records (not just current page)
        total_outstanding_pipeline = [
            {'$match': query} if query else {'$match': {}},
            {'$group': {'_id': None, 'total': {'$sum': '$outstanding_balance'}}}
        ]
        total_outstanding_result = list(debtors.aggregate(total_outstanding_pipeline))
        total_outstanding_balance = total_outstanding_result[0]['total'] if total_outstanding_result else 0

        # Build sort
        sort_direction = -1 if sort_order == 'desc' else 1
        sort_field = sort_by if sort_by in ['created_at', 'updated_at', 'outstanding_balance', 'name', 'account_number', 'case_id'] else 'created_at'

        # Calculate skip value
        skip = (page - 1) * page_size

        # Execute query with pagination
        cursor = debtors.find(query, {'_id': 0}).sort(sort_field, sort_direction).skip(skip).limit(page_size)
        page_debtors = list(cursor)

        # Convert datetime objects to ISO format strings
        for debtor in page_debtors:
            if 'created_at' in debtor and debtor['created_at']:
                debtor['created_at'] = debtor['created_at'].isoformat()
            if 'updated_at' in debtor and debtor['updated_at']:
                debtor['updated_at'] = debtor['updated_at'].isoformat()

        return JsonResponse({
            'success': True,
            'debtors': page_debtors,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'total_outstanding_balance': total_outstanding_balance
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_debtor(request, account_number):
    """Delete a debtor (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        debtors = get_debtors_collection()
        result = debtors.delete_one({'account_number': account_number})

        if result.deleted_count > 0:
            return JsonResponse({'success': True, 'message': 'Debtor deleted successfully'})
        else:
            return JsonResponse({'error': 'Debtor not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def debtor_login(request):
    """Debtor login - send OTP to registered email (supports multiple login methods)"""
    try:
        data = json.loads(request.body)
        login_method = data.get('login_method', 'national_id')  # national_id, phone, email, account_number
        login_value = data.get('login_value') or data.get('national_id')  # Support both formats
        language = data.get('language', 'en')  # Get language preference from frontend

        if not login_value:
            error_messages = {
                'national_id': 'National ID is required',
                'phone': 'Phone number is required',
                'email': 'Email is required',
                'account_number': 'Account number is required'
            }
            return JsonResponse({'error': error_messages.get(login_method, 'Login value is required')}, status=400)

        debtors = get_debtors_collection()
        national_id = None
        debtor_list = []

        # Find accounts based on login method
        if login_method == 'national_id':
            national_id = login_value
            debtor_list = list(debtors.find({'national_id': national_id}))
        elif login_method == 'phone':
            debtor_list = list(debtors.find({'phone': login_value}))
            if debtor_list:
                national_id = debtor_list[0].get('national_id')
                # Get ALL accounts with this national_id
                if national_id:
                    debtor_list = list(debtors.find({'national_id': national_id}))
        elif login_method == 'email':
            debtor_list = list(debtors.find({'email': login_value}))
            if debtor_list:
                national_id = debtor_list[0].get('national_id')
                # Get ALL accounts with this national_id
                if national_id:
                    debtor_list = list(debtors.find({'national_id': national_id}))
        elif login_method == 'account_number':
            debtor = debtors.find_one({'account_number': login_value})
            if debtor:
                national_id = debtor.get('national_id')
                # Get ALL accounts with this national_id
                if national_id:
                    debtor_list = list(debtors.find({'national_id': national_id}))

        if not debtor_list:
            error_messages = {
                'national_id': 'No accounts found. Please check your National ID.',
                'phone': 'No accounts found. Please check your phone number.',
                'email': 'No accounts found. Please check your email address.',
                'account_number': 'No accounts found. Please check your account number.'
            }
            return JsonResponse({'error': error_messages.get(login_method, 'No accounts found.')}, status=404)

        # Get email for OTP from the first account (or any account with email)
        email = None
        for debtor in debtor_list:
            if debtor.get('email'):
                email = debtor.get('email')
                break

        if not email:
            return JsonResponse({'error': 'No email registered for your accounts. Please contact support.'}, status=400)

        # Generate OTP
        otp = generate_otp()

        # Store OTP in MongoDB (replaces in-memory storage for multi-worker support)
        otps = get_otp_collection()
        otps.update_one(
            {'national_id': national_id},
            {
                '$set': {
                    'national_id': national_id,
                    'otp': otp,
                    'email': email,
                    'created_at': datetime.utcnow()
                }
            },
            upsert=True
        )

        # Mask email for display (e.g., j***@email.com)
        email_parts = email.split('@')
        if len(email_parts) == 2 and len(email_parts[0]) > 2:
            masked_email = email_parts[0][:2] + '***@' + email_parts[1]
        else:
            masked_email = '***@***.***'

        # Send OTP via email Lambda (not Django send_mail)
        email_sent = False
        try:
            # Get debtor name from first account
            debtor_name = debtor_list[0].get('name', 'Customer') if debtor_list else 'Customer'
            
            # ✅ PRODUCTION MODE: Send OTP to debtor's actual email
            email_sent = send_otp_via_lambda(email, otp, debtor_name)
            
            if email_sent:
                print(f"✅ OTP email sent to debtor's email: {email} via Lambda")
            else:
                print(f"Failed to send OTP email to {email}")
                
        except Exception as email_error:
            print(f"Failed to send OTP email: {email_error}")
            import traceback
            traceback.print_exc()

        return JsonResponse({
            'success': True,
            'message': f'OTP sent to {masked_email}',
            'masked_email': masked_email,
            'national_id': national_id,
            'account_count': len(debtor_list),
            'email_sent': email_sent,
            'otp': otp if settings.DEBUG else None  # Show OTP in development mode only
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_otp(request):
    """Verify OTP and login debtor (returns all accounts for the national_id)"""
    try:
        data = json.loads(request.body)
        national_id = data.get('national_id')
        otp = data.get('otp')

        if not national_id or not otp:
            return JsonResponse({'error': 'National ID and OTP are required'}, status=400)

        # Check OTP from MongoDB
        otps = get_otp_collection()
        stored_otp_data = otps.find_one({'national_id': national_id})

        if not stored_otp_data:
            return JsonResponse({'error': 'OTP expired or not found. Please request a new OTP.'}, status=400)

        # Check if OTP has expired (5 minutes from creation)
        created_at = stored_otp_data.get('created_at')
        if created_at and datetime.utcnow() > created_at + timedelta(minutes=5):
            otps.delete_one({'national_id': national_id})
            return JsonResponse({'error': 'OTP expired. Please request a new OTP.'}, status=400)

        if stored_otp_data['otp'] != otp:
            return JsonResponse({'error': 'Invalid OTP'}, status=400)

        # Clear OTP after successful verification
        otps.delete_one({'national_id': national_id})

        # Get ALL debtor accounts for this national_id
        debtors = get_debtors_collection()
        debtor_list = list(debtors.find({'national_id': national_id}, {'_id': 0}))

        # Calculate total outstanding balance
        total_balance = sum(d.get('outstanding_balance', 0) for d in debtor_list)

        # Get account numbers for the token
        account_numbers = [d.get('account_number') for d in debtor_list]

        # Create token for debtor (24 hours expiry) with national_id
        token = create_jwt_token({
            'national_id': national_id,
            'account_numbers': account_numbers,
            'role': 'debtor'
        }, expires_hours=24)

        # Convert datetime objects to ISO format strings
        for debtor in debtor_list:
            if 'created_at' in debtor and debtor['created_at']:
                debtor['created_at'] = debtor['created_at'].isoformat()
            if 'updated_at' in debtor and debtor['updated_at']:
                debtor['updated_at'] = debtor['updated_at'].isoformat()

        # Check if PDPA consent has been given (check first account)
        pdpa_consent = debtor_list[0].get('pdpa_consent', False) if debtor_list else False
        pdpa_consent_date = debtor_list[0].get('pdpa_consent_date') if debtor_list else None
        if pdpa_consent_date:
            pdpa_consent_date = pdpa_consent_date.isoformat() if hasattr(pdpa_consent_date, 'isoformat') else pdpa_consent_date

        return JsonResponse({
            'success': True,
            'token': token,
            'national_id': national_id,
            'accounts': debtor_list,
            'account_count': len(debtor_list),
            'total_balance': total_balance,
            'pdpa_consent': pdpa_consent,
            'pdpa_consent_date': pdpa_consent_date
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_pdpa_consent(request):
    """Save PDPA consent for a debtor (all accounts under the national_id)"""
    try:
        # Verify debtor token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') != 'debtor':
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        national_id = payload.get('national_id')
        if not national_id:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # Update all accounts for this national_id with PDPA consent
        debtors = get_debtors_collection()
        consent_date = datetime.utcnow()

        result = debtors.update_many(
            {'national_id': national_id},
            {
                '$set': {
                    'pdpa_consent': True,
                    'pdpa_consent_date': consent_date,
                    'pdpa_consent_text': 'I hereby give my explicit consent to Power Asset Management Co., Ltd. to collect, use, disclose, and process my personal data for the purposes of debt management, payment processing, legal enforcement, regulatory compliance, and related activities in accordance with the Personal Data Protection Act B.E. 2562 (2019) and the Company\'s Privacy Notice.'
                }
            }
        )

        return JsonResponse({
            'success': True,
            'message': 'PDPA consent saved successfully',
            'accounts_updated': result.modified_count,
            'consent_date': consent_date.isoformat()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_payment_consent(request):
    """Save payment consent for a debtor before making payment"""
    try:
        # Verify debtor token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') != 'debtor':
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        national_id = payload.get('national_id')
        if not national_id:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # Update all accounts for this national_id with payment consent
        debtors = get_debtors_collection()
        consent_date = datetime.utcnow()

        # Store payment consent with timestamp
        result = debtors.update_many(
            {'national_id': national_id},
            {
                '$set': {
                    'payment_terms_consent': True,
                    'payment_terms_consent_date': consent_date,
                    'digital_receipt_consent': True,
                    'digital_receipt_consent_date': consent_date,
                    'payment_terms_text': 'I acknowledge and agree that this payment is made toward my outstanding debt under the above contract. This payment does not automatically constitute full settlement or legal closure unless expressly confirmed by the Asset Management Company in writing.',
                    'digital_receipt_text': 'I consent to receive my payment receipt, tax documents (if applicable), and related confirmations in electronic format. I acknowledge that such electronic documents shall be legally binding under the Electronic Transactions Act B.E. 2544 (2001).'
                }
            }
        )

        return JsonResponse({
            'success': True,
            'message': 'Payment consent saved successfully',
            'accounts_updated': result.modified_count,
            'consent_date': consent_date.isoformat()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_debtor_account(request, account_number):
    """Get debtor account details"""
    try:
        # Verify token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Check if user is authorized to access this account
        if payload.get('role') == 'debtor':
            # Check both old format (single account_number) and new format (account_numbers list)
            account_numbers = payload.get('account_numbers', [])
            single_account = payload.get('account_number')
            if single_account:
                account_numbers.append(single_account)

            if account_number not in account_numbers:
                return JsonResponse({'error': 'Unauthorized'}, status=401)

        debtors = get_debtors_collection()
        debtor = debtors.find_one({'account_number': account_number}, {'_id': 0})

        if not debtor:
            return JsonResponse({'error': 'Account not found'}, status=404)

        # Convert datetime objects to ISO format strings
        if 'created_at' in debtor and debtor['created_at']:
            debtor['created_at'] = debtor['created_at'].isoformat()
        if 'updated_at' in debtor and debtor['updated_at']:
            debtor['updated_at'] = debtor['updated_at'].isoformat()

        return JsonResponse({
            'success': True,
            'debtor': debtor
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_debtor_accounts(request):
    """Get all accounts for the logged-in debtor (by national_id)"""
    try:
        # Verify token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        if payload.get('role') != 'debtor':
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        national_id = payload.get('national_id')
        if not national_id:
            return JsonResponse({'error': 'Invalid token - missing national_id'}, status=401)

        debtors = get_debtors_collection()
        debtor_list = list(debtors.find({'national_id': national_id}, {'_id': 0}))

        # Calculate total outstanding balance
        total_balance = sum(d.get('outstanding_balance', 0) for d in debtor_list)

        # Convert datetime objects to ISO format strings
        for debtor in debtor_list:
            if 'created_at' in debtor and debtor['created_at']:
                debtor['created_at'] = debtor['created_at'].isoformat()
            if 'updated_at' in debtor and debtor['updated_at']:
                debtor['updated_at'] = debtor['updated_at'].isoformat()

        return JsonResponse({
            'success': True,
            'national_id': national_id,
            'accounts': debtor_list,
            'account_count': len(debtor_list),
            'total_balance': total_balance
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_debtor_contact(request, account_number):
    """Update debtor contact information (phone and/or email)"""
    try:
        # Verify token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Check if user is authorized to update this account
        if payload.get('role') == 'debtor':
            # Check both old format (single account_number) and new format (account_numbers list)
            account_numbers = payload.get('account_numbers', [])
            single_account = payload.get('account_number')
            if single_account:
                account_numbers.append(single_account)

            if account_number not in account_numbers:
                return JsonResponse({'error': 'Unauthorized'}, status=401)

        data = json.loads(request.body)
        phone = data.get('phone')
        email = data.get('email')

        if not phone and not email:
            return JsonResponse({'error': 'Phone or email is required'}, status=400)

        debtors = get_debtors_collection()

        # Build update object
        update_data = {'updated_at': datetime.utcnow()}
        if phone:
            update_data['phone'] = phone
        if email:
            update_data['email'] = email

        result = debtors.update_one(
            {'account_number': account_number},
            {'$set': update_data}
        )

        if result.matched_count == 0:
            return JsonResponse({'error': 'Account not found'}, status=404)

        # Fetch updated debtor data
        debtor = debtors.find_one({'account_number': account_number}, {'_id': 0})

        return JsonResponse({
            'success': True,
            'message': 'Contact information updated successfully',
            'debtor': debtor
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_receipt_filename_local(account_number, transaction_number):
    """Generate unique filename for payment receipt"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_account = account_number.replace('/', '_').replace('\\', '_')
    safe_trans = transaction_number.replace('/', '_').replace('\\', '_')[:20] if transaction_number else 'notrans'
    return f"receipt_{safe_account}_{safe_trans}_{timestamp}"


@csrf_exempt
@require_http_methods(["POST"])
def send_payment_interest_notification(request):
    """Send email notification when debtor submits a payment with transaction number and optional receipt"""
    try:
        # Verify token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Handle both JSON and multipart/form-data
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            # Form data with file upload
            account_number = request.POST.get('account_number')
            payment_type = request.POST.get('payment_type', 'N/A')
            payment_amount = parse_currency_value(request.POST.get('payment_amount', 0))
            transaction_number = request.POST.get('transaction_number', 'N/A')
            receipt_file = request.FILES.get('receipt')
            language = request.POST.get('language', 'en')  # Get language preference
        else:
            # JSON data
            data = json.loads(request.body)
            account_number = data.get('account_number')
            payment_type = data.get('payment_type', 'N/A')
            payment_amount = parse_currency_value(data.get('payment_amount', 0))
            transaction_number = data.get('installment_plan', 'N/A')
            receipt_file = None
            language = data.get('language', 'en')  # Get language preference

        if not account_number:
            return JsonResponse({'error': 'Account number is required'}, status=400)

        # Get debtor details
        debtors = get_debtors_collection()
        debtor = debtors.find_one({'account_number': account_number}, {'_id': 0})

        if not debtor:
            return JsonResponse({'error': 'Debtor not found'}, status=404)

        # Get recipient email from system settings
        system_settings = get_system_settings_collection()
        settings_doc = system_settings.find_one({'key': 'app_settings'})
        recipient_email = None
        if settings_doc:
            recipient_email = settings_doc.get('notification_email')

        # Fallback to Django settings if not configured in system settings
        if not recipient_email:
            recipient_email = getattr(settings, 'COLLECTIONS_TEAM_EMAIL', 'collections@example.com')

        # Prepare email content using language templates
        subject = get_email_template('payment_subject', language).format(
            account_number=account_number,
            transaction_number=transaction_number
        )

        email_body = get_email_template('payment_body', language).format(
            account_number=debtor.get('account_number', 'N/A'),
            name=debtor.get('name', 'N/A'),
            national_id=debtor.get('national_id', 'N/A'),
            phone=debtor.get('phone', 'N/A'),
            email=debtor.get('email', 'N/A'),
            original_creditor=debtor.get('original_creditor', 'N/A'),
            debt_type=debtor.get('debt_type', 'N/A'),
            outstanding_balance=format_thai_currency(debtor.get('outstanding_balance', 0)),
            loan_contract_date=debtor.get('loan_contract_date', 'N/A'),
            payment_type=payment_type,
            payment_amount=format_thai_currency(payment_amount),
            transaction_number=transaction_number,
            timestamp=get_bangkok_time()
        )

        # Try to send email
        try:
            # Debug: Log email settings
            print(f"=== EMAIL DEBUG ===")
            print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
            print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
            print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            print(f"Recipient: {recipient_email}")
            print(f"===================")

            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            email_sent = True
            email_message = f'Email notification sent to {recipient_email}'
            print(f"Email sent successfully to {recipient_email}")
        except Exception as email_error:
            # If email fails, log but don't fail the request
            email_sent = False
            email_message = f'Email could not be sent: {str(email_error)}'
            print(f"Email sending failed: {email_error}")
            import traceback
            traceback.print_exc()

        # Handle receipt file upload
        receipt_filename = None
        if receipt_file:
            try:
                # Generate unique filename
                file_ext = os.path.splitext(receipt_file.name)[1].lower()
                if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.webp']:
                    file_ext = '.jpg'  # Default extension
                base_filename = generate_receipt_filename_local(account_number, transaction_number)
                receipt_filename = f"{base_filename}{file_ext}"

                # Save to storage (S3 or local)
                receipt_key = get_receipt_key(receipt_filename)
                save_uploaded_file(receipt_file.read(), receipt_key)

                print(f"Receipt saved: {receipt_key}")
            except Exception as file_error:
                print(f"Failed to save receipt: {file_error}")
                receipt_filename = None

        # Log the payment in database (optional - for tracking)
        payment_log = {
            'account_number': account_number,
            'debtor_name': debtor.get('name'),
            'payment_type': payment_type,
            'payment_amount': payment_amount,
            'transaction_number': transaction_number,
            'email_sent': email_sent,
            'recipient_email': recipient_email,
            'receipt_filename': receipt_filename,
            'timestamp': datetime.utcnow()
        }

        # Create notification for admin portal (include receipt info)
        create_notification(
            notification_type='payment_submitted',
            title='Payment Submitted',
            message=f'{debtor.get("name", "A customer")} has submitted a payment with transaction #{transaction_number}.',
            debtor_data=debtor,
            metadata={
                'payment_type': payment_type,
                'payment_amount': payment_amount,
                'transaction_number': transaction_number,
                'receipt_filename': receipt_filename,
                'payment_terms_consent': debtor.get('payment_terms_consent', False),
                'payment_terms_consent_date': debtor.get('payment_terms_consent_date').isoformat() if debtor.get('payment_terms_consent_date') else None,
                'digital_receipt_consent': debtor.get('digital_receipt_consent', False),
                'digital_receipt_consent_date': debtor.get('digital_receipt_consent_date').isoformat() if debtor.get('digital_receipt_consent_date') else None,
            }
        )

        return JsonResponse({
            'success': True,
            'message': 'Payment recorded successfully',
            'email_sent': email_sent,
            'email_message': email_message,
            'receipt_saved': receipt_filename is not None,
            'log': {
                'account_number': account_number,
                'payment_type': payment_type,
                'payment_amount': payment_amount,
                'transaction_number': transaction_number,
                'receipt_filename': receipt_filename,
                'timestamp': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_not_ready_to_pay_notification(request):
    """Send email notification when debtor is not ready to pay"""
    try:
        # Verify token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        data = json.loads(request.body)
        account_number = data.get('account_number')
        reason = data.get('reason', 'Not specified')
        notes = data.get('notes', '')
        language = data.get('language', 'en')  # Get language preference
        preferred_contact_date = data.get('preferred_contact_date', '')
        preferred_contact_time = data.get('preferred_contact_time', '')
        preferred_contact_method = data.get('preferred_contact_method', '')
        preferred_contact_value = data.get('preferred_contact_value', '')
        instalment_plan = data.get('instalment_plan', '')

        if not account_number:
            return JsonResponse({'error': 'Account number is required'}, status=400)

        if not reason:
            return JsonResponse({'error': 'Reason for non-payment is required'}, status=400)

        # Get debtor details
        debtors = get_debtors_collection()
        debtor = debtors.find_one({'account_number': account_number}, {'_id': 0})

        if not debtor:
            return JsonResponse({'error': 'Debtor not found'}, status=404)

        # Prepare email content using language templates
        subject = get_email_template('not_ready_subject', language).format(
            account_number=account_number
        )

        no_notes_text = 'No additional notes provided.' if language == 'en' else 'ไม่มีหมายเหตุเพิ่มเติม'
        not_specified_text = 'Not specified' if language == 'en' else 'ไม่ระบุ'

        # Map contact time values to readable text
        time_labels = {
            'morning': 'Morning (9AM - 12PM)' if language == 'en' else 'ช่วงเช้า (9.00 - 12.00 น.)',
            'afternoon': 'Afternoon (12PM - 5PM)' if language == 'en' else 'ช่วงบ่าย (12.00 - 17.00 น.)',
            'evening': 'Evening (5PM - 8PM)' if language == 'en' else 'ช่วงเย็น (17.00 - 20.00 น.)',
            'anytime': 'Anytime' if language == 'en' else 'ติดต่อได้ทุกเวลา',
        }

        # Map contact method values to readable text
        method_labels = {
            'phone': 'Phone Call' if language == 'en' else 'โทรศัพท์',
            'email': 'Email' if language == 'en' else 'อีเมล',
        }

        # Format contact method with value if provided
        contact_method_display = method_labels.get(preferred_contact_method, not_specified_text)
        if preferred_contact_value and preferred_contact_method in ['phone', 'email']:
            contact_method_display = f"{contact_method_display}: {preferred_contact_value}"

        # Map instalment plan to readable text
        instalment_plan_display = instalment_plan if instalment_plan else not_specified_text

        email_body = get_email_template('not_ready_body', language).format(
            account_number=debtor.get('account_number', 'N/A'),
            name=debtor.get('name', 'N/A'),
            national_id=debtor.get('national_id', 'N/A'),
            phone=debtor.get('phone', 'N/A'),
            email=debtor.get('email', 'N/A'),
            original_creditor=debtor.get('original_creditor', 'N/A'),
            debt_type=debtor.get('debt_type', 'N/A'),
            outstanding_balance=format_thai_currency(debtor.get('outstanding_balance', 0)),
            loan_contract_date=debtor.get('loan_contract_date', 'N/A'),
            reason=reason,
            instalment_plan=instalment_plan_display,
            notes=notes if notes else no_notes_text,
            preferred_contact_date=preferred_contact_date if preferred_contact_date else not_specified_text,
            preferred_contact_time=time_labels.get(preferred_contact_time, not_specified_text),
            preferred_contact_method=contact_method_display,
            timestamp=get_bangkok_time()
        )

        # Get recipient email from system settings
        system_settings = get_system_settings_collection()
        settings_doc = system_settings.find_one({'key': 'app_settings'})
        recipient_email = None
        if settings_doc:
            recipient_email = settings_doc.get('notification_email')

        # Fallback to Django settings if not configured
        if not recipient_email:
            recipient_email = getattr(settings, 'COLLECTIONS_TEAM_EMAIL', 'collections@example.com')

        # Try to send email
        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            email_sent = True
            email_message = f'Email notification sent to {recipient_email}'
        except Exception as email_error:
            email_sent = False
            email_message = f'Email could not be sent: {str(email_error)}'
            print(f"Email sending failed: {email_error}")

        # Create notification for admin portal
        create_notification(
            notification_type='not_ready_to_pay',
            title='Need Support to Pay',
            message=f'{debtor.get("name", "A customer")} needs support to pay.',
            debtor_data=debtor,
            metadata={
                'reason': reason,
                'instalment_plan': instalment_plan,
                'notes': notes,
                'preferred_contact_date': preferred_contact_date,
                'preferred_contact_time': preferred_contact_time,
                'preferred_contact_method': preferred_contact_method,
                'preferred_contact_value': preferred_contact_value,
            }
        )

        return JsonResponse({
            'success': True,
            'message': 'Non-payment reason recorded successfully',
            'email_sent': email_sent,
            'email_message': email_message,
            'log': {
                'account_number': account_number,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_notifications(request):
    """Get all notifications for admin portal"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        notifications = get_notifications_collection()

        # Get all notifications sorted by created_at descending
        all_notifications = list(notifications.find().sort('created_at', -1).limit(50))

        # Convert ObjectId to string for JSON serialization
        for notification in all_notifications:
            notification['_id'] = str(notification['_id'])
            if 'created_at' in notification:
                notification['created_at'] = notification['created_at'].isoformat()

        # Count unread notifications
        unread_count = notifications.count_documents({'read': False})

        return JsonResponse({
            'success': True,
            'notifications': all_notifications,
            'unread_count': unread_count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        notifications = get_notifications_collection()

        result = notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'read': True}}
        )

        if result.matched_count == 0:
            return JsonResponse({'error': 'Notification not found'}, status=404)

        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        notifications = get_notifications_collection()

        result = notifications.update_many(
            {'read': False},
            {'$set': {'read': True}}
        )

        return JsonResponse({
            'success': True,
            'message': f'{result.modified_count} notifications marked as read'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_qr_code(request):
    """Upload LINE QR code image (multipart form data)"""
    try:
        print(f"[DEBUG] QR Upload - Content-Type: {request.content_type}")
        
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized - Missing authorization header'}, status=401)

        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Check if file is in request
        if 'qr_image' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)

        file = request.FILES['qr_image']
        
        # Validate file
        if not file.name:
            return JsonResponse({'error': 'No file selected'}, status=400)

        # Validate file type
        allowed_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']
        file_extension = file.name.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'
            }, status=400)

        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File too large. Maximum size is 5MB'}, status=400)

        # Read file content
        file_content = file.read()
        
        # Determine content type
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg', 
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        content_type = content_type_map.get(file_extension, 'image/jpeg')

        # Connect to MongoDB and save QR code
        settings_collection = get_settings_collection()
        
        # Create QR document
        qr_document = {
            'qr_image_data': file_content,
            'content_type': content_type,
            'filename': file.name,
            'upload_date': datetime.datetime.utcnow()
        }
        
        # Update or insert QR code setting
        result = settings_collection.update_one(
            {'key': 'line_qr_code'},
            {'$set': {'value': qr_document}},
            upsert=True
        )

        print(f"[DEBUG] QR Upload Success - File: {file.name}, Size: {file.size}, Type: {content_type}")
        
        return JsonResponse({
            'success': True,
            'message': 'QR code uploaded successfully',
            'filename': file.name,
            'size': file.size,
            'content_type': content_type
        })

    except Exception as e:
        print(f"[ERROR] QR Upload Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_qr_code_base64(request):
    """Upload LINE QR code image using base64 encoding (more reliable for Lambda)"""
    try:
        print(f"[DEBUG] QR Upload Base64 - Content-Type: {request.content_type}")
        
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized - Missing authorization header'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            print(f"[DEBUG] QR Upload Base64 - Invalid token or role: {payload}")
            return JsonResponse({'error': 'Unauthorized - Invalid token or permissions'}, status=401)

        # Parse JSON body
        data = json.loads(request.body)
        
        if 'file_data' not in data or 'filename' not in data:
            return JsonResponse({'error': 'Missing file_data or filename'}, status=400)

        filename = data['filename'].lower()
        file_data_b64 = data['file_data']
        
        print(f"[DEBUG] QR Upload Base64 - Processing: {filename}, data length: {len(file_data_b64)}")

        # Validate file type - accept both JPG and PNG
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
        file_extension = None
        for ext in valid_extensions:
            if filename.endswith(ext):
                file_extension = ext
                break
        
        if not file_extension:
            return JsonResponse({
                'error': 'Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, WEBP, BMP)',
                'accepted_formats': valid_extensions
            }, status=400)

        # Validate base64 data
        try:
            file_content = base64.b64decode(file_data_b64)
            if len(file_content) == 0:
                return JsonResponse({'error': 'Empty file data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Invalid base64 data: {str(e)}'}, status=400)

        # Determine content type based on file extension
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg', 
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        content_type = content_type_map.get(file_extension, 'image/png')

        print(f"[DEBUG] QR Upload Base64 - File size: {len(file_content)} bytes, type: {content_type}")

        # Store in settings collection
        settings = get_settings_collection()
        result = settings.update_one(
            {'key': 'line_qr_code'},
            {
                '$set': {
                    'key': 'line_qr_code',
                    'value': file_data_b64,  # Store the base64 data directly
                    'content_type': content_type,
                    'filename': data['filename'],
                    'size': len(file_content),
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )

        print(f"[DEBUG] QR Upload Base64 - Database update: modified={result.modified_count}, upserted={result.upserted_id}")

        return JsonResponse({
            'success': True,
            'message': 'QR code uploaded successfully',
            'filename': data['filename'],
            'size': len(file_content),
            'content_type': content_type
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"[ERROR] QR Upload Base64 failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)
    """Upload LINE QR code image (admin only)"""
    try:
        print(f"[DEBUG] QR Upload - Content-Type: {request.content_type}")
        print(f"[DEBUG] QR Upload - FILES: {list(request.FILES.keys())}")
        print(f"[DEBUG] QR Upload - POST: {list(request.POST.keys())}")
        
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            print(f"[DEBUG] QR Upload - Missing or invalid auth header: {auth_header}")
            return JsonResponse({'error': 'Unauthorized - Missing or invalid authorization header'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            print(f"[DEBUG] QR Upload - Invalid token payload: {payload}")
            return JsonResponse({'error': 'Unauthorized - Invalid token or insufficient permissions'}, status=401)

        # Get uploaded file
        if 'file' not in request.FILES:
            print(f"[DEBUG] QR Upload - No file in request.FILES. Available keys: {list(request.FILES.keys())}")
            return JsonResponse({
                'error': 'No file uploaded',
                'debug': {
                    'content_type': request.content_type,
                    'files_keys': list(request.FILES.keys()),
                    'post_keys': list(request.POST.keys())
                }
            }, status=400)

        file = request.FILES['file']
        filename = file.name.lower()
        
        print(f"[DEBUG] QR Upload - File received: {file.name}, size: {file.size}")

        # Validate file type - accept both JPG and PNG
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
        file_extension = None
        for ext in valid_extensions:
            if filename.endswith(ext):
                file_extension = ext
                break
        
        if not file_extension:
            return JsonResponse({
                'error': 'Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, WEBP, BMP)',
                'accepted_formats': valid_extensions
            }, status=400)

        # Read and encode file as base64
        file_content = file.read()
        if len(file_content) == 0:
            return JsonResponse({'error': 'Empty file uploaded'}, status=400)
            
        base64_image = base64.b64encode(file_content).decode('utf-8')

        # Determine content type based on file extension
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg', 
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        content_type = content_type_map.get(file_extension, file.content_type or 'image/png')
        
        print(f"[DEBUG] QR Upload - Processing file: {content_type}, base64 length: {len(base64_image)}")

        # Store in settings collection
        settings = get_settings_collection()
        result = settings.update_one(
            {'key': 'line_qr_code'},
            {
                '$set': {
                    'key': 'line_qr_code',
                    'value': base64_image,
                    'content_type': content_type,
                    'filename': file.name,
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )
        
        print(f"[DEBUG] QR Upload - Database update result: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id}")

        return JsonResponse({
            'success': True,
            'message': 'QR code uploaded successfully'
        })

    except Exception as e:
        print(f"[ERROR] QR Upload failed: {str(e)}")
        return JsonResponse({'error': f'QR upload failed: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_qr_code(request):
    """Get LINE QR code image (public endpoint for debtors)"""
    try:
        settings = get_settings_collection()
        qr_setting = settings.find_one({'key': 'line_qr_code'})

        if not qr_setting:
            return JsonResponse({
                'success': True,
                'qr_code': None,
                'message': 'No QR code configured'
            })

        return JsonResponse({
            'success': True,
            'qr_code': {
                'image': qr_setting.get('value'),
                'content_type': qr_setting.get('content_type', 'image/png'),
                'filename': qr_setting.get('filename', 'qr_code.png')
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_qr_code(request):
    """Delete LINE QR code image (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        settings = get_settings_collection()
        result = settings.delete_one({'key': 'line_qr_code'})

        if result.deleted_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'QR code deleted successfully'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'No QR code to delete'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Enhanced QR Processing Endpoints

@csrf_exempt
@require_http_methods(["POST"])
def process_qr_codes(request):
    """
    Enhanced QR code processing endpoint
    Accepts multiple image files and extracts QR codes with analysis
    """
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        if not request.FILES:
            return JsonResponse({'error': 'No files uploaded'}, status=400)

        results = []
        total_files = len(request.FILES)
        total_qr_found = 0

        for file_key, uploaded_file in request.FILES.items():
            filename = uploaded_file.name
            
            try:
                # Read file content
                file_content = uploaded_file.read()
                
                # Process QR codes with production processor if available
                if PRODUCTION_QR_AVAILABLE:
                    # Validate image first
                    validation = RobustQRProcessor.validate_image_input(file_content, filename)
                    
                    if validation['valid']:
                        # Try to enhance image for better QR detection
                        enhanced_content = RobustQRProcessor.enhance_image_for_processing(file_content, 'medium')
                        
                        # Process both original and enhanced versions
                        result = {
                            'success': True,
                            'filename': filename,
                            'file_size': len(file_content),
                            'image_info': validation['details'],
                            'processing_method': 'production_qr',
                            'enhancement_applied': len(enhanced_content) != len(file_content),
                            'qr_detection': 'QR detection requires specialized OCR service in Lambda environment',
                            'recommendation': 'Use generate_thai_payment_qr endpoint for creating payment QR codes'
                        }
                    else:
                        result = {
                            'success': False,
                            'filename': filename,
                            'file_size': len(file_content),
                            'error': validation['error'],
                            'processing_method': 'production_qr_validation_failed'
                        }
                else:
                    # Fallback to Lambda processor
                    result = LambdaQRProcessor.process_image_for_qr_info(file_content, filename)
                
                # Add filename to result
                result['filename'] = filename
                result['file_size'] = len(file_content)
                
                # Enhanced image processing results
                if result['success']:
                    total_qr_found += 1  # Count successful processing
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e),
                    'qr_codes': []
                })

        return JsonResponse({
            'success': True,
            'message': f'Processed {total_files} files, found {total_qr_found} QR codes',
            'summary': {
                'total_files': total_files,
                'total_qr_found': total_qr_found,
                'successful_files': len([r for r in results if r['success']]),
                'failed_files': len([r for r in results if not r['success']])
            },
            'results': results
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def extract_qr_from_image(request):
    """
    Extract QR code from single image with enhancement options
    """
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Handle file upload or base64 data
        if 'file' in request.FILES:
            file = request.FILES['file']
            filename = file.name
            file_content = file.read()
        elif request.content_type == 'application/json':
            data = json.loads(request.body)
            file_content = base64.b64decode(data.get('image_data', ''))
            filename = data.get('filename', 'uploaded_image.png')
        else:
            return JsonResponse({'error': 'No image data provided'}, status=400)

        # Process image for QR analysis
        result = LambdaQRProcessor.process_image_for_qr_info(file_content, filename)
        
        # Add enhanced image as base64 if processing was successful
        if result['success'] and result.get('enhanced_image_data'):
            result['enhanced_image_base64'] = base64.b64encode(result['enhanced_image_data']).decode('utf-8')
            del result['enhanced_image_data']  # Remove binary data

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_payment_qr(request):
    """
    Generate payment QR code for debt collection
    """
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        data = json.loads(request.body)
        
        # Required fields
        account_number = data.get('account_number')
        amount = data.get('amount')
        
        if not account_number:
            return JsonResponse({'error': 'Account number is required'}, status=400)
        
        # Get account details
        debtors = get_debtors_collection()
        debtor = debtors.find_one({'account_number': account_number})
        
        if not debtor:
            return JsonResponse({'error': f'Account {account_number} not found'}, status=404)

        # Prepare QR data
        if amount:
            qr_text = f"Payment for Account: {account_number}\nName: {debtor.get('name', '')}\nAmount: ฿{amount:,.2f}\nRef: {debtor.get('case_id', '')}"
        else:
            qr_text = f"Account: {account_number}\nName: {debtor.get('name', '')}\nBalance: ฿{debtor.get('outstanding_balance', 0):,.2f}\nRef: {debtor.get('case_id', '')}"
        
        # Generate payment QR code
        qr_result = PaymentQRGenerator.create_payment_qr(
            account_number=account_number,
            debtor_name=debtor.get('name', ''),
            amount=amount,
            case_id=debtor.get('case_id'),
            bank_info="PowerAMC Collection"
        )
        
        if not qr_result['success']:
            return JsonResponse({'error': f"QR generation failed: {qr_result['error']}"}, status=500)
        
        qr_base64 = qr_result['qr_image_base64']
        qr_text = qr_result['qr_text']
        
        # Store QR code info (use system settings for now)
        settings = get_settings_collection()
        qr_id = f"QR-{account_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        qr_record = {
            'key': f'payment_qr_{qr_id}',
            'qr_id': qr_id,
            'account_number': account_number,
            'debtor_name': debtor.get('name', ''),
            'amount': amount,
            'qr_data': qr_text,
            'qr_image_base64': qr_base64,
            'created_by': payload.get('username'),
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        settings.insert_one(qr_record)
        
        return JsonResponse({
            'success': True,
            'qr_id': qr_id,
            'qr_image_base64': qr_base64,
            'qr_data': qr_text,
            'account_info': {
                'account_number': account_number,
                'name': debtor.get('name'),
                'case_id': debtor.get('case_id'),
                'outstanding_balance': debtor.get('outstanding_balance')
            },
            'message': 'Payment QR code generated successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_upload_history(request):
    """Get upload history (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        upload_history = get_upload_history_collection()

        # Get all upload history sorted by uploaded_at descending (exclude file_content)
        history_records = list(upload_history.find(
            {},
            {'file_content': 0}  # Exclude file content from listing
        ).sort('uploaded_at', -1).limit(100))

        # Convert ObjectId to string for JSON serialization
        for record in history_records:
            record['_id'] = str(record['_id'])
            if 'uploaded_at' in record:
                record['uploaded_at'] = record['uploaded_at'].isoformat()

        return JsonResponse({
            'success': True,
            'history': history_records,
            'count': len(history_records)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def download_upload_file(request, upload_id):
    """Download a previously uploaded file (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        upload_history = get_upload_history_collection()

        # Find the upload record
        record = upload_history.find_one({'_id': ObjectId(upload_id)})

        if not record:
            return JsonResponse({'error': 'File not found'}, status=404)

        # Check for file path (new system) or file_content (legacy)
        if 'saved_filename' in record:
            # Storage-based file system (S3 or local)
            upload_key = get_upload_key(record['saved_filename'])
            try:
                file_data = get_file(upload_key)
                file_content = base64.b64encode(file_data).decode('utf-8')
                return JsonResponse({
                    'success': True,
                    'filename': record.get('filename', 'download.xlsx'),
                    'content_type': record.get('content_type', 'application/octet-stream'),
                    'file_content': file_content
                })
            except Exception:
                return JsonResponse({'error': 'File not found in storage'}, status=404)
        elif 'file_content' in record:
            # Legacy base64 storage (for backwards compatibility)
            return JsonResponse({
                'success': True,
                'filename': record.get('filename', 'download.xlsx'),
                'content_type': record.get('content_type', 'application/octet-stream'),
                'file_content': record['file_content']
            })
        else:
            return JsonResponse({'error': 'File content not available'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# SUPER ADMIN ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def get_system_settings(request):
    """Get system settings (public endpoint for frontend configuration)"""
    try:
        system_settings = get_system_settings_collection()
        settings_doc = system_settings.find_one({'key': 'app_settings'}, {'_id': 0, 'key': 0})

        if not settings_doc:
            # Return default settings if none exist
            settings_doc = {
                'admin_tabs': {
                    'upload_data': True,
                    'view_accounts': True,
                    'debtor_requests': True,
                    'upload_history': True,
                    'settings': True,
                },
                'enable_image_upload': False,
                'debtor_features': {
                    'make_payment': True,
                    'not_ready_to_pay': True,
                    'line_qr_support': True,
                    'update_contact': True,
                },
                'notification_email': '',
                'bank_account': {
                    'bank_name': '',
                    'account_name': '',
                    'account_number': '',
                    'promptpay_id': '',
                },
                'admin_filters': {
                    'type_filter': True,
                    'status_filter': True,
                },
                'table_actions': {
                    'view_accounts': True,
                    'debtor_requests': True,
                    'upload_history': True,
                },
                'maintenance_mode': {
                    'enabled': False,
                    'title': '',
                    'message': '',
                    'estimated_time': '',
                },
            }

        # Convert datetime to ISO format if exists
        if 'updated_at' in settings_doc and settings_doc['updated_at']:
            settings_doc['updated_at'] = settings_doc['updated_at'].isoformat()

        return JsonResponse({
            'success': True,
            'settings': settings_doc
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_system_settings(request):
    """Update system settings (super admin only)"""
    try:
        # Verify super admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') != 'super_admin':
            return JsonResponse({'error': 'Super admin access required'}, status=403)

        data = json.loads(request.body)
        print(f"Received settings update: {data}")  # Debug log

        system_settings = get_system_settings_collection()

        # Get existing settings first
        existing = system_settings.find_one({'key': 'app_settings'})

        # Build update object with proper merging
        update_data = {
            'key': 'app_settings',
            'updated_at': datetime.utcnow()
        }

        # Update admin tabs - merge with existing or use provided
        if 'admin_tabs' in data:
            existing_tabs = existing.get('admin_tabs', {}) if existing else {}
            update_data['admin_tabs'] = {**existing_tabs, **data['admin_tabs']}
        elif existing and 'admin_tabs' in existing:
            update_data['admin_tabs'] = existing['admin_tabs']

        # Update image upload setting if provided
        if 'enable_image_upload' in data:
            update_data['enable_image_upload'] = data['enable_image_upload']
        elif existing:
            update_data['enable_image_upload'] = existing.get('enable_image_upload', False)

        # Update admin OTP setting if provided
        if 'admin_otp_enabled' in data:
            update_data['admin_otp_enabled'] = data['admin_otp_enabled']
        elif existing:
            update_data['admin_otp_enabled'] = existing.get('admin_otp_enabled', False)

        # Update debtor features - merge with existing or use provided
        if 'debtor_features' in data:
            existing_features = existing.get('debtor_features', {}) if existing else {}
            update_data['debtor_features'] = {**existing_features, **data['debtor_features']}
        elif existing and 'debtor_features' in existing:
            update_data['debtor_features'] = existing['debtor_features']

        # Update notification email
        if 'notification_email' in data:
            update_data['notification_email'] = data['notification_email']
        elif existing and 'notification_email' in existing:
            update_data['notification_email'] = existing['notification_email']

        # Update bank account details
        if 'bank_account' in data:
            existing_bank = existing.get('bank_account', {}) if existing else {}
            update_data['bank_account'] = {**existing_bank, **data['bank_account']}
        elif existing and 'bank_account' in existing:
            update_data['bank_account'] = existing['bank_account']

        # Update admin filters settings
        if 'admin_filters' in data:
            existing_filters = existing.get('admin_filters', {}) if existing else {}
            update_data['admin_filters'] = {**existing_filters, **data['admin_filters']}
        elif existing and 'admin_filters' in existing:
            update_data['admin_filters'] = existing['admin_filters']

        # Update table action column settings
        if 'table_actions' in data:
            existing_table_actions = existing.get('table_actions', {}) if existing else {}
            update_data['table_actions'] = {**existing_table_actions, **data['table_actions']}
        elif existing and 'table_actions' in existing:
            update_data['table_actions'] = existing['table_actions']

        # Update table columns visibility settings
        if 'table_columns' in data:
            existing_table_columns = existing.get('table_columns', {}) if existing else {}
            # Deep merge for nested structure (table_name -> column_name -> boolean)
            merged_table_columns = {**existing_table_columns}
            for table_name, columns in data['table_columns'].items():
                if table_name in merged_table_columns:
                    merged_table_columns[table_name] = {**merged_table_columns[table_name], **columns}
                else:
                    merged_table_columns[table_name] = columns
            update_data['table_columns'] = merged_table_columns
        elif existing and 'table_columns' in existing:
            update_data['table_columns'] = existing['table_columns']

        # Update maintenance mode settings
        if 'maintenance_mode' in data:
            existing_maintenance = existing.get('maintenance_mode', {}) if existing else {}
            update_data['maintenance_mode'] = {**existing_maintenance, **data['maintenance_mode']}
        elif existing and 'maintenance_mode' in existing:
            update_data['maintenance_mode'] = existing['maintenance_mode']

        print(f"Saving settings: {update_data}")  # Debug log

        result = system_settings.replace_one(
            {'key': 'app_settings'},
            update_data,
            upsert=True
        )

        print(f"Save result: matched={result.matched_count}, modified={result.modified_count}")  # Debug log

        return JsonResponse({
            'success': True,
            'message': 'System settings updated successfully'
        })

    except Exception as e:
        print(f"Error saving settings: {str(e)}")  # Debug log
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# ADMIN USER MANAGEMENT (Super Admin Only)
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def get_admin_users(request):
    """Get list of all admin users (super admin only)"""
    try:
        # Verify super admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') != 'super_admin':
            return JsonResponse({'error': 'Super admin access required'}, status=403)

        admins = get_admins_collection()
        admin_list = list(admins.find({}, {'_id': 0, 'password': 0, 'otp': 0, 'otp_expiry': 0}))

        return JsonResponse({
            'success': True,
            'admins': admin_list
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def change_admin_password(request):
    """Allow admin to change their own password"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        username = payload.get('username')
        if not username:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return JsonResponse({'error': 'Current password and new password are required'}, status=400)

        if len(new_password) < 6:
            return JsonResponse({'error': 'New password must be at least 6 characters'}, status=400)

        admins = get_admins_collection()
        admin = admins.find_one({'username': username})

        if not admin:
            return JsonResponse({'error': 'Admin user not found'}, status=404)

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), admin['password'].encode('utf-8')):
            return JsonResponse({'error': 'Current password is incorrect'}, status=400)

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update the password
        admins.update_one(
            {'username': username},
            {'$set': {'password': hashed_password.decode('utf-8')}}
        )

        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reset_admin_password(request, username):
    """Reset password for an admin user (super admin only)"""
    try:
        # Verify super admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') != 'super_admin':
            return JsonResponse({'error': 'Super admin access required'}, status=403)

        data = json.loads(request.body)
        new_password = data.get('new_password')

        if not new_password:
            return JsonResponse({'error': 'New password is required'}, status=400)

        if len(new_password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters'}, status=400)

        admins = get_admins_collection()
        admin = admins.find_one({'username': username})

        if not admin:
            return JsonResponse({'error': 'Admin user not found'}, status=404)

        # Prevent resetting super_admin password through this endpoint
        if admin.get('role') == 'super_admin':
            return JsonResponse({'error': 'Cannot reset super admin password through this endpoint'}, status=403)

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update the password
        admins.update_one(
            {'username': username},
            {'$set': {'password': hashed_password.decode('utf-8')}}
        )

        return JsonResponse({
            'success': True,
            'message': f'Password for {username} has been reset successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# PAYMENT RECEIPT ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def serve_payment_receipt(request, filename):
    """Serve payment receipt file (admin only)"""
    try:
        # Verify token - admin only
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Only admin or super_admin can view receipts
        if payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized - Admin access required'}, status=401)

        # Try to get receipt from storage
        receipt_key = get_receipt_key(filename)
        print(f"Looking for receipt at key: {receipt_key}")

        try:
            file_data = get_file(receipt_key)
        except Exception as e:
            # Try without extension as fallback
            base_name = os.path.splitext(filename)[0]
            print(f"Primary key not found, trying variations for: {base_name}")

            # Try common extensions
            found = False
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf']:
                try:
                    test_key = get_receipt_key(f"{base_name}{ext}")
                    file_data = get_file(test_key)
                    filename = f"{base_name}{ext}"
                    found = True
                    print(f"Found receipt with extension: {ext}")
                    break
                except Exception:
                    continue

            if not found:
                print(f"Receipt not found: {filename}")
                return JsonResponse({'error': f'Receipt not found: {filename}'}, status=404)

        # Determine content type based on extension or default to PNG
        file_ext = os.path.splitext(filename)[1].lower()
        print(f"File extension: '{file_ext}'")

        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
        }

        # Default to PNG for images without extension
        content_type = content_types.get(file_ext, 'image/png')
        print(f"Content type: {content_type}")

        print(f"Serving receipt: {filename}, size: {len(file_data)} bytes")
        response = HttpResponse(file_data, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        import traceback
        print(f"Error serving receipt: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# TEST EMAIL ENDPOINT
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def test_email(request):
    """Test endpoint to verify email configuration"""
    try:
        # Get recipient email from query params or use default
        recipient = request.GET.get('email')

        if not recipient:
            # Try system settings first
            system_settings = get_system_settings_collection()
            settings_doc = system_settings.find_one({'key': 'app_settings'})
            if settings_doc:
                recipient = settings_doc.get('notification_email')

            # Fallback to Django settings
            if not recipient:
                recipient = getattr(settings, 'COLLECTIONS_TEAM_EMAIL', None)

        if not recipient:
            return JsonResponse({
                'success': False,
                'error': 'No recipient email configured. Set notification_email in SuperAdmin or pass ?email=your@email.com'
            }, status=400)

        # Log email settings for debugging
        email_config = {
            'EMAIL_HOST': settings.EMAIL_HOST,
            'EMAIL_PORT': settings.EMAIL_PORT,
            'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
            'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
            'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            'recipient': recipient,
        }

        print(f"=== TEST EMAIL CONFIG ===")
        for key, value in email_config.items():
            print(f"{key}: {value}")
        print(f"=========================")

        # Try to send test email
        send_mail(
            subject='Test Email from Customer Portal',
            message=f'''This is a test email from the Customer Portal.

If you received this email, your email configuration is working correctly.

Email Settings:
- Host: {settings.EMAIL_HOST}
- Port: {settings.EMAIL_PORT}
- TLS: {settings.EMAIL_USE_TLS}
- From: {settings.DEFAULT_FROM_EMAIL}

Timestamp: {get_bangkok_time()} (Bangkok)
''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )

        return JsonResponse({
            'success': True,
            'message': f'Test email sent successfully to {recipient}',
            'config': email_config
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Test email failed: {error_details}")

        return JsonResponse({
            'success': False,
            'error': str(e),
            'details': error_details,
            'config': {
                'EMAIL_HOST': settings.EMAIL_HOST,
                'EMAIL_PORT': settings.EMAIL_PORT,
                'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
                'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
                'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            }
        }, status=500)


# ============================================
# DEBTOR IMAGES ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def upload_debtor_images(request):
    """Upload debtor images or PDF files with QR codes to file system (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Get uploaded files
        files = request.FILES.getlist('images')

        if not files:
            return JsonResponse({'error': 'No files uploaded'}, status=400)

        debtor_images = get_debtor_images_collection()
        debtors = get_debtors_collection()

        uploaded_count = 0
        not_found_count = 0
        pdf_extracted_count = 0
        errors = []

        valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

        for file in files:
            filename = file.name

            # Check if it's a PDF file
            if filename.lower().endswith('.pdf'):
                # Process PDF to extract QR codes
                if not PDF_PROCESSING_AVAILABLE:
                    errors.append(f'{filename}: PDF processing not available (install required libraries)')
                    continue

                print(f"Processing PDF file: {filename}")
                qr_results, pdf_errors = process_pdf_for_qr(file, filename)
                errors.extend(pdf_errors)

                for account_number, qr_bytes in qr_results:
                    # Check if debtor exists
                    debtor = debtors.find_one({'account_number': account_number})
                    if not debtor:
                        not_found_count += 1
                        errors.append(f'{filename}: Account {account_number} not found in database')
                        continue

                    # Save QR image to storage (PNG format for better quality)
                    safe_filename = f"{account_number}.png"

                    # Delete existing images with different extensions
                    for old_ext in valid_image_extensions:
                        if old_ext != '.png':
                            remove_debtor_image_from_storage(account_number, old_ext.lstrip('.'))

                    # Save to storage (S3 or local)
                    image_result = save_debtor_image(account_number, qr_bytes, 'png')
                    image_key = image_result.get('key', get_image_key(account_number, 'png'))

                    # Store metadata in MongoDB
                    debtor_images.update_one(
                        {'account_number': account_number},
                        {
                            '$set': {
                                'account_number': account_number,
                                'filename': safe_filename,
                                'content_type': 'image/png',
                                'storage_key': image_key,
                                'uploaded_by': payload.get('username', 'admin'),
                                'uploaded_at': datetime.utcnow(),
                                'source': 'pdf_extraction',
                                'source_file': filename
                            }
                        },
                        upsert=True
                    )
                    pdf_extracted_count += 1
                    uploaded_count += 1

                # Force garbage collection after each PDF to prevent memory buildup
                gc.collect()
                continue

            # Regular image file processing
            # Extract account number from filename (remove extension)
            account_number = filename.rsplit('.', 1)[0].strip()

            # Validate file type
            file_ext = None
            for ext in valid_image_extensions:
                if filename.lower().endswith(ext):
                    file_ext = ext
                    break

            if not file_ext:
                errors.append(f'{filename}: Invalid file type (use PNG, JPG, GIF, WEBP, or PDF)')
                continue

            # Check if debtor exists
            debtor = debtors.find_one({'account_number': account_number})
            if not debtor:
                not_found_count += 1
                errors.append(f'{filename}: Account {account_number} not found')
                continue

            # Determine content type
            content_type = file.content_type or 'image/png'

            # Create safe filename (account_number + extension)
            safe_filename = f"{account_number}{file_ext}"
            extension = file_ext.lstrip('.')

            # Delete existing images with different extensions
            for old_ext in valid_image_extensions:
                if old_ext != file_ext:
                    remove_debtor_image_from_storage(account_number, old_ext.lstrip('.'))

            # Save file to storage (S3 or local)
            file_data = file.read()
            image_result = save_debtor_image(account_number, file_data, extension)
            image_key = image_result.get('key', get_image_key(account_number, extension))

            # Store metadata in MongoDB (not the image itself)
            debtor_images.update_one(
                {'account_number': account_number},
                {
                    '$set': {
                        'account_number': account_number,
                        'filename': safe_filename,
                        'content_type': content_type,
                        'storage_key': image_key,
                        'uploaded_by': payload.get('username', 'admin'),
                        'uploaded_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            uploaded_count += 1

        # Build response message
        if pdf_extracted_count > 0:
            message = f'Successfully processed: {uploaded_count} QR images ({pdf_extracted_count} from PDF extraction)'
        else:
            message = f'Successfully uploaded {uploaded_count} images'

        return JsonResponse({
            'success': True,
            'message': message,
            'uploaded': uploaded_count,
            'pdf_extracted': pdf_extracted_count,
            'not_found': not_found_count,
            'errors': errors if errors else None
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_debtor_image(request, account_number):
    """Get debtor image data by account number (returns base64 for display)"""
    try:
        # Verify token (admin or debtor can access)
        auth_header = request.headers.get('Authorization')
        print(f"=== DEBUG AUTH ===")
        print(f"Auth header present: {auth_header is not None}")

        if not auth_header or not auth_header.startswith('Bearer '):
            print("No valid auth header")
            return JsonResponse({'error': 'Unauthorized - No token'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        print(f"Token payload: {payload}")

        if not payload:
            print("Token verification failed")
            return JsonResponse({'error': 'Unauthorized - Invalid token'}, status=401)

        # Check if user is authorized
        print(f"Role: {payload.get('role')}, Token accounts: {payload.get('account_numbers')}, Requested: {account_number}")
        if payload.get('role') == 'debtor':
            # Check both old format (single account_number) and new format (account_numbers list)
            account_numbers = payload.get('account_numbers', [])
            single_account = payload.get('account_number')
            if single_account:
                account_numbers.append(single_account)

            if account_number not in account_numbers:
                print("Account mismatch")
                return JsonResponse({'error': 'Unauthorized - Account mismatch'}, status=401)

        # First check database for image record
        debtor_images = get_debtor_images_collection()
        image_doc = debtor_images.find_one({'account_number': account_number})

        print(f"=== DEBUG get_debtor_image ===")
        print(f"Account: {account_number}")
        print(f"IMAGES_DIR: {IMAGES_DIR}")
        print(f"Image doc found: {image_doc is not None}")
        if image_doc:
            print(f"Filename in DB: {image_doc.get('filename')}")

        if image_doc:
            # Try to read image from storage using storage_key or fallback to filename
            filename = image_doc.get('filename')
            storage_key = image_doc.get('storage_key')
            print(f"Storage key in DB: {storage_key}")
            print(f"Filename in DB: {filename}")

            if storage_key or filename:
                try:
                    if storage_key:
                        # Use storage key directly
                        image_bytes = get_file(storage_key)
                    else:
                        # Build storage key from filename
                        ext = os.path.splitext(filename)[1].lstrip('.') or 'png'
                        image_bytes = fetch_debtor_image_data(account_number, ext)

                    image_data = base64.b64encode(image_bytes).decode('utf-8')
                    return JsonResponse({
                        'success': True,
                        'image': {
                            'data': image_data,
                            'content_type': image_doc.get('content_type', 'image/png'),
                            'filename': filename or f"{account_number}.png"
                        }
                    })
                except Exception as e:
                    print(f"Error fetching from storage: {e}")
                    # Continue to fallback

        # Fallback: Check storage directly for common extensions
        valid_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
        for ext in valid_extensions:
            try:
                image_bytes = fetch_debtor_image_data(account_number, ext)
                # Determine content type
                content_type = 'image/png'
                if ext in ['jpg', 'jpeg']:
                    content_type = 'image/jpeg'
                elif ext == 'gif':
                    content_type = 'image/gif'
                elif ext == 'webp':
                    content_type = 'image/webp'

                image_data = base64.b64encode(image_bytes).decode('utf-8')
                return JsonResponse({
                    'success': True,
                    'image': {
                        'data': image_data,
                        'content_type': content_type,
                        'filename': f"{account_number}.{ext}"
                    }
                })
            except Exception:
                continue

        return JsonResponse({
            'success': True,
            'image': None,
            'message': 'No image found for this account'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_debtor_image_public(request, account_number):
    """Get debtor image data by account number (PUBLIC ACCESS - no auth required)"""
    try:
        # First check database for image record
        debtor_images = get_debtor_images_collection()
        image_doc = debtor_images.find_one({'account_number': account_number})

        if image_doc:
            # Try to read image from storage using storage_key or fallback to filename
            filename = image_doc.get('filename')
            storage_key = image_doc.get('storage_key')

            if storage_key or filename:
                try:
                    if storage_key:
                        # Use storage key directly
                        image_bytes = get_file(storage_key)
                    else:
                        # Build storage key from filename
                        ext = os.path.splitext(filename)[1].lstrip('.') or 'png'
                        image_bytes = fetch_debtor_image_data(account_number, ext)

                    image_data = base64.b64encode(image_bytes).decode('utf-8')
                    return JsonResponse({
                        'success': True,
                        'image': {
                            'data': image_data,
                            'content_type': image_doc.get('content_type', 'image/png'),
                            'filename': filename or f"{account_number}.png"
                        }
                    })
                except Exception as e:
                    print(f"Error fetching from storage: {e}")
                    # Continue to fallback

        # Fallback: Check storage directly for common extensions
        valid_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
        for ext in valid_extensions:
            try:
                image_bytes = fetch_debtor_image_data(account_number, ext)
                # Determine content type
                content_type = 'image/png'
                if ext in ['jpg', 'jpeg']:
                    content_type = 'image/jpeg'
                elif ext == 'gif':
                    content_type = 'image/gif'
                elif ext == 'webp':
                    content_type = 'image/webp'

                image_data = base64.b64encode(image_bytes).decode('utf-8')
                return JsonResponse({
                    'success': True,
                    'image': {
                        'data': image_data,
                        'content_type': content_type,
                        'filename': f"{account_number}.{ext}"
                    }
                })
            except Exception:
                continue

        return JsonResponse({
            'success': True,
            'image': None,
            'message': 'No image found for this account'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def serve_debtor_image(request, account_number):
    """Serve actual image file for a debtor"""
    try:
        # Verify token (admin or debtor can access)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Check if user is authorized
        if payload.get('role') == 'debtor':
            # Check both old format (single account_number) and new format (account_numbers list)
            account_numbers = payload.get('account_numbers', [])
            single_account = payload.get('account_number')
            if single_account:
                account_numbers.append(single_account)

            if account_number not in account_numbers:
                return JsonResponse({'error': 'Unauthorized'}, status=401)

        debtor_images = get_debtor_images_collection()
        image_doc = debtor_images.find_one({'account_number': account_number})

        if not image_doc:
            raise Http404("Image not found")

        # Find the image file from storage
        filename = image_doc.get('filename')
        storage_key = image_doc.get('storage_key')
        content_type = image_doc.get('content_type', 'image/png')

        try:
            if storage_key:
                image_bytes = get_file(storage_key)
            elif filename:
                ext = os.path.splitext(filename)[1].lstrip('.') or 'png'
                image_bytes = fetch_debtor_image_data(account_number, ext)
            else:
                raise Http404("Image file not found")

            return HttpResponse(image_bytes, content_type=content_type)
        except Exception as e:
            print(f"Error serving image: {e}")
            raise Http404("Image file not found")

    except Http404:
        raise
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_debtor_images_batch(request):
    """Get image URLs for multiple debtors in one request (for lazy loading)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Get account numbers from query params
        account_numbers = request.GET.get('accounts', '').split(',')
        account_numbers = [a.strip() for a in account_numbers if a.strip()]

        if not account_numbers:
            return JsonResponse({'success': True, 'images': {}})

        debtor_images = get_debtor_images_collection()

        # Query all images at once
        images = list(debtor_images.find(
            {'account_number': {'$in': account_numbers}},
            {'_id': 0, 'account_number': 1, 'filename': 1, 'content_type': 1}
        ))

        # Build response dict
        result = {}
        for img in images:
            result[img['account_number']] = {
                'url': f'/api/admin/images/{img["account_number"]}/file/',
                'content_type': img.get('content_type', 'image/png'),
                'filename': img.get('filename')
            }

        return JsonResponse({
            'success': True,
            'images': result
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_debtor_image(request, account_number):
    """Delete debtor image from file system (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        debtor_images = get_debtor_images_collection()
        image_doc = debtor_images.find_one({'account_number': account_number})

        # Delete file from storage if exists
        if image_doc:
            storage_key = image_doc.get('storage_key')
            filename = image_doc.get('filename')
            if storage_key:
                try:
                    delete_file(storage_key)
                except Exception as e:
                    print(f"Error deleting from storage: {e}")
            elif filename:
                # Try to delete by constructing key from filename
                ext = os.path.splitext(filename)[1].lstrip('.') or 'png'
                remove_debtor_image_from_storage(account_number, ext)

        # Delete metadata from MongoDB
        result = debtor_images.delete_one({'account_number': account_number})

        if result.deleted_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'Image deleted successfully'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'No image found to delete'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# BULK QR CODE UPLOAD SYSTEM
# ============================================
# Supports: Single images, ZIP files with multiple images, PDFs with QR codes
# Mapping: filename (without extension) = account_number

@csrf_exempt
@require_http_methods(["POST"])
def stage_pdf_files(request):
    """
    Bulk QR code upload - replaces PDF staging.
    Accepts: PNG/JPG images, ZIP files with images, PDFs with QR codes.
    Maps filename to account_number automatically.
    """
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        files = request.FILES.getlist('files')
        
        # Also try single file if getlist is empty
        if not files and 'files' in request.FILES:
            files = [request.FILES['files']]

        if not files:
            return JsonResponse({'error': 'No files uploaded'}, status=400)

        debtors = get_debtors_collection()
        debtor_images = get_debtor_images_collection()
        
        uploaded_count = 0
        not_found_count = 0
        errors = []
        valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

        for file in files:
            filename = file.name
            file_lower = filename.lower()

            # Handle ZIP files
            if file_lower.endswith('.zip'):
                try:
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO(file.read())
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                        for zip_info in zip_ref.namelist():
                            # Skip directories and hidden files
                            if zip_info.endswith('/') or os.path.basename(zip_info).startswith('.'):
                                continue
                            
                            # Check if it's an image
                            zip_file_lower = zip_info.lower()
                            if not any(zip_file_lower.endswith(ext) for ext in valid_image_extensions):
                                continue
                            
                            # Extract account number from filename
                            base_filename = os.path.basename(zip_info)
                            account_number = base_filename.rsplit('.', 1)[0].strip()
                            
                            # Check if debtor exists (match by account_number or national_id)
                            debtor = debtors.find_one({'$or': [
                                {'account_number': account_number},
                                {'national_id': account_number}
                            ]})
                            if not debtor:
                                not_found_count += 1
                                errors.append(f'{base_filename}: Account/ID {account_number} not found')
                                continue
                            
                            # Read image data from ZIP
                            image_data = zip_ref.read(zip_info)
                            
                            # Determine extension
                            file_ext = os.path.splitext(base_filename)[1].lstrip('.')
                            if not file_ext:
                                file_ext = 'png'
                            
                            # Save to S3
                            image_result = save_debtor_image(account_number, image_data, file_ext)
                            image_key = image_result.get('key', get_image_key(account_number, file_ext))
                            
                            # Store metadata in MongoDB
                            debtor_images.update_one(
                                {'account_number': debtor.get('account_number')},
                                {
                                    '$set': {
                                        'account_number': debtor.get('account_number'),
                                        'national_id': debtor.get('national_id', ''),
                                        'filename': f"{account_number}.{file_ext}",
                                        'content_type': f'image/{file_ext}',
                                        'storage_key': image_key,
                                        'uploaded_by': payload.get('username', 'admin'),
                                        'uploaded_at': datetime.utcnow(),
                                        'source': 'bulk_upload_zip',
                                        'source_file': filename
                                    }
                                },
                                upsert=True
                            )
                            uploaded_count += 1
                            
                except Exception as e:
                    errors.append(f"{filename}: ZIP processing failed - {str(e)}")
                continue

            # Handle PDF files with QR codes
            elif file_lower.endswith('.pdf'):
                try:
                    import fitz  # PyMuPDF
                    from PIL import Image
                    
                    pdf_data = file.read()
                    pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
                    
                    for page_num in range(len(pdf_doc)):
                        page = pdf_doc[page_num]
                        
                        # Extract images from PDF page
                        image_list = page.get_images(full=True)
                        
                        for img_index, img_info in enumerate(image_list):
                            xref = img_info[0]
                            base_image = pdf_doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Try to extract account number from image or use PDF filename
                            if page_num == 0 and img_index == 0:
                                # First image - use PDF filename as account number
                                account_number = filename.rsplit('.', 1)[0].strip()
                            else:
                                # For multiple images, try pattern: filename_page_index
                                base_name = filename.rsplit('.', 1)[0].strip()
                                account_number = f"{base_name}_p{page_num+1}_i{img_index+1}"
                            
                            # Check if debtor exists (match by account_number or national_id)
                            debtor = debtors.find_one({'$or': [
                                {'account_number': account_number},
                                {'national_id': account_number}
                            ]})
                            if not debtor:
                                not_found_count += 1
                                errors.append(f'{filename} (page {page_num+1}): Account/ID {account_number} not found')
                                continue
                            
                            # Save to S3 as PNG
                            image_result = save_debtor_image(account_number, image_bytes, 'png')
                            image_key = image_result.get('key', get_image_key(account_number, 'png'))
                            
                            # Store metadata in MongoDB
                            debtor_images.update_one(
                                {'account_number': debtor.get('account_number')},
                                {
                                    '$set': {
                                        'account_number': debtor.get('account_number'),
                                        'national_id': debtor.get('national_id', ''),
                                        'filename': f"{account_number}.png",
                                        'content_type': 'image/png',
                                        'storage_key': image_key,
                                        'uploaded_by': payload.get('username', 'admin'),
                                        'uploaded_at': datetime.utcnow(),
                                        'source': 'pdf_extraction',
                                        'source_file': filename
                                    }
                                },
                                upsert=True
                            )
                            uploaded_count += 1
                    
                    pdf_doc.close()
                    
                except Exception as e:
                    errors.append(f"{filename}: PDF processing failed - {str(e)}")
                continue

            # Handle regular image files
            else:
                # Check if it's a valid image extension
                file_ext = None
                for ext in valid_image_extensions:
                    if file_lower.endswith(ext):
                        file_ext = ext
                        break
                
                if not file_ext:
                    errors.append(f'{filename}: Invalid file type (use PNG, JPG, GIF, WEBP, PDF, or ZIP)')
                    continue
                
                # Extract account number from filename
                account_number = filename.rsplit('.', 1)[0].strip()
                
                # Check if debtor exists (match by account_number or national_id)
                debtor = debtors.find_one({'$or': [
                    {'account_number': account_number},
                    {'national_id': account_number}
                ]})
                if not debtor:
                    not_found_count += 1
                    errors.append(f'{filename}: Account/ID {account_number} not found')
                    continue
                
                # Read image data
                image_data = file.read()
                extension = file_ext.lstrip('.')
                
                # Save to S3
                image_result = save_debtor_image(account_number, image_data, extension)
                image_key = image_result.get('key', get_image_key(account_number, extension))
                
                # Store metadata in MongoDB
                debtor_images.update_one(
                    {'account_number': debtor.get('account_number')},
                    {
                        '$set': {
                            'account_number': debtor.get('account_number'),
                            'national_id': debtor.get('national_id', ''),
                            'filename': f"{account_number}.{extension}",
                            'content_type': file.content_type or f'image/{extension}',
                            'storage_key': image_key,
                            'uploaded_by': payload.get('username', 'admin'),
                            'uploaded_at': datetime.utcnow(),
                            'source': 'bulk_upload',
                            'source_file': filename
                        }
                    },
                    upsert=True
                )
                uploaded_count += 1

        return JsonResponse({
            'success': True,
            'uploaded': uploaded_count,
            'not_found': not_found_count,
            'errors': errors,
            'message': f'Successfully uploaded {uploaded_count} QR images'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stage_pdf_files_base64(request):
    """
    Bulk QR upload using base64 encoding (Lambda-optimized).
    Accepts: images, PDFs, ZIP files in base64 format.
    """
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        files_data = data.get('files', [])
        if not files_data:
            return JsonResponse({'error': 'No files provided'}, status=400)

        debtors = get_debtors_collection()
        debtor_images = get_debtor_images_collection()
        
        uploaded_count = 0
        not_found_count = 0
        errors = []
        valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

        for file_data in files_data:
            filename = file_data.get('filename', '')
            base64_content = file_data.get('content', '')
            
            if not base64_content:
                errors.append(f"{filename}: No file content")
                continue

            try:
                import base64
                file_bytes = base64.b64decode(base64_content)
                file_lower = filename.lower()
                
                # Handle ZIP files
                if file_lower.endswith('.zip'):
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO(file_bytes)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                        for zip_info in zip_ref.namelist():
                            if zip_info.endswith('/') or os.path.basename(zip_info).startswith('.'):
                                continue
                            
                            zip_file_lower = zip_info.lower()
                            if not any(zip_file_lower.endswith(ext) for ext in valid_image_extensions):
                                continue
                            
                            base_filename = os.path.basename(zip_info)
                            account_number = base_filename.rsplit('.', 1)[0].strip()
                            
                            debtor = debtors.find_one({'$or': [
                                {'account_number': account_number},
                                {'national_id': account_number}
                            ]})
                            if not debtor:
                                not_found_count += 1
                                errors.append(f'{base_filename}: Account/ID {account_number} not found')
                                continue
                            
                            image_data = zip_ref.read(zip_info)
                            file_ext = os.path.splitext(base_filename)[1].lstrip('.') or 'png'
                            
                            image_result = save_debtor_image(account_number, image_data, file_ext)
                            image_key = image_result.get('key', get_image_key(account_number, file_ext))
                            
                            debtor_images.update_one(
                                {'account_number': debtor.get('account_number')},
                                {
                                    '$set': {
                                        'account_number': debtor.get('account_number'),
                                        'national_id': debtor.get('national_id', ''),
                                        'filename': f"{account_number}.{file_ext}",
                                        'content_type': f'image/{file_ext}',
                                        'storage_key': image_key,
                                        'uploaded_by': payload.get('username', 'admin'),
                                        'uploaded_at': datetime.utcnow(),
                                        'source': 'bulk_upload_zip_base64',
                                        'source_file': filename
                                    }
                                },
                                upsert=True
                            )
                            uploaded_count += 1
                
                # Handle PDF files
                elif file_lower.endswith('.pdf'):
                    import fitz
                    
                    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                    
                    for page_num in range(len(pdf_doc)):
                        page = pdf_doc[page_num]
                        image_list = page.get_images(full=True)
                        
                        for img_index, img_info in enumerate(image_list):
                            xref = img_info[0]
                            base_image = pdf_doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            if page_num == 0 and img_index == 0:
                                account_number = filename.rsplit('.', 1)[0].strip()
                            else:
                                base_name = filename.rsplit('.', 1)[0].strip()
                                account_number = f"{base_name}_p{page_num+1}_i{img_index+1}"
                            
                            debtor = debtors.find_one({'$or': [
                                {'account_number': account_number},
                                {'national_id': account_number}
                            ]})
                            if not debtor:
                                not_found_count += 1
                                errors.append(f'{filename} (page {page_num+1}): Account/ID {account_number} not found')
                                continue
                            
                            image_result = save_debtor_image(account_number, image_bytes, 'png')
                            image_key = image_result.get('key', get_image_key(account_number, 'png'))
                            
                            debtor_images.update_one(
                                {'account_number': debtor.get('account_number')},
                                {
                                    '$set': {
                                        'account_number': debtor.get('account_number'),
                                        'national_id': debtor.get('national_id', ''),
                                        'filename': f"{account_number}.png",
                                        'content_type': 'image/png',
                                        'storage_key': image_key,
                                        'uploaded_by': payload.get('username', 'admin'),
                                        'uploaded_at': datetime.utcnow(),
                                        'source': 'pdf_extraction_base64',
                                        'source_file': filename
                                    }
                                },
                                upsert=True
                            )
                            uploaded_count += 1
                    
                    pdf_doc.close()
                
                # Handle regular images
                else:
                    file_ext = None
                    for ext in valid_image_extensions:
                        if file_lower.endswith(ext):
                            file_ext = ext
                            break
                    
                    if not file_ext:
                        errors.append(f'{filename}: Invalid file type')
                        continue
                    
                    account_number = filename.rsplit('.', 1)[0].strip()
                    
                    debtor = debtors.find_one({'$or': [
                        {'account_number': account_number},
                        {'national_id': account_number}
                    ]})
                    if not debtor:
                        not_found_count += 1
                        errors.append(f'{filename}: Account/ID {account_number} not found')
                        continue
                    
                    extension = file_ext.lstrip('.')
                    image_result = save_debtor_image(account_number, file_bytes, extension)
                    image_key = image_result.get('key', get_image_key(account_number, extension))
                    
                    debtor_images.update_one(
                        {'account_number': debtor.get('account_number')},
                        {
                            '$set': {
                                'account_number': debtor.get('account_number'),
                                'national_id': debtor.get('national_id', ''),
                                'filename': f"{account_number}.{extension}",
                                'content_type': f'image/{extension}',
                                'storage_key': image_key,
                                'uploaded_by': payload.get('username', 'admin'),
                                'uploaded_at': datetime.utcnow(),
                                'source': 'bulk_upload_base64',
                                'source_file': filename
                            }
                        },
                        upsert=True
                    )
                    uploaded_count += 1
                    
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")

        return JsonResponse({
            'success': True,
            'uploaded': uploaded_count,
            'not_found': not_found_count,
            'errors': errors,
            'message': f'Successfully uploaded {uploaded_count} QR images (base64)'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def finalize_staging(request, job_id):
    """Mark a staging job as ready for processing."""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        jobs = get_processing_jobs_collection()
        result = jobs.update_one(
            {'job_id': job_id, 'status': 'staging'},
            {'$set': {'status': 'staged'}}
        )

        if result.modified_count > 0:
            return JsonResponse({'success': True, 'message': 'Job ready for processing'})
        else:
            return JsonResponse({'error': 'Job not found or not in staging status'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_pdf_processing(request, job_id):
    """Start background processing of staged PDF files."""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        jobs = get_processing_jobs_collection()
        job = jobs.find_one({'job_id': job_id})

        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)

        if job['status'] == 'processing':
            return JsonResponse({'error': 'Job is already processing'}, status=400)

        if job['status'] == 'completed':
            return JsonResponse({'error': 'Job is already completed'}, status=400)

        # Update job status to processing
        jobs.update_one(
            {'job_id': job_id},
            {'$set': {'status': 'processing', 'started_at': datetime.utcnow()}}
        )

        # Start background processing - use SQS if available, otherwise thread
        if SQS_AVAILABLE and sqs_client and settings.PDF_QUEUE_URL:
            # Send message to SQS for Lambda processing
            try:
                sqs_client.send_message(
                    QueueUrl=settings.PDF_QUEUE_URL,
                    MessageBody=json.dumps({'job_id': job_id}),
                    MessageAttributes={
                        'job_id': {
                            'DataType': 'String',
                            'StringValue': job_id
                        }
                    }
                )
                print(f"[SQS] Sent job {job_id} to queue")
            except Exception as e:
                print(f"[SQS] Failed to send message: {e}, falling back to thread")
                import threading
                thread = threading.Thread(target=process_pdf_job_background, args=(job_id,))
                thread.daemon = True
                thread.start()
        else:
            # Fall back to thread-based processing
            import threading
            thread = threading.Thread(target=process_pdf_job_background, args=(job_id,))
            thread.daemon = True
            thread.start()

        return JsonResponse({
            'success': True,
            'message': 'Processing started',
            'job_id': job_id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def process_pdf_job_background(job_id):
    """Background worker to process staged PDF files."""
    jobs = get_processing_jobs_collection()
    job = jobs.find_one({'job_id': job_id})

    if not job:
        return

    debtors = get_debtors_collection()
    debtor_images = get_debtor_images_collection()
    valid_image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']

    processed = 0
    successful = 0
    failed = 0
    not_found = 0
    errors = []

    try:
        # Get list of PDF files from storage
        staged_files = list_staging_files(job_id)
        pdf_files = [f for f in staged_files if f.get('key', '').lower().endswith('.pdf')]
        total = len(pdf_files)

        for pdf_file_info in pdf_files:
            pdf_key = pdf_file_info.get('key')
            filename = os.path.basename(pdf_key)

            try:
                account_number = filename.rsplit('.', 1)[0].strip()

                # Download PDF from storage and process
                pdf_data = get_file(pdf_key)
                pdf_buffer = BytesIO(pdf_data)
                qr_results, pdf_errors = process_pdf_for_qr(pdf_buffer, filename)

                if pdf_errors:
                    errors.extend(pdf_errors)

                for acc_num, qr_bytes in qr_results:
                    # Check if debtor exists
                    debtor = debtors.find_one({'account_number': acc_num})
                    if not debtor:
                        not_found += 1
                        errors.append(f'{filename}: Account {acc_num} not found in database')
                        continue

                    # Delete existing images with different extensions
                    for old_ext in valid_image_extensions:
                        if old_ext != 'png':
                            remove_debtor_image_from_storage(acc_num, old_ext)

                    # Save QR image to storage
                    safe_filename = f"{acc_num}.png"
                    image_result = save_debtor_image(acc_num, qr_bytes, 'png')
                    image_key = image_result.get('key', get_image_key(acc_num, 'png'))

                    # Store metadata
                    debtor_images.update_one(
                        {'account_number': acc_num},
                        {
                            '$set': {
                                'account_number': acc_num,
                                'filename': safe_filename,
                                'content_type': 'image/png',
                                'storage_key': image_key,
                                'uploaded_at': datetime.utcnow(),
                                'source': 'pdf_extraction',
                                'source_file': filename
                            }
                        },
                        upsert=True
                    )
                    successful += 1

                if not qr_results:
                    failed += 1

                processed += 1

                # Update progress every 10 files
                if processed % 10 == 0:
                    jobs.update_one(
                        {'job_id': job_id},
                        {'$set': {
                            'processed': processed,
                            'successful': successful,
                            'failed': failed,
                            'not_found': not_found
                        }}
                    )

                # Clean up memory
                gc.collect()

            except Exception as e:
                errors.append(f'{filename}: {str(e)}')
                failed += 1
                processed += 1

        # Mark job as completed
        jobs.update_one(
            {'job_id': job_id},
            {'$set': {
                'status': 'completed',
                'processed': processed,
                'successful': successful,
                'failed': failed,
                'not_found': not_found,
                'processing_errors': errors[-100:] if len(errors) > 100 else errors,  # Keep last 100 errors
                'completed_at': datetime.utcnow()
            }}
        )

        # Clean up staging folder in storage
        try:
            delete_staging_folder(job_id)
        except Exception as cleanup_err:
            print(f"Failed to cleanup staging: {cleanup_err}")

    except Exception as e:
        jobs.update_one(
            {'job_id': job_id},
            {'$set': {
                'status': 'failed',
                'processing_errors': [str(e)],
                'completed_at': datetime.utcnow()
            }}
        )


@csrf_exempt
@require_http_methods(["GET"])
def get_processing_status(request, job_id):
    """Get status of a PDF processing job."""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        jobs = get_processing_jobs_collection()
        job = jobs.find_one({'job_id': job_id}, {'_id': 0})

        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)

        # Convert datetime objects
        for field in ['created_at', 'started_at', 'completed_at']:
            if job.get(field):
                job[field] = job[field].isoformat()

        # Calculate percentage
        if job['total_files'] > 0:
            job['percentage'] = round((job['processed'] / job['total_files']) * 100, 1)
        else:
            job['percentage'] = 0

        return JsonResponse(job)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_processing_jobs(request):
    """Get all PDF processing jobs."""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)

        if not payload or payload.get('role') not in ['admin', 'super_admin']:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        jobs = get_processing_jobs_collection()
        job_list = list(jobs.find({}, {'_id': 0, 'processing_errors': 0, 'staging_errors': 0}).sort('created_at', -1).limit(50))

        # Convert datetime objects and calculate percentage
        for job in job_list:
            for field in ['created_at', 'started_at', 'completed_at']:
                if job.get(field):
                    job[field] = job[field].isoformat()
            
            # Safely handle total_files field
            total_files = job.get('total_files', 0)
            processed = job.get('processed', 0)
            
            if total_files > 0:
                job['percentage'] = round((processed / total_files) * 100, 1)
            else:
                job['percentage'] = 0
                
            # Ensure required fields exist
            job['total_files'] = total_files
            job['processed'] = processed

        return JsonResponse({'jobs': job_list})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# PRODUCTION QR CODE & PDF PROCESSING ENDPOINTS
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def validate_image_upload(request):
    """Validate image before processing"""
    try:
        data = json.loads(request.body)
        
        # Check for base64 image data
        image_data_b64 = data.get('image_data')
        if not image_data_b64:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        try:
            # Decode base64
            image_data = base64.b64decode(image_data_b64)
        except Exception as e:
            return JsonResponse({'error': 'Invalid base64 image data'}, status=400)
        
        if PRODUCTION_QR_AVAILABLE:
            validation = RobustQRProcessor.validate_image_input(image_data, data.get('filename', ''))
        else:
            # Basic validation fallback
            size_mb = len(image_data) / (1024 * 1024)
            validation = {
                'valid': len(image_data) > 0 and size_mb <= 10,
                'error': None if size_mb <= 10 else f'Image too large: {size_mb:.1f}MB',
                'details': {'size_mb': round(size_mb, 2)}
            }
        
        return JsonResponse({
            'valid': validation['valid'],
            'error': validation.get('error'),
            'details': validation.get('details', {}),
            'processing_available': PRODUCTION_QR_AVAILABLE
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Validation failed: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_thai_payment_qr(request):
    """Generate comprehensive Thai payment QR code"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        data = json.loads(request.body)
        
        # Required fields
        account_number = data.get('account_number')
        debtor_name = data.get('debtor_name')
        
        if not account_number or not debtor_name:
            return JsonResponse({'error': 'Account number and debtor name required'}, status=400)
        
        # Optional fields
        outstanding_balance = data.get('outstanding_balance')
        payment_amount = data.get('payment_amount')
        case_id = data.get('case_id')
        contact_info = data.get('contact_info', 'hello@poweramc.co')
        due_date = data.get('due_date')
        
        if PRODUCTION_QR_AVAILABLE:
            qr_result = ThaiPaymentQRGenerator.create_payment_qr(
                account_number=account_number,
                debtor_name=debtor_name,
                outstanding_balance=outstanding_balance,
                amount=payment_amount,
                case_id=case_id,
                contact_info=contact_info,
                due_date=due_date
            )
            
            if qr_result['success']:
                return JsonResponse({
                    'success': True,
                    'qr_image_base64': qr_result['qr_image_base64'],
                    'payment_info': qr_result.get('payment_info', {}),
                    'metadata': qr_result.get('metadata', {})
                })
            else:
                return JsonResponse({'success': False, 'error': qr_result['error']}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Production QR generator not available'}, status=503)
        
    except Exception as e:
        return JsonResponse({'error': f'QR generation failed: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_qr_by_national_id(request, national_id):
    """Get QR code or payment information for specific National ID"""
    try:
        debtors = get_debtors_collection()
        debtor = debtors.find_one({'national_id': national_id})
        
        if not debtor:
            return JsonResponse({
                'success': False,
                'error': 'No account found for this National ID',
                'national_id': national_id
            }, status=404)
        
        # Check if there's a specific QR image for this account
        account_number = debtor['account_number']
        
        # Try to get debtor-specific image first
        try:
            image_data = fetch_debtor_image_data(account_number)
            if image_data:
                return JsonResponse({
                    'success': True,
                    'type': 'debtor_specific',
                    'national_id': national_id,
                    'account_number': account_number,
                    'qr_code': {
                        'image': image_data,
                        'content_type': 'image/png',
                        'filename': f'qr_{account_number}.png'
                    },
                    'account_info': {
                        'name': debtor.get('name', ''),
                        'outstanding_balance': debtor.get('outstanding_balance', 0),
                        'case_id': debtor.get('case_id', '')
                    }
                })
        except Exception as e:
            print(f"No specific image for account {account_number}: {e}")
        
        # Generate payment QR if production QR is available
        if PRODUCTION_QR_AVAILABLE:
            qr_result = ThaiPaymentQRGenerator.create_payment_qr(
                account_number=account_number,
                debtor_name=debtor.get('name', ''),
                outstanding_balance=debtor.get('outstanding_balance', 0),
                case_id=debtor.get('case_id', ''),
                contact_info='hello@poweramc.co'
            )
            
            if qr_result['success']:
                return JsonResponse({
                    'success': True,
                    'type': 'generated_payment_qr',
                    'national_id': national_id,
                    'account_number': account_number,
                    'qr_code': {
                        'image': qr_result['qr_image_base64'],
                        'content_type': 'image/png',
                        'filename': f'payment_qr_{account_number}.png'
                    },
                    'payment_info': qr_result.get('payment_info', {}),
                    'account_info': {
                        'name': debtor.get('name', ''),
                        'outstanding_balance': debtor.get('outstanding_balance', 0),
                        'case_id': debtor.get('case_id', '')
                    }
                })
        
        # Fallback: return global QR code with account information
        settings = get_settings_collection()
        qr_setting = settings.find_one({'key': 'line_qr_code'})
        
        return JsonResponse({
            'success': True,
            'type': 'global_with_account_info',
            'national_id': national_id,
            'account_number': account_number,
            'qr_code': {
                'image': qr_setting.get('value') if qr_setting else None,
                'content_type': 'image/png',
                'filename': 'global_qr.png'
            } if qr_setting else None,
            'account_info': {
                'name': debtor.get('name', ''),
                'outstanding_balance': debtor.get('outstanding_balance', 0),
                'case_id': debtor.get('case_id', ''),
                'account_number': account_number
            },
            'payment_instructions': {
                'contact_email': 'hello@poweramc.co',
                'message': f'Please contact us with your account number {account_number} for payment arrangements.'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to get QR code: {str(e)}',
            'national_id': national_id
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_qr_by_account(request, account_number):
    """Get QR code or payment information for specific Account Number"""
    try:
        debtors = get_debtors_collection()
        debtor = debtors.find_one({'account_number': account_number})
        
        if not debtor:
            return JsonResponse({
                'success': False,
                'error': 'Account not found',
                'account_number': account_number
            }, status=404)
        
        # Try to get debtor-specific image first
        try:
            image_data = fetch_debtor_image_data(account_number)
            if image_data:
                return JsonResponse({
                    'success': True,
                    'type': 'debtor_specific',
                    'account_number': account_number,
                    'qr_code': {
                        'image': image_data,
                        'content_type': 'image/png',
                        'filename': f'qr_{account_number}.png'
                    },
                    'account_info': {
                        'name': debtor.get('name', ''),
                        'outstanding_balance': debtor.get('outstanding_balance', 0),
                        'case_id': debtor.get('case_id', ''),
                        'national_id': debtor.get('national_id', '')
                    }
                })
        except Exception as e:
            print(f"No specific image for account {account_number}: {e}")
        
        # Generate payment QR if production QR is available
        if PRODUCTION_QR_AVAILABLE:
            qr_result = ThaiPaymentQRGenerator.create_payment_qr(
                account_number=account_number,
                debtor_name=debtor.get('name', ''),
                outstanding_balance=debtor.get('outstanding_balance', 0),
                case_id=debtor.get('case_id', ''),
                contact_info='hello@poweramc.co'
            )
            
            if qr_result['success']:
                return JsonResponse({
                    'success': True,
                    'type': 'generated_payment_qr',
                    'account_number': account_number,
                    'qr_code': {
                        'image': qr_result['qr_image_base64'],
                        'content_type': 'image/png',
                        'filename': f'payment_qr_{account_number}.png'
                    },
                    'payment_info': qr_result.get('payment_info', {}),
                    'account_info': {
                        'name': debtor.get('name', ''),
                        'outstanding_balance': debtor.get('outstanding_balance', 0),
                        'case_id': debtor.get('case_id', ''),
                        'national_id': debtor.get('national_id', '')
                    }
                })
        
        # Fallback: return global QR code with account information
        settings = get_settings_collection()
        qr_setting = settings.find_one({'key': 'line_qr_code'})
        
        return JsonResponse({
            'success': True,
            'type': 'global_with_account_info',
            'account_number': account_number,
            'qr_code': {
                'image': qr_setting.get('value') if qr_setting else None,
                'content_type': 'image/png',
                'filename': 'global_qr.png'
            } if qr_setting else None,
            'account_info': {
                'name': debtor.get('name', ''),
                'outstanding_balance': debtor.get('outstanding_balance', 0),
                'case_id': debtor.get('case_id', ''),
                'national_id': debtor.get('national_id', ''),
                'account_number': account_number
            },
            'payment_instructions': {
                'contact_email': 'hello@poweramc.co',
                'message': f'Please contact us with your account number {account_number} for payment arrangements.'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to get QR code: {str(e)}',
            'account_number': account_number
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_qr_processing_status(request):
    """Get QR processing capabilities and status"""
    try:
        return JsonResponse({
            'production_qr_available': PRODUCTION_QR_AVAILABLE,
            'pdf_processing_available': PDF_PROCESSING_AVAILABLE,
            'ocr_available': OCR_AVAILABLE,
            'capabilities': {
                'qr_generation': PRODUCTION_QR_AVAILABLE,
                'image_enhancement': PRODUCTION_QR_AVAILABLE,
                'pdf_text_extraction': PRODUCTION_QR_AVAILABLE,
                'payment_qr_generation': PRODUCTION_QR_AVAILABLE,
                'legacy_qr_processing': not PRODUCTION_QR_AVAILABLE,
                'national_id_qr': True,  # Always available
                'account_number_qr': True,  # Always available
                'global_line_qr': True  # Always available
            },
            'status': 'Production Ready' if PRODUCTION_QR_AVAILABLE else 'Legacy Mode',
            'qr_types': {
                'global_line_qr': 'Contact support QR (same for all users)',
                'account_payment_qr': 'Account-specific payment QR codes',
                'generated_payment_qr': 'Auto-generated payment QR with account info'
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Status check failed: {str(e)}'}, status=500)
