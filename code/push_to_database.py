from google.cloud.sql.connector import Connector
import json
import sqlalchemy
from sqlalchemy import text
import pandas as pd
import logging
import os
from google.cloud import pubsub_v1
from concurrent import futures
import datetime

# get the input variables 
PROJECT_ID = os.environ.get("project_id")
REGION = os.environ.get("region")
INSTANCE_NAME = os.environ.get("instance_name")
DB_USER = os.environ.get("db_user")
DB_PASS = os.environ.get("db_pass")
DB_NAME = os.environ.get("db_name")
SUBSCRIPTION_ID = os.environ.get("subscription_id")

# create the instance connection name for the connection
INSTANCE_CONNECTION_NAME = f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"

def push_to_database(event, context):
    # config the logger to only show warnings and up
    logging.basicConfig(level=logging.WARNING)
    

    def ingest_to_db(json_response):
        # initialize Connector object
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
            
            # create weather_Data table in our weather_db database if it doesn't exist
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
                        wind_kph FLOAT,
                        name varchar(255)); """)
                )
            
            # create the insert statement for the database
            insert_stmt = sqlalchemy.text(
            "INSERT INTO weather_db.weather_data ( lat, lon, temperature_c, feelslike_c, humidity, last_updated, wind_kph, name) VALUES ( :lat, :lon, :temperature_c, :feelslike_c, :humidity, :last_updated, :wind_kph, :name);" )
            
            # normalize the json into a pandas dataframe
            data = pd.json_normalize(json_response)

            # get the date & city.
            dt = str(data['current.last_updated'].values[0])
            city = str(data['location.name'].values[0])
            
            # create a mask for all the columns that we need and then just get these
            mask = ["location.lat", "location.lon", "current.temp_c", "current.feelslike_c", "current.humidity","current.last_updated","current.wind_kph", "location.name"]
            data_to_ingest = data[mask]

            # put the column values from the dataframe into variables
            lat, lon, temp_c, feelslike_c, humidity, last_updated, wind_kph, name = [row.values[0] for col, row in data_to_ingest.items()]
            
            #create a query that tests if we already have data for this timestamp and location and execute it
            query = "SELECT * FROM weather_db.weather_data where last_updated='" + dt + "' and name='" + city +"';"
            print(query)
            results = db_conn.execute(text(query))

            # check if there are results 
            if len(results.fetchmany())==0:
                # if there's no result we are good to write the datapoint to the db
                print("\n****************** Writing to SQL database ***********************")
                db_conn.execute(insert_stmt, parameters={"lat": lat, "lon": lon, "temperature_c": temp_c,
                                        "feelslike_c": feelslike_c, "humidity":humidity, "last_updated": last_updated,
                                        "wind_kph":wind_kph, "name":name})
                db_conn.commit()
            else:
                # if there's a result that datapoint is already in the database. Don't write it
                print("\n******************  SQL already has records ***********************")

            db_conn.close()


    subscriber = pubsub_v1.SubscriberClient()
        # The `subscription_path` method creates a fully qualified identifier
        # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    # callback will be done when a new message arrives
    def callback(message):
        print(f"Received from Pub/Sub: {message}")
        decoded_data = message.data.decode('utf-8')
        json_data = json.loads(decoded_data)
        ingest_to_db(json_data)
        message.ack()

    # subscribe to the pub/sub message queue
    future = subscriber.subscribe(subscription_path, callback=callback)

    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first. Let's close the connection after 5 seconds
            future.result(timeout= 5)
        except futures.TimeoutError:
            future.cancel()  # Trigger the shutdown.
            future.result()  # Block until the shutdown is complete.