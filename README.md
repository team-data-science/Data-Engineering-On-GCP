## Architecture of the course
<img src="https://github.com/team-data-science/course-gcp/blob/main/images/Architecture.png">


1. Set the environment
   
2. Create a GCP Project
<br/>Project name: weather-api-project

3. Activate required APIs with
```
gcloud services enable cloudfunctions.googleapis.com sqladmin.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com eventarc.googleapis.com compute.googleapis.com servicenetworking.googleapis.com pubsub.googleapis.com logging.googleapis.com
```
4. Setting up a Scheduler
- [ ] Cron scheduler:
Name: weather_call<br/> 
Region: us-central1<br/> 
Description: Information about the job<br/> 
Frequency: 0 * * * *<br/> 
Timezone: UTC<br/> 

- [ ] Pub/Sub
Topic ID: weather_calls<br/>
Message body: update<br/>

5. Setting up CloudSQL(MySQL)
- [ ] Compute Engine  
Name: weather-vm<br/>
Machine configuration >> general-purpose:<br/>
Series N1<br/>
Machine type: f1-micro<br/>
Allow http and https traffic<br/>
 - [ ] VPC Network  
Name: weather-vm-ip<br/>
 - [ ] Cloud SQL
Database Engine: MySQL 8.0<br/>
Instance ID: weather-db<br/>
Password: admin1234<br/>
Preset: Development<br/>
Machine type: Lightweight 1vCPU 3.75GB<br/>
Storage: SSD 10GB with automatic storage increases<br/>
Network >> Name: connection-db-vm<br/>
--VM IP address reserved<br/>
- [ ] Compute Engine  
--install mysql server<br/>
```
sudo apt-get update
sudo apt-get install \
default-mysql-server
```
--log in to mysql database<br/>
```
mysql -h <weather-vm-ip (external static IP)> \
-u root -p
```
For example,
```
mysql -h 34.72.233.196 \
-u root -p
```
--create a weather_db database.<br/>
```
 CREATE DATABASE weather_db;
 SHOW DATABASES; 
```
--create a weather_db.weather_data table<br/>
```
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
- [ ] Pub/Sub topic<br/>
Topic ID: apiweather-extract<br/>

- [ ] Pub/Sub subscription<br/>
Subscription ID: apiweather-extract-subscription<br/>

7. Creating a Cloud Function
- [ ] Function name: pull-weather-data<br/>   
Region: us-central1<br/> 
Environment: 1st gen<br/> 
Memory: 512 MiB<br/> 
Environmental variables:<br/> 
   -- api_token: your weather API token<br/> 
   -- base_url: http://api.weatherapi.com/v1/current.json<br/> 
   -- q: your country<br/> 
   -- project_id: yourProjectId<br/> 
   -- region: us-central1<br/> 
   -- topic_id: apiweather-extract<br/> 
         --- Entry point: pull_from_api<br/> 
         --- main.py - https://github.com/team-data-science/course-gcp/blob/main/code/pull_from_api.py<br/> 
         --- requirements.txt - https://github.com/team-data-science/course-gcp/blob/main/code/pull-weather-data_requirements.txt 

- [ ] Function name: weather-data-to-db<br/>
Region: us-central1<br/> 
Environment: 1st gen<br/> 
Memory: 512 MiB<br/> 
Environmental variables:<br/> 
   -- project_id: yourProjectId<br/> 
   -- region: us-central1<br/> 
   -- db_user: root<br/> 
   -- db_pass: admin1234<br/> 
   -- db_name: weather_db<br/> 
   -- instance_name: weather-db<br/> 
   -- subscription_id: apiweather-extract-subscription<br/> 
         --- Entry point: push_to_database<br/> 
         --- main.py - https://github.com/team-data-science/course-gcp/blob/main/code/push_to_database.py<br/> 
         --- requirements.txt - https://github.com/team-data-science/course-gcp/blob/main/code/weather-data-to-db_requirements.txt<br/> 
<br/> Testing - https://github.com/team-data-science/course-gcp/blob/main/code/testing.json 

8. Connect CloudSQL to Looker Studio - https://lookerstudio.google.com/<br/>
Instance Connection Name<br/>
Database name: weather_db<br/>
Username: root<br/>
Password: admin1234<br/>

9. Making Dashboards
```
CONCAT(lat,",",lon)
```
