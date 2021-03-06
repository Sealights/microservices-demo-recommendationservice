import os
import grpc

import boto3
from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor

import demo_pb2
import demo_pb2_grpc

from logger import getJSONLogger
logger = getJSONLogger('recommendationservice-server')

Boto3SQSInstrumentor().instrument()

region_name = os.environ.get('AWS_REGION', "us-east-2")
aws_access_key_id = os.environ.get('AWS_US_ACCESS_KEY_ID', "")
aws_secret_access_key = os.environ.get('AWS_US_SECRET_ACCESS_KEY', "")
sqs_wait_time_sec = os.environ.get('SQS_WAIT_TIME_SEC', "20") 
sqs_max_messages = os.environ.get('SQS_MAX_MESSAGES', "5") 
endpoint_notification_url = os.environ.get('AWS_NOTIFICATION_SQS_QUEUE_URL', "") 
queue_loop_quantity = os.environ.get('QUEUE_LOOP_QUANTITY', "0") 

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
          
def call_product_catalog_service():
  try:
    catalog_addr = os.environ.get('PRODUCT_CATALOG_SERVICE_ADDR', '')
    channel = grpc.insecure_channel(catalog_addr)
    product_catalog_stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)
    product_catalog_stub.ListProducts(demo_pb2.Empty())
  except Exception as e: 
       logger.error('Error during calling product catalog service {} .'.format(e))     

def process_and_send_loop_message(message):
  leftLoopQuantity = 0
  try:
    leftLoopQuantity = int(message['Body'])
  except Exception as e: 
    leftLoopQuantity = int(queue_loop_quantity)    
  try:
    if leftLoopQuantity != 0:
      response = send_notification_message(message, leftLoopQuantity - 1)
      logger.info('SQS send message, response {} .'.format(response['MessageId']))    
  except Exception as e: 
       logger.error('Error during process loop messages {} .'.format(e))  
  return leftLoopQuantity       

def process_queue():  
  while True:
    response = receive_message()
    if "Messages" in response:   
      for message in response["Messages"]:
        logger.info(f"Recived message: {message}")
        leftLoopQuantity = process_and_send_loop_message(message)
        delete_message(message) 
        if leftLoopQuantity == 0:
          call_product_catalog_service() 
         
