
import os
import random
from flask import Flask, request
import grpc
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from waitress import serve
import json
import demo_pb2
import demo_pb2_grpc
from logger import getJSONLogger
logger = getJSONLogger('recommendationservice-server')
    
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/listrecomendation", methods=['GET'])
def ListRecommendations():
    products_ids = request.args.get('product_ids')
    req_product_ids = []
    if products_ids != None:
      req_product_ids = request.args.get('product_ids').split(',')

    max_responses = 5
    catalog_addr = os.environ.get('PRODUCT_CATALOG_SERVICE_ADDR', '')
    channel = grpc.insecure_channel(catalog_addr)
    product_catalog_stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)
    cat_response = product_catalog_stub.ListProducts(demo_pb2.Empty())
    
    product_ids = [x.id for x in cat_response.products]
    filtered_products = list(set(product_ids)-set(req_product_ids))
    num_products = len(filtered_products)
    num_return = min(max_responses, num_products)
  
    indices = random.sample(range(num_products), num_return)

    prod_list = [filtered_products[i] for i in indices]
    logger.info("[Recv ListRecommendations] product_ids={}".format(prod_list))
    
    return json.dumps({"product_ids": prod_list})

def RunHttpServer():   
  try:
    logger.info("Starting http serer on port:{}".format(os.environ.get('HTTP_PORT', "8082")) )
    serve(app, host="0.0.0.0", port=os.environ.get('HTTP_PORT', "8082"))
  except Exception as e: 
       logger.error('Error during starting http server {} .'.format(e))   
    