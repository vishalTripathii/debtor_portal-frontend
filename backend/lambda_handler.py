"""
AWS Lambda handler for Django application using Mangum.

This module provides the entry point for AWS Lambda to handle
HTTP requests through API Gateway and route them to Django.
"""

import os
import sys
import traceback
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debtorportal.settings')

try:
    # Initialize Django before importing the application
    import django
    django.setup()
    print("[Lambda] Django setup successful")
    
    from mangum import Mangum
    from django.core.asgi import get_asgi_application
    
    # Get the ASGI application 
    application = get_asgi_application()
    
    # Create the Lambda handler
    handler = Mangum(application, lifespan="off")
    print("[Lambda] Mangum handler created successfully")
except Exception as init_error:
    init_error_msg = str(init_error)
    init_error_tb = traceback.format_exc()
    print(f"[Lambda ERROR] Failed to initialize: {init_error_msg}")
    print(f"[Lambda ERROR] Traceback: {init_error_tb}")
    
    # Create a fallback handler that returns the error
    def handler(event, context):
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Lambda initialization failed',
                'message': init_error_msg,
                'traceback': init_error_tb
            })
        }


def warmup_handler(event, context):
    """
    Warmup handler to reduce cold starts.
    Can be triggered by CloudWatch Events on a schedule.
    """
    if event.get('source') == 'serverless-plugin-warmup':
        print('WarmUp - Lambda is warm!')
        return {'statusCode': 200, 'body': 'Lambda is warm!'}

    # If not a warmup event, pass to the main handler
    try:
        return handler(event, context)
    except Exception as e:
        print(f"[Lambda ERROR] Handler execution failed: {str(e)}")
        print(f"[Lambda ERROR] Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Handler execution failed',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        }
