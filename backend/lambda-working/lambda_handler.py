"""
AWS Lambda handler for Django application using Mangum.

This module provides the entry point for AWS Lambda to handle
HTTP requests through API Gateway and route them to Django.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debtorportal.settings')

# Initialize Django before importing the application
import django
django.setup()

from mangum import Mangum
from django.core.asgi import get_asgi_application

# Get the ASGI application 
application = get_asgi_application()

# Create the Lambda handler
handler = Mangum(application, lifespan="off")


def warmup_handler(event, context):
    """
    Warmup handler to reduce cold starts.
    Can be triggered by CloudWatch Events on a schedule.
    """
    if event.get('source') == 'serverless-plugin-warmup':
        print('WarmUp - Lambda is warm!')
        return {'statusCode': 200, 'body': 'Lambda is warm!'}

    # If not a warmup event, pass to the main handler
    return handler(event, context)
