import json
import boto3
import time
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])


def lambda_handler(event, context):
    batch_item_failures = []
    
    for record in event.get('Records', []):
        try:
            body = json.loads(record['body'])
            webhook_id = body.get('webhook_id')
            data = body.get('data')
            
            # Procesamiento asincrónico (simular 2s para pruebas)
            time.sleep(2)
            
            # Buscar el item
            response = table.query(
                KeyConditionExpression='webhook_id = :id',
                ExpressionAttributeValues={':id': webhook_id}
            )
            
            if response['Items']:
                created_at = response['Items'][0]['created_at']
                
                # Actualizar DynamoDB
                table.update_item(
                    Key={
                        'webhook_id': webhook_id,
                        'created_at': created_at
                    },
                    UpdateExpression='SET #status = :status, processed_data = :data',
                    ExpressionAttributeNames={
                        '#status': 'status'
                    },
                    ExpressionAttributeValues={
                        ':status': 'COMPLETED',
                        ':data': {'processed': True, 'timestamp': int(time.time() * 1000)}
                    }
                )
        
        except Exception as e:
            batch_item_failures.append({'itemId': record['messageId']})
    
    return {'batchItemFailures': batch_item_failures}
