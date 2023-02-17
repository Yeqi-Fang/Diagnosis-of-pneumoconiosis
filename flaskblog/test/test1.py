import logging
import boto3
from botocore.exceptions import ClientError
import os


def upload_file(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


s3 = boto3.client('s3')
# with open(r"D:\scu\Innovation\Diagnosis of pneumoconiosis\flaskblog\static\profile_pics\0a3377e7f868a642.jpeg",
#           "rb") as f:
#     s3.upload_fileobj(f, "testing-for-flask-test")


upload_file(r'D:\scu\Innovation\Diagnosis of pneumoconiosis\flaskblog\static\profile_pics\0a3377e7f868a642.jpeg',
            'testing-for-flask-test', 'test-folder11/1.png')
