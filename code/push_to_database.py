from google.cloud.sql.connector import Connector
import json
import sqlalchemy
import pandas as pd
import logging
import os
from google.cloud import pubsub_v1
from concurrent import futures
import datetime


PROJECT_ID = os.environ.get("project_id")
REGION = os.environ.get("region")
INSTANCE_NAME = os.environ.get("instance_name")
DB_USER = os.environ.get("db_user")
DB_PASS = os.environ.get("db_pass")
DB_NAME = os.environ.get("db_name")

INSTANCE_CONNECTION_NAME = f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"

SUBSCRIPTION_ID = os.environ.get("subscription_id")

def push_to_database(event, context):
    logging.basicConfig(level=logging.INFO)
    # initialize Connector object

    def ingest_to_db(json_response):

        connector = Connector()

        # function to return the database connection object
        def getconn():
            conn = connector.connect(
                INSTANCE_CONNECTION_NAME,
                "pymysql",
                user=DB_USER,
                password=DB_PASS,
                db=DB_NAME
                )
            print(INSTANCE_CONNECTION_NAME)
            return conn

        
        # create connection pool with 'creator' argument to our connection object function
        pool = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=getconn,
        )

        # connect to connection pool
        with pool.connect() as db_conn:
            # create weather_Data table in our weather_db database
            db_conn.execute(
            sqlalchemy.text(
                    """CREATE TABLE IF NOT EXISTS weather_data (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    lat FLOAT NOT NULL,
                    lon FLOAT NOT NULL, 
                    temperature_c FLOAT NOT NULL,
                    feelslike_c FLOAT NOT NULL, 
                    humidity FLOAT NOT NULL,
                    last_updated timestamp,
                    wind_kph FLOAT); """)
                )
            # insert data into our weather_data table
            insert_stmt = sqlalchemy.text(
                "INSERT INTO weather_db.weather_data (lat, lon, temperature_c, feelslike_c, humidity, last_updated, wind_kph) VALUES (:lat, :lon, :temperature_c, :feelslike_c, :humidity, :last_updated, :wind_kph)",
                )
            data = pd.json_normalize(json_response)
            mask = ["location.lat", "location.lon", "current.temp_c", "current.feelslike_c", "current.humidity","current.last_updated","current.wind_kph"]
            data_to_ingest = data[mask]
            lat, lon, temp_c, feelslike_c, humidity, last_updated, wind_kph = [row.values[0] for col, row in data_to_ingest.items()]

            db_conn.execute(insert_stmt, parameters={"lat": lat, "lon": lon, "temperature_c": temp_c,
                                "feelslike_c": feelslike_c, "humidity":humidity, "last_updated": last_updated,
                                "wind_kph":wind_kph})
        
            db_conn.commit()
        
            print(list(db_conn.execute(sqlalchemy.text("SHOW DATABASES;"))))
        
            results = db_conn.execute(sqlalchemy.text("SELECT * FROM weather_db.weather_data")).fetchall()

            # show results
            for row in results:
                print(row)

    subscriber = pubsub_v1.SubscriberClient()
        # The `subscription_path` method creates a fully qualified identifier
        # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    def callback(message):
        logging.info("Received %s", message)
        decoded_data = message.data.decode('utf-8')
        json_data = json.loads(decoded_data)
        ingest_to_db(json_data)
        message.ack()


    future = subscriber.subscribe(subscription_path, callback=callback)

    with subscriber:
        try:
            print(f"i enter here: {future}, \n {future.result()}")
            future.result()
        except futures.TimeoutError:
            future.cancel()  # Trigger the shutdown.
            future.result()  # Block until the shutdown is complete.
