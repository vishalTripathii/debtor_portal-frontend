"""
API URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Admin endpoints
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/verify-otp/', views.verify_admin_otp, name='verify_admin_otp'),
    path('admin/change-password/', views.change_admin_password, name='change_admin_password'),
    path('admin/upload/', views.upload_file, name='upload_file'),
    path('admin/upload-base64/', views.upload_file_base64, name='upload_file_base64'),
    path('admin/upload-async/', views.upload_file_async, name='upload_file_async'),
    path('admin/upload-presigned/', views.get_upload_presigned_url, name='get_upload_presigned_url'),
    path('admin/upload-start-processing/', views.start_processing, name='start_processing'),
    path('admin/upload-status/<str:job_id>/', views.get_upload_status, name='get_upload_status'),
    path('admin/debtors/', views.get_all_debtors, name='get_all_debtors'),
    path('admin/debtor/<str:account_number>/', views.update_debtor, name='update_debtor'),
    path('admin/debtor/<str:account_number>/delete/', views.delete_debtor, name='delete_debtor'),
    path('admin/debtors/bulk-delete/', views.bulk_delete_debtors, name='bulk_delete_debtors'),
    path('admin/debtors/bulk-delete-excel/', views.bulk_delete_from_excel, name='bulk_delete_from_excel'),
    path('admin/debtors/bulk-update-excel/', views.bulk_update_from_excel, name='bulk_update_from_excel'),
    # S3 pre-signed URL endpoints for Excel uploads
    path('admin/excel/get-upload-url/', views.get_excel_upload_url, name='get_excel_upload_url'),
    path('admin/excel/process-from-s3/', views.process_excel_from_s3, name='process_excel_from_s3'),
    path('admin/notifications/', views.get_notifications, name='get_notifications'),
    path('admin/notifications/<str:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('admin/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('admin/qr-code/', views.upload_qr_code, name='upload_qr_code'),
    path('admin/qr-code/base64/', views.upload_qr_code_base64, name='upload_qr_code_base64'),
    path('admin/qr-code/delete/', views.delete_qr_code, name='delete_qr_code'),
    
    # Enhanced QR Processing endpoints
    path('admin/qr-process/', views.process_qr_codes, name='process_qr_codes'),
    path('admin/qr-extract/', views.extract_qr_from_image, name='extract_qr_from_image'),
    path('admin/qr-generate/', views.generate_payment_qr, name='generate_payment_qr'),
    
    # Production QR Processing endpoints
    path('admin/production-qr/validate/', views.validate_image_upload, name='validate_image_upload'),
    path('admin/production-qr/thai-payment/', views.generate_thai_payment_qr, name='generate_thai_payment_qr'),
    path('admin/production-qr/status/', views.get_qr_processing_status, name='get_qr_processing_status'),
    
    path('admin/upload-history/', views.get_upload_history, name='get_upload_history'),
    path('admin/upload-history/<str:upload_id>/download/', views.download_upload_file, name='download_upload_file'),
    path('admin/images/upload/', views.upload_debtor_images, name='upload_debtor_images'),
    path('admin/images/batch/', views.get_debtor_images_batch, name='get_debtor_images_batch'),
    path('admin/images/<str:account_number>/', views.get_debtor_image, name='get_debtor_image'),
    path('admin/images/<str:account_number>/file/', views.serve_debtor_image, name='serve_debtor_image'),
    path('admin/images/<str:account_number>/delete/', views.delete_debtor_image, name='delete_debtor_image'),

    # Bulk QR Code Upload endpoints (replaces PDF staging)
    path('admin/qr/bulk-upload/', views.stage_pdf_files, name='bulk_qr_upload'),
    path('admin/qr/bulk-upload-base64/', views.stage_pdf_files_base64, name='bulk_qr_upload_base64'),
    
    # Async QR Upload endpoints (unlimited timeout - same as Excel)
    path('admin/qr/upload-async/', views.upload_qr_async, name='upload_qr_async'),
    path('admin/qr/upload-presigned/', views.get_qr_presigned_url, name='get_qr_presigned_url'),
    path('admin/qr/start-processing/', views.start_qr_processing, name='start_qr_processing'),
    path('admin/qr/upload-status/<str:job_id>/', views.get_qr_upload_status, name='get_qr_upload_status'),
    
    # Legacy PDF endpoints (kept for backward compatibility)
    path('admin/pdf/stage/', views.stage_pdf_files, name='stage_pdf_files'),
    path('admin/pdf/stage-base64/', views.stage_pdf_files_base64, name='stage_pdf_files_base64'),
    path('admin/pdf/finalize/<str:job_id>/', views.finalize_staging, name='finalize_staging'),
    path('admin/pdf/process/<str:job_id>/', views.start_pdf_processing, name='start_pdf_processing'),
    path('admin/pdf/status/<str:job_id>/', views.get_processing_status, name='get_processing_status'),
    path('admin/pdf/jobs/', views.get_all_processing_jobs, name='get_all_processing_jobs'),

    # Super Admin endpoints
    path('superadmin/settings/', views.get_system_settings, name='get_system_settings'),
    path('superadmin/settings/update/', views.update_system_settings, name='update_system_settings'),
    path('superadmin/admins/', views.get_admin_users, name='get_admin_users'),
    path('superadmin/admins/<str:username>/reset-password/', views.reset_admin_password, name='reset_admin_password'),

    # Public endpoints
    path('settings/qr-code/', views.get_qr_code, name='get_qr_code'),
    path('settings/system/', views.get_system_settings, name='get_public_system_settings'),
    
    # QR Code endpoints for debtors
    path('qr/national-id/<str:national_id>/', views.get_qr_by_national_id, name='get_qr_by_national_id'),
    path('qr/account/<str:account_number>/', views.get_qr_by_account, name='get_qr_by_account'),

    # Debtor portal endpoints
    path('debtor/login/', views.debtor_login, name='debtor_login'),
    path('debtor/verify-otp/', views.verify_otp, name='verify_otp'),
    path('debtor/pdpa-consent/', views.save_pdpa_consent, name='save_pdpa_consent'),
    path('debtor/payment-consent/', views.save_payment_consent, name='save_payment_consent'),
    path('debtor/accounts/', views.get_all_debtor_accounts, name='get_all_debtor_accounts'),
    path('debtor/account/<str:account_number>/', views.get_debtor_account, name='get_debtor_account'),
    path('debtor/account/<str:account_number>/contact/', views.update_debtor_contact, name='update_debtor_contact'),
    path('debtor/payment-interest/', views.send_payment_interest_notification, name='send_payment_interest_notification'),
    path('debtor/not-ready-to-pay/', views.send_not_ready_to_pay_notification, name='send_not_ready_to_pay_notification'),
    path('debtor/image/<str:account_number>/', views.get_debtor_image_public, name='get_debtor_image_public'),

    # Health check
    path('health/', views.health_check, name='health_check'),

    # Test endpoints (for debugging)
    path('test/email/', views.test_email, name='test_email'),

    # Receipt endpoints (admin only)
    path('admin/receipts/<str:filename>/', views.serve_payment_receipt, name='serve_payment_receipt'),
]
