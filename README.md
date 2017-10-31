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
* nginx: Serves static files

## How To Run
* `cd` to the repository.
* Build with `make build`
* Build + Run with `make run`
* Navigate to http://localhost:5000
* Stop with `CTRL+C in the terminal you ran it in or with make stop`
* Reset with `make reset`
