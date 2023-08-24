import json
import requests
import logging
import os
from google.cloud import pubsub_v1


BASE_URL = os.environ.get("base_url")
API_KEY = os.environ.get("api_token")
Q = os.environ.get("q")

PROJECT_ID = os.environ.get("project_id")
REGION = os.environ.get("region")


TOPIC_ID = os.environ.get("topic_id")

def pull_from_api(event, context):
    logging.basicConfig(level=logging.INFO)
    
    # insert entries into table
    response = requests.get(f"{BASE_URL}?key={API_KEY}&q={Q}")
    json_response = response.json()       
    
    # publish data to the topic
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    message = json.dumps(json_response).encode("utf-8")
    future1 = publisher.publish(topic_path, message)
    print(future1.result())
