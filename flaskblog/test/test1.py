import boto3
from botocore.exceptions import ClientError
ec2 = boto3.client('ec2', region='')
try:
    response = ec2.describe_instances()
    print(response)
except ClientError as e:
    print(e)
