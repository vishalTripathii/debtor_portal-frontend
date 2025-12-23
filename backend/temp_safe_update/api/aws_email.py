"""
AWS SES Email Backend for Django

This module provides an email backend that uses AWS SES for sending emails.
It can be used as a drop-in replacement for Django's SMTP backend.

Usage:
    In settings.py:
        EMAIL_BACKEND = 'api.aws_email.SESEmailBackend'
        SES_SENDER_EMAIL = 'noreply@yourdomain.com'

    Or use directly:
        from api.aws_email import send_ses_email
        send_ses_email(
            to_emails=['user@example.com'],
            subject='Hello',
            body_text='Plain text body',
            body_html='<h1>HTML body</h1>'
        )
"""

import os
import logging
from typing import List, Optional, Dict, Any

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage, EmailMultiAlternatives

# Try to import boto3
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception

logger = logging.getLogger(__name__)


class SESEmailBackend(BaseEmailBackend):
    """
    Django email backend using AWS SES.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)

        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for SES email backend")

        self.region = getattr(settings, 'AWS_REGION', 'ap-southeast-1')
        self.sender = getattr(settings, 'SES_SENDER_EMAIL',
                              getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'))

        # Create SES client
        self.client = boto3.client('ses', region_name=self.region)

    def send_messages(self, email_messages) -> int:
        """
        Send one or more EmailMessage objects and return the number sent.
        """
        if not email_messages:
            return 0

        num_sent = 0
        for message in email_messages:
            try:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
                logger.error(f"Failed to send email: {str(e)}")

        return num_sent

    def _send(self, message: EmailMessage) -> bool:
        """
        Send a single EmailMessage.
        """
        if not message.recipients():
            return False

        # Build the email
        from_email = message.from_email or self.sender
        to_addresses = list(message.to)
        cc_addresses = list(message.cc) if message.cc else []
        bcc_addresses = list(message.bcc) if message.bcc else []

        # Build destination
        destination = {'ToAddresses': to_addresses}
        if cc_addresses:
            destination['CcAddresses'] = cc_addresses
        if bcc_addresses:
            destination['BccAddresses'] = bcc_addresses

        # Build message content
        body = {}

        # Check if this is a multipart message with HTML
        if isinstance(message, EmailMultiAlternatives):
            # Plain text body
            if message.body:
                body['Text'] = {'Data': message.body, 'Charset': 'UTF-8'}

            # HTML body
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    body['Html'] = {'Data': content, 'Charset': 'UTF-8'}
                    break
        else:
            # Plain text only
            body['Text'] = {'Data': message.body, 'Charset': 'UTF-8'}

        # Send email
        try:
            response = self.client.send_email(
                Source=from_email,
                Destination=destination,
                Message={
                    'Subject': {
                        'Data': message.subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': body
                }
            )
            logger.info(f"Email sent via SES. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"SES send_email failed: {e.response['Error']['Message']}")
            if not self.fail_silently:
                raise
            return False


def send_ses_email(
    to_emails: List[str],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    from_email: Optional[str] = None,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
    reply_to: Optional[List[str]] = None,
    configuration_set: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email using AWS SES directly.

    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (optional)
        from_email: Sender email (uses SES_SENDER_EMAIL if not provided)
        cc_emails: CC recipients
        bcc_emails: BCC recipients
        reply_to: Reply-to addresses
        configuration_set: SES configuration set name

    Returns:
        Dict with 'success' and 'message_id' or 'error'
    """
    if not BOTO3_AVAILABLE:
        return {'success': False, 'error': 'boto3 is not installed'}

    region = getattr(settings, 'AWS_REGION', 'ap-southeast-1')
    sender = from_email or getattr(settings, 'SES_SENDER_EMAIL',
                                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'))

    client = boto3.client('ses', region_name=region)

    # Build destination
    destination = {'ToAddresses': to_emails}
    if cc_emails:
        destination['CcAddresses'] = cc_emails
    if bcc_emails:
        destination['BccAddresses'] = bcc_emails

    # Build message body
    body = {'Text': {'Data': body_text, 'Charset': 'UTF-8'}}
    if body_html:
        body['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}

    # Build request
    request = {
        'Source': sender,
        'Destination': destination,
        'Message': {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': body
        }
    }

    if reply_to:
        request['ReplyToAddresses'] = reply_to

    if configuration_set:
        request['ConfigurationSetName'] = configuration_set

    try:
        response = client.send_email(**request)
        logger.info(f"SES email sent. MessageId: {response['MessageId']}")
        return {
            'success': True,
            'message_id': response['MessageId']
        }

    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"SES send_email failed: {error_message}")
        return {
            'success': False,
            'error': error_message
        }


def send_templated_email(
    to_emails: List[str],
    template_name: str,
    template_data: Dict[str, Any],
    from_email: Optional[str] = None,
    configuration_set: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email using an SES template.

    Args:
        to_emails: List of recipient email addresses
        template_name: SES template name
        template_data: Template data as a dict
        from_email: Sender email
        configuration_set: SES configuration set name

    Returns:
        Dict with 'success' and 'message_id' or 'error'
    """
    import json

    if not BOTO3_AVAILABLE:
        return {'success': False, 'error': 'boto3 is not installed'}

    region = getattr(settings, 'AWS_REGION', 'ap-southeast-1')
    sender = from_email or getattr(settings, 'SES_SENDER_EMAIL',
                                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'))

    client = boto3.client('ses', region_name=region)

    request = {
        'Source': sender,
        'Destination': {'ToAddresses': to_emails},
        'Template': template_name,
        'TemplateData': json.dumps(template_data)
    }

    if configuration_set:
        request['ConfigurationSetName'] = configuration_set

    try:
        response = client.send_templated_email(**request)
        logger.info(f"SES templated email sent. MessageId: {response['MessageId']}")
        return {
            'success': True,
            'message_id': response['MessageId']
        }

    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"SES send_templated_email failed: {error_message}")
        return {
            'success': False,
            'error': error_message
        }


def verify_email_identity(email: str) -> Dict[str, Any]:
    """
    Send a verification email for a new sender identity.

    Args:
        email: Email address to verify

    Returns:
        Dict with 'success' and status
    """
    if not BOTO3_AVAILABLE:
        return {'success': False, 'error': 'boto3 is not installed'}

    region = getattr(settings, 'AWS_REGION', 'ap-southeast-1')
    client = boto3.client('ses', region_name=region)

    try:
        client.verify_email_identity(EmailAddress=email)
        return {
            'success': True,
            'message': f'Verification email sent to {email}'
        }

    except ClientError as e:
        return {
            'success': False,
            'error': e.response['Error']['Message']
        }


def get_send_quota() -> Dict[str, Any]:
    """
    Get the current SES sending quota and statistics.

    Returns:
        Dict with quota information
    """
    if not BOTO3_AVAILABLE:
        return {'success': False, 'error': 'boto3 is not installed'}

    region = getattr(settings, 'AWS_REGION', 'ap-southeast-1')
    client = boto3.client('ses', region_name=region)

    try:
        quota = client.get_send_quota()
        return {
            'success': True,
            'max_24_hour_send': quota['Max24HourSend'],
            'max_send_rate': quota['MaxSendRate'],
            'sent_last_24_hours': quota['SentLast24Hours']
        }

    except ClientError as e:
        return {
            'success': False,
            'error': e.response['Error']['Message']
        }
