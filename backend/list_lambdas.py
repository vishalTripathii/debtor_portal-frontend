import boto3

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
response = lambda_client.list_functions()

print("Lambda functions containing 'debtor':")
for func in response['Functions']:
    if 'debtor' in func['FunctionName'].lower():
        print(f"  - {func['FunctionName']}")
