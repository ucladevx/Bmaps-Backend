# Mappening-Backend

## Overview
A single platform for events all over campus. Mappening helps raise awareness of events by aggregating event information from various sources of advertising.

## Prerequisites
Download [Docker](https://www.docker.com) and clone this repository. 

## Built Using
* Flask : Web microframework for Python
* mLab : Database-as-a-Service cloud-hosted MongoDB
* Pymongo : Database Connector between MongoDB and Flask

## To Build
* `cd` to the repository.
* Build with `docker build -t mappening_backend .`
* Run with `docker run -p 5000:5000 -i -t mappening_backend`
* Navigate to localhost:5000
