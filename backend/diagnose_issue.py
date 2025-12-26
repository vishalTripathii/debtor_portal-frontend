import boto3

print("=" * 70)
print("ROOT CAUSE ANALYSIS")
print("=" * 70)

s3 = boto3.client('s3', region_name='ap-southeast-1')
bucket = 'debtor-portal-api-dev-serverlessdeploymentbucket-rhgfzohvfm57'

print("\n1. Checking available Lambda packages in S3:")
response = s3.list_objects_v2(Bucket=bucket, Prefix='lambda')
for obj in response.get('Contents', []):
    if 'lambda' in obj['Key'].lower() and obj['Key'].endswith('.zip'):
        size_mb = obj['Size'] / 1024 / 1024
        print(f"   - {obj['Key']}: {size_mb:.2f} MB (Modified: {obj['LastModified']})")

print("\n2. Checking current Lambda function configuration:")
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
func = lambda_client.get_function(FunctionName='debtor-portal-api-dev-api')
config = func['Configuration']
print(f"   Runtime: {config['Runtime']}")
print(f"   Current Code Size: {config['CodeSize'] / 1024 / 1024:.2f} MB")
print(f"   State: {config['State']}")
print(f"   Last Update: {config['LastUpdateStatus']}")

print("\n3. Checking recent CloudWatch error logs:")
logs = boto3.client('logs', region_name='ap-southeast-1')
log_group = '/aws/lambda/debtor-portal-api-dev-api'

try:
    streams = logs.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    
    if streams['logStreams']:
        stream = streams['logStreams'][0]['logStreamName']
        events = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream,
            limit=50,
            startFromHead=False
        )
        
        errors = []
        for event in events['events']:
            msg = event['message'].strip()
            if any(x in msg for x in ['ERROR', 'Error', 'Traceback', 'ImportError', 'ModuleNotFoundError']):
                errors.append(msg)
        
        if errors:
            print("\n   ERRORS FOUND:")
            for err in errors[-10:]:  # Last 10 errors
                print(f"   {err[:200]}")
        else:
            print("   No recent errors found")
            
except Exception as e:
    print(f"   Could not fetch logs: {e}")

print("\n" + "=" * 70)
print("SOLUTION:")
print("=" * 70)
print("The working version was lambda-working-morning.zip (94.2 MB)")
print("We should restore that version and add ONLY the bulk operations code")
print("to it without changing Django or other dependencies.")
print("=" * 70)
