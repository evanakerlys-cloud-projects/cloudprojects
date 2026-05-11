import json
import boto3
import uuid
from datetime import datetime, timezone

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = 'securefile-audit-log'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-2:047385673852:securefile-notifications'

def lambda_handler(event, context):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        size = event['Records'][0]['s3']['object']['size']
        
        file_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'file_id': file_id,
            'filename': key,
            'bucket': bucket,
            'file_size': size,
            'timestamp': timestamp
        })
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='SecureFile: New Document Uploaded',
            Message=f'New file uploaded.\nFilename: {key}\nBucket: {bucket}\nSize: {size} bytes\nTimestamp: {timestamp}\nFile ID: {file_id}'
        )
        
        print(f'Processed file: {key} | File ID: {file_id}')
        return {'statusCode': 200, 'body': json.dumps('Success')}
        
    except Exception as e:
        print(f'Error: {str(e)}')
        raise
