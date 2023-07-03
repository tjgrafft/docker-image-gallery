import os
import logging
import boto3
from botocore.exceptions import ClientError

def create_bucket(region=None):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    bucket_name = os.getenv('S3_IMAGE_BUCKET')

    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def put_object(key, value):
    bucket_name = os.getenv('S3_IMAGE_BUCKET')
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=value)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def get_object(key):
    bucket_name = os.getenv('S3_IMAGE_BUCKET')
    try:
        s3_client = boto3.client('s3')
        result = s3_client.get_object(Bucket=bucket_name, Key=key)
    except ClientError as e:
        logging.error(e)
        return None
    return result
    

def main():
    #create_bucket('us-east-1')
    #put_object('banana', 'green')
    print(get_object('banana')['Body'].read())

if __name__ == '__main__':
    main()

