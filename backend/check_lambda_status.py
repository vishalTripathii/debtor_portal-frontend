import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

print("Checking Lambda function status...")
try:
    response = lambda_client.get_function(FunctionName='debtor-portal-api-dev-api')
    
    config = response['Configuration']
    print(f"\n[OK] Function found: {config['FunctionName']}")
    print(f"  State: {config['State']}")
    print(f"  Last Update Status: {config['LastUpdateStatus']}")
    print(f"  Runtime: {config['Runtime']}")
    print(f"  Handler: {config['Handler']}")
    print(f"  Timeout: {config['Timeout']}s")
    print(f"  Memory: {config['MemorySize']} MB")
    print(f"  Code Size: {config['CodeSize'] / 1024 / 1024:.2f} MB")
    
    if config['State'] != 'Active':
        print(f"\n[WARN] Function is not Active: {config['State']}")
        if 'StateReasonCode' in config:
            print(f"  Reason: {config['StateReasonCode']}")
    
    if config['LastUpdateStatus'] != 'Successful':
        print(f"\n[WARN] Last update was not successful: {config['LastUpdateStatus']}")
        if 'LastUpdateStatusReasonCode' in config:
            print(f"  Reason: {config['LastUpdateStatusReasonCode']}")
    
    # Check environment variables
    if 'Environment' in config and 'Variables' in config['Environment']:
        env_vars = config['Environment']['Variables']
        print(f"\nEnvironment Variables:")
        for key in ['USE_S3_STORAGE', 'MONGODB_URI', 'S3_BUCKET_NAME', 'STAGE']:
            if key in env_vars:
                if 'MONGODB' in key or 'SECRET' in key:
                    print(f"  {key}: [HIDDEN]")
                else:
                    print(f"  {key}: {env_vars[key]}")
            else:
                print(f"  [WARN] {key}: NOT SET")
    
except Exception as e:
    print(f"[ERROR] Error: {str(e)}")

# Check recent logs
print("\n" + "="*60)
print("Checking CloudWatch Logs (last 10 events)...")
try:
    logs_client = boto3.client('logs', region_name='ap-southeast-1')
    log_group = '/aws/lambda/debtor-portal-api-dev-api'
    
    # Get latest log stream
    streams = logs_client.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    
    if streams['logStreams']:
        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"Log Stream: {stream_name}\n")
        
        # Get log events
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=20,
            startFromHead=False
        )
        
        for event in events['events'][-10:]:
            message = event['message'].strip()
            if 'ERROR' in message or 'Error' in message or 'error' in message or 'Traceback' in message:
                print(f"[ERROR] {message}")
            elif 'WARNING' in message or 'Warning' in message:
                print(f"[WARN] {message}")
            else:
                print(f"   {message}")
    else:
        print("No log streams found")
        
except Exception as e:
    print(f"[ERROR] Could not fetch logs: {str(e)}")
