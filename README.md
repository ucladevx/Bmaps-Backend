# Mappening-Backend

## Overview
A single platform for events all over campus. Mappening helps raise awareness of events by aggregating event information from various sources of advertising.

## Prerequisites
Download [Docker](https://www.docker.com) and [Docker-Compose](https://github.com/docker/compose/releases) release 1.16.1.  
Clone this repository with `git clone https://github.com/ucladevx/Mappening-Backend.git` 

## Built With
* Flask: Web microframework for Python
* mLab: Database-as-a-Service cloud-hosted MongoDB
* Pymongo: Database Connector between MongoDB and Flask
* nginx: Server for static files

## How to Run on AWS
* `cd` to the repository.
* Build + Push a new image to AWS with `make push`
  * Just build with `make build`
* In separate tab/window run `make ssh` to login to AWS instance
* Deploy with `make deploy`
* Navigate to 52.53.197.64
  * Access static files with nginx with `/` or `/imgs`
    * e.g. `52.53.197.64/imgs`
  * Access flask api by forwarding requests through nginx
    * Use `/api/v1/insert_api_route_here`
    * e.g. `52.53.197.64/api/v1/events`
* Stop running on ubuntu with `CTRL+C`
