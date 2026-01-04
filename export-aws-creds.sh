#!/bin/bash
# Helper script to export AWS credentials for Pulumi
# Usage: source export-aws-creds.sh

eval $(python3 << 'EOF'
import boto3
session = boto3.Session()
credentials = session.get_credentials()
if credentials:
    print(f"export AWS_ACCESS_KEY_ID={credentials.access_key}")
    print(f"export AWS_SECRET_ACCESS_KEY={credentials.secret_key}")
    if credentials.token:
        print(f"export AWS_SESSION_TOKEN={credentials.token}")
    print(f"export AWS_REGION={session.region_name}")
    print("echo 'AWS credentials exported successfully'", file=__import__('sys').stderr)
else:
    print("echo 'ERROR: No AWS credentials found'", file=__import__('sys').stderr)
    print("exit 1")
EOF
)