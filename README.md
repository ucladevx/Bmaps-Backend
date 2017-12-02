# Mappening-Backend

## Overview
A single platform for events all over campus. Mappening helps raise awareness of events by aggregating event information from various sources of advertising.

## Built With
* Flask (Port 5000): Web microframework for Python
* mLab: Database-as-a-Service cloud-hosted MongoDB
* Pymongo: Database Connector between MongoDB and Flask
* nginx (Port 80): Server for static files, forwards requests to backend and serves results
* AWS EC2/Elastic Container Service for deployment

## Setting Up the Environment
* Download [Docker](https://www.docker.com) and [Docker-Compose](https://github.com/docker/compose/releases) release 1.16.1.  
* Clone this repository 
  * `git clone https://github.com/ucladevx/Mappening-Backend.git`  
* `cd Mappening-Backend`
* Clone the frontend repository to the name `node_app`
  * `git clone https://github.com/ucladevx/Mappening-Frontend.git node_app`
  * `cd node_app`
  * Install necessary packages
    * `npm install`

## How to Run Locally
* `cd` to the repository.
* Build + Run with `make run`
  * Just build with `make build-local`
* Navigate to `localhost`
  * Access static files with nginx with `/` or `/imgs`
    * e.g. `localhost/imgs`
  * Access flask api by forwarding requests through nginx
    * Use `/api/v1/insert_api_route_here`
    * e.g. `localhost/api/v1/events`
    * nginx forwards to AWS to serve api requests. Be aware of this if trying to test changes locally.
  * Can also access flask server directly at port 5000
    * e.g. `localhost:5000/api/events`
    * Better for testing local changes
* Stop running with `CTRL+C` or with `make stop`
* Reset containers/images with `make reset`

## How to Deploy on AWS
* `cd` to the repository.
* Build + Push a new image to AWS with `make push`
  * Just build with `make build`
* In separate tab/window run `make ssh` to login to AWS instance
* Deploy with `make deploy`
* Navigate to `52.53.72.98`
  * Access static files with nginx with `/` or `/imgs`
    * e.g. `52.53.72.98/imgs`
  * Access flask api by forwarding requests through nginx
    * Use `/api/v1/insert_api_route_here`
    * e.g. `52.53.72.98/api/v1/events`
  * Can also access flask server directly at port 5000
    * e.g. `52.53.72.98:5000/api/events`
* Stop running on ubuntu with `CTRL+C`
