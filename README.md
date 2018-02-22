# Mappening-Backend

## Overview
A single platform for events across campus. Mappening helps raise awareness of events by aggregating event information from various sources of advertising. 

## Built With
- Python 2.7.14
- Flask (Port 5000): Web microframework for Python
- mLab: Database-as-a-Service cloud-hosted MongoDB
- Pymongo: Database Connector between MongoDB and Flask
- AWS EC2/Elastic Container Service for deployment
- Sphinx to automatically generate documentation

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
- Latest documentation is in the `_build` folder
- Actual auto-generated documentation in `_build_generated`. Some manual HTML changes to `_build`
- Minified js/css files in `_static`
- Manually changed "Classes" to "APIs": `<h2>APIs Documented<a class="headerlink" href="#classes-documented" title="Permalink to this headline">¶</a></h2>`
- Most manual changes for events.html
- basic.css remove div.body max and min width
- sphinx-autobuild with sudo pip, then `sphinx-autobuild . ./_build/html` and navigate to http://127.0.0.1:8000/events.html
- embed html using rst or something http://www.sphinx-doc.org/en/stable/rest.html
.field-name{min-width:85px;


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
