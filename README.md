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

## How To Run
* `cd` to the repository.
* Build + Run with `make run`
  * Just build with `make build`
* Navigate to http://localhost:5000
* Stop running with `CTRL+C` or with `make stop`
* Reset containers/images with `make reset`
