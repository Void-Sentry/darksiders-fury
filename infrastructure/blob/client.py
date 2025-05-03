import boto3
import os

blob_client = boto3.client(
    's3',
    endpoint_url=os.getenv('BLOB_URL'),
    aws_access_key_id=os.getenv('BLOB_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('BLOB_SECRET_ACCESS_KEY'),
    region_name=os.getenv('BLOB_REGION_NAME'),
)
