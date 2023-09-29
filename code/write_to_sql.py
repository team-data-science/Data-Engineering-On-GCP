import base64
import json
import os
import functions_framework
import sqlalchemy
from sqlalchemy import text
from google.cloud.sql.connector import Connector

PROJECT_ID = os.environ.get("project_id")
REGION = os.environ.get("region")
INSTANCE_NAME = os.environ.get("instance_name")
DB_USER = os.environ.get("db_user")
DB_PASS = os.environ.get("db_pass")
DB_NAME = os.environ.get("db_name")

INSTANCE_CONNECTION_NAME = f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def write_to_database(cloud_event):

    def ingest_to_db(str_record):
	    # function to return the database connection object
        connector = Connector()
        
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

        # load the json string into a dictionary
        dict_record = json.loads(str_record)
        
        
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
                    wind_kph FLOAT,
                    name varchar(255)); """)
                )
            
            # craete the general insert statement which we use to put the data into the database
            insert_stmt = sqlalchemy.text(
            "INSERT INTO weather_db.weather_data ( lat, lon, temperature_c, feelslike_c, humidity, last_updated, wind_kph, name) VALUES ( :lat, :lon, :temperature_c, :feelslike_c, :humidity, :last_updated, :wind_kph, :name);" )

            #slice the dicitionarys' nested data into individual ones for location and current
            location = dict_record['location']
            current = dict_record['current']
            
            #get the date and the location into variables
            dt = current['last_updated']
            city = location['name']
            
            #create a query that tests if we already have data for this timestamp and location and execute it
            query = "SELECT * FROM weather_db.weather_data where last_updated='" + dt + "' and name='" + city +"';"
            print(query)
            results = db_conn.execute(text(query))

            # check if there are results 
            if len(results.fetchmany())==0:
                # if there's no result we are good to write the datapoint to the db
                print("\n****************** Writing to SQL database ***********************")
                db_conn.execute(insert_stmt, parameters={ "lat": location['lat'], "lon": location['lon'], "temperature_c": current['temp_c'],
                                "feelslike_c": current['feelslike_c'], "humidity":current['humidity'], "last_updated": dt,
                                "wind_kph":current['wind_kph'], "name": city})
                db_conn.commit()
            else:
                # if there's a result that datapoint is already in the database. Don't write it
                print("\n******************  SQL already has records ***********************")

            db_conn.close()

    # get the message from the event that triggered this run
    t_record = base64.b64decode(cloud_event.data["message"]["data"])
    print(t_record)

    # just make sure that it's formated as utf-8 string
    str_record = str(t_record,'utf-8')
    print (str_record)

    # start the writing into the database
    ingest_to_db(str_record)