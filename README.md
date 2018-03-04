# Mappening-Backend

## Overview
A single platform for events across campus. Mappening helps raise awareness of events by aggregating event information from various sources of advertising. 

## Built With
- Python 2.7.14
- Flask (Port 5000): Web microframework for Python
- mLab: Database-as-a-Service cloud-hosted MongoDB
- Pymongo: Database Connector between MongoDB and Flask
- Facebook Graph API + Login/OAuth for getting event information and user authentication
- Google Maps/Places API Web Service for getting place information
- AWS EC2/Elastic Container Service for deployment
- Sphinx to automatically generate documentation
- Tkinter, Selenium, Google chromedriver for internal tools

## Setting Up the Environment
- Download [Docker](https://www.docker.com) and [Docker-Compose](https://github.com/docker/compose/releases) release 1.16.1.  
- Clone this repository 
  - `git clone https://github.com/ucladevx/Mappening-Backend.git`
- Get the `.env` file which contains sensitive information from a dev and add it to python_app/

## Generating Documentation with Sphinx
- Make sure required packages are installed
  - `make sphinx-setup`
- Read Sphinx help information
  - `make sphinx-help`
- Generate Sphinx documentation
  - `make html`
  - TODO: Check this with Hannah. `make clean`?? 
- Set up Sphinx Autobuild
  - `sudo pip install sphinx-autobuild`
  - `sphinx-autobuild . ./_build/html` from Mappening-Backend
  - Navigate to `http://127.0.0.1:8000/`
  - `CTRL-C` to stop autobuilding
- Latest documentation is in the `_build` folder
- Minified js/css files in `_static`
- Manual Changes with [reST](http://www.sphinx-doc.org/en/stable/rest.html):
  - Manually changed "Classes" to "APIs" in `index.html`
  - Removed div.body max and min width in `basic.css`
  - Added min-width to .field-name in `basic.css`

## How to Push Image to AWS ECS
- Enter the repository
  - `cd Mappening-Backend`
- Login, build, and push image to AWS
  - `make push`

## How to Run Backend Locally
- Build and run container
  - `make dev`
- Navigate to `localhost`
- Access flask api directly at port 5000
  - Use `localhost:5000/api/<insert_api_route_here>`
  - e.g. `localhost:5000/api/events`
- Stop running with `CTRL+C` or `make stop` in a separate terminal window

## More Info
- Check out the [frontend](https://github.com/ucladevx/Mappening-Frontend) repository
- Check out the [deployment](https://github.com/ucladevx/Mappening-Deployment) repository
  - Contains instructions for local development and production

## What's Next?
- Locations
  - Filter unknown locations using internal tkinter tools
  - See how accurate locations API is
  - Improve API accordingly
  - Integrate locations API with events API
  - Clean up/document!
- Events
  - Web Scraping!
