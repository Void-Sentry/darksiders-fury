from .client import blob_client
import os

def initialize_blob():
    existing_buckets = blob_client.list_buckets()
    bucket_name = os.getenv('BLOB_BUCKET_NAME')

    if not any(b['Name'] == bucket_name for b in existing_buckets['Buckets']):
        blob_client.create_bucket(Bucket=bucket_name)
