import requests
import json

# Test endpoint to see what environment variables are available
url = "https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev/api/test/email/"

response = requests.get(url)
print("Response:", response.text)

# The response shows the config, let's see what it contains
data = response.json()
if 'config' in data:
    print("\nEmail Config:")
    for key, value in data['config'].items():
        if 'PASSWORD' in key:
            print(f"{key}: {'***' if value else 'EMPTY'}")
        else:
            print(f"{key}: {value}")