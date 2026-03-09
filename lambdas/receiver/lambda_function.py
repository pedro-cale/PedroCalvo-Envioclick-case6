import json
import boto3
import uuid
import time
import os

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

table = dynamodb.Table(os.environ['TABLE_NAME'])
queue_url = os.environ['QUEUE_URL']


def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        
        if not body:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Empty body'}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        webhook_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        table.put_item(
            Item={
                'webhook_id': webhook_id,
                'created_at': timestamp,
                'status': 'PENDING',
                'data': body
            }
        )
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'webhook_id': webhook_id,
                'data': body
            })
        )
        
        return {
            'statusCode': 202,
            'body': json.dumps({
                'webhook_id': webhook_id,
                'status': 'PENDING'
            }),
            'headers': {'Content-Type': 'application/json'}
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
