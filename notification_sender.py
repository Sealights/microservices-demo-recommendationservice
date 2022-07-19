import os

import boto3
from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor


import demo_pb2
import demo_pb2_grpc

Boto3SQSInstrumentor().instrument()

from logger import getJSONLogger
logger = getJSONLogger('notificationsender')

region_name = os.environ.get('AWS_REGION', "us-east-2")
aws_access_key_id = os.environ.get('AWS_US_ACCESS_KEY_ID', "")
aws_secret_access_key = os.environ.get('AWS_US_SECRET_ACCESS_KEY', "")
sqs_wait_time_sec = os.environ.get('SQS_WAIT_TIME_SEC', "20") 
sqs_max_messages = os.environ.get('SQS_MAX_MESSAGES', "5") 
endpoint_notification_url = os.environ.get('AWS_NOTIFICATION_SQS_QUEUE_URL', "") 

sqs = boto3.client('sqs',
      region_name=region_name,
      aws_access_key_id=aws_access_key_id,
      aws_secret_access_key=aws_secret_access_key)  

def delete_message(message):
  receipt_handle = message['ReceiptHandle'] 
  sqs.delete_message(
      QueueUrl=endpoint_notification_url,
      ReceiptHandle=receipt_handle
  )

def receive_message():
  return sqs.receive_message(
      QueueUrl=endpoint_notification_url,
      MaxNumberOfMessages=int(sqs_max_messages),
      AttributeNames=[
        'SentTimestamp'
      ],
      VisibilityTimeout=1,
      WaitTimeSeconds=int(sqs_wait_time_sec),
      MessageAttributeNames=[
        'All'
      ],
  )
  
def send_notification_message(message, bodyValue):
  if endpoint_notification_url == "":
    return

  return sqs.send_message(
        QueueUrl='https://sqs.us-east-2.amazonaws.com/474620256508/EmailQueue',
        DelaySeconds=10,
        MessageBody=str(bodyValue) 
    )  

def process_queue():  
  while True:
    response = receive_message()
    if "Messages" in response:   
      for message in response["Messages"]:
          logger.info(f"Recived message: {message}")
          try:
            numberValue = 0
            try:
              numberValue = int(message['Body'])
              numberValue = numberValue - 1
              if numberValue == 0:
                demo_pb2_grpc.ProductCatalogService.ListProducts(demo_pb2.Empty())
                delete_message(message) 
                return
            except:
              numberValue = 2               
            response = send_notification_message(message, numberValue)
            logger.info('SQS send message, response {} .'.format(response['MessageId']))
          except Exception as e: 
            logger.error('Error during sending message to notification sqs {} .'.format(e))       
          delete_message(message) 
          