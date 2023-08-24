## Architecture of the course
<img src="https://github.com/team-data-science/dev-data-engineering-on-GCP/blob/main/1-Set_the_environment/Set%20the%20environment/Architecture.png">


1. Set the environment
   
2. Create a GCP Project
  Project name: weather-api-project

3. Activate required APIs with
```
gcloud services enable cloudfunctions.googleapis.com sqladmin.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com eventarc.googleapis.com compute.googleapis.com servicenetworking.googleapis.com pubsub.googleapis.com logging.googleapis.com
```
4. Setting up a Scheduler
- [ ] Cron scheduler:  
  Name: weather_call  
  Region: us-central1  
  Description → information about the job  
  Frequency: 0 * * * *  
  Timezone: UTC

- [ ] Pub/Sub topic ID: weather_calls
Message body: update

5. Setting up CloudSQL(MySQL)
- [ ] Compute Engine  
   name: weather-vm
   Machine configuration:
    * general-purpose
    * series N1
    * machine type f1-micro
    * llow http and https traffic
 - [ ] VPC Network  
    Name: weather-vm-ip
 - [ ] Cloud SQL
    * MySQL 8.0
    * Instance ID: weather-db
    * Password: admin1234
    * Development
    * Machine type: Lightweight 1vCPU 3.75GB
    * Storage: SSD 10GB with automatic storage increases
    * Network >> Name: connection-db-vm
        * VM IP address reserved
- [ ] Compute Engine  
--install mysql server
```
sudo apt-get update
sudo apt-get install \
default-mysql-server
```
--log in to mysql database
```
mysql -h 34.72.233.196 \
-u root -p
```
--create a weather_db database.
```
 CREATE DATABASE weather_db;
 SHOW DATABASES; 
```
--create a weather_db.weather_data table
CREATE TABLE IF NOT EXISTS weather_db.weather_data (
  	id INT PRIMARY KEY AUTO_INCREMENT,
  	lat FLOAT NOT NULL,
  	lon FLOAT NOT NULL,
  	temperature_c FLOAT NOT NULL,
  	feelslike_c FLOAT NOT NULL,
  	humidity FLOAT NOT NULL,
    last_updated timestamp,
  	wind_kph FLOAT);
```

6. Working-on-topic-subscription
- [ ] Pub/Sub topic
    * Topic ID: apiweather-extract
- [ ] Pub/Sub subscription
    * Subscription ID: apiweather-extract-subscription

7. Creating a Cloud Function
- [ ] Function name: pull-weather-data
    * Region: us-central1  
    * Environment: 1st gen  
    * Memory: 512 MiB  
    * Environmental variables:  
    *        api_token: your weather API token  
    *        base_url: http://api.weatherapi.com/v1/current.json  
    *        q: your country  
    *        project_id: weather-api-project  
    *        region: us-central1  
    *        topic_id: apiweather-extract

- [ ] Function name: pull-weather-data
    * Region: us-central1  
    * Environment: 1st gen  
    * Memory: 512 MiB  
    * Environmental variables:  
      *        api_token: your weather API token  
      *        base_url: http://api.weatherapi.com/v1/current.json  
      *        q: your country  
      *        project_id: weather-api-project  
      *        region: us-central1  
      *        topic_id: apiweather-extract  
        *        Entry point: pull_from_api

```
functions-framework==3.*
requests==2.28.2
google-cloud-pubsub==2.15.2
```
10. Connect CloudSQL to Looker Studio
11. Making Dashboards
