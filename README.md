# Webhook Asincrónico

Arquitectura: API Gateway → Lambda Receiver → SQS → Lambda Processor → DynamoDB

## Estructura

```
.github/workflows/
  deploy.yml           # GitHub Actions deployment
cloudformation/
  template.yaml        # CloudFormation template
lambdas/
  receiver/
    lambda_function.py # Responde rápido (<2s)
    requirements.txt
  processor/
    lambda_function.py # Procesa asincronicamente
    requirements.txt
```

## Setup

### Prerequisitos

1. Bucket S3 para código Lambda: `your-bucket-name`
2. IAM Role para GitHub Actions: `arn:aws:iam::ACCOUNT:role/github-actions-role`
3. Secrets configurados:
   - `AWS_ACCOUNT`: ID de cuenta AWS
   - `LAMBDA_BUCKET`: Nombre del bucket S3

### Despliegue Manual

```bash
# Package y upload
mkdir build-receiver && cd lambdas/receiver && pip install -r requirements.txt -t ../../build-receiver/ && cp lambda_function.py ../../build-receiver/ && cd ../../build-receiver && zip -r ../receiver.zip .

mkdir build-processor && cd ../processor && pip install -r requirements.txt -t ../../build-processor/ && cp lambda_function.py ../../build-processor/ && cd ../../build-processor && zip -r ../processor.zip .

aws s3 cp receiver.zip s3://your-bucket/webhook-receiver-v1.0.0.zip
aws s3 cp processor.zip s3://your-bucket/webhook-processor-v1.0.0.zip

# Deploy CloudFormation
aws cloudformation create-stack \
  --stack-name webhook-dev \
  --template-body file://cloudformation/template.yaml \
  --parameters \
    ParameterKey=Env,ParameterValue=dev \
    ParameterKey=LambdaCodeBucket,ParameterValue=your-bucket \
    ParameterKey=ReceiverCodeKey,ParameterValue=webhook-receiver-v1.0.0.zip \
    ParameterKey=ProcessorCodeKey,ParameterValue=webhook-processor-v1.0.0.zip \
  --capabilities CAPABILITY_NAMED_IAM
```

### Despliegue Automático (GitHub Actions)

```bash
git tag v1.0.0-dev
git push --tags
```

El workflow se ejecutará automáticamente.

## API

```bash
curl -X POST https://api-endpoint/webhook \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Respuesta
{"webhook_id": "uuid", "status": "PENDING"}
```

## Arquitectura

- **Receiver**: Valida, guarda en DynamoDB, envía a SQS → responde 202 (<2s)
- **Processor**: Lee SQS, procesa (17+ seg), actualiza DynamoDB
- **DynamoDB**: Estado de webhooks (PENDING → COMPLETED)
- **SQS**: Cola de procesamiento con DLQ
