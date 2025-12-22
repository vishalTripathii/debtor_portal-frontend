"""
MANUAL DATA CLEANUP GUIDE
=========================

Since direct connections are having DNS issues, here are your options:

LOCAL CLEANUP (COMPLETED ✅)
============================
- SQLite database: DELETED
- Local media files: CLEARED
- Local staging files: CLEARED

MONGODB ATLAS CLEANUP 
=====================
Option 1: Web Dashboard (Recommended)
--------------------------------------
1. Go to: https://cloud.mongodb.com/
2. Login with your credentials (naveenkumar/password)
3. Select your cluster: Cluster0
4. Click "Browse Collections"
5. For each collection (debtors, debtor_images, processing_jobs, activity_logs):
   - Click the collection name
   - Click "Delete Collection" or "Delete All Documents"

Option 2: MongoDB Compass (Desktop App)
---------------------------------------
1. Download MongoDB Compass
2. Connect with: mongodb+srv://naveenkumar:naveenkumar@cluster0.3v2gs.mongodb.net/
3. Select database: debtor_portal
4. Delete all collections or documents

AWS S3 CLEANUP
==============
Option 1: AWS Console (Recommended) 
-----------------------------------
1. Go to: https://console.aws.amazon.com/s3/
2. Find bucket: debtor-portal-storage
3. Delete all folders:
   - debtor_images/
   - pdf_staging/
   - uploads/
   - payment_receipts/
   - media/

Option 2: AWS CLI (if installed)
-------------------------------
aws s3 rm s3://debtor-portal-storage --recursive

VERIFICATION
============
After cleanup, test the system:
1. Visit your deployed app
2. Login as admin/admin123 (should be recreated)
3. Upload fresh QR images
4. Test PDF processing

QUICK STATUS CHECK
==================
Your local system is now clean and ready for fresh uploads!
The deployed Lambda functions are working perfectly for PDF processing.
"""

print(__doc__)