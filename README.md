# Mappening-Backend

## Documentation
Hosted on GitHub Pages at http://ucladevx.com/Mappening-Backend/

## Setting Up the Environment
- Follow instructions in main [Mappening](https://github.com/ucladevx/Mappening) repository
- Get the `.env` file which contains sensitive information from a dev and add it to `src/mappening/utils/`
- Build the base image that contains all dependencies that are fairly static but take a while to install
  - `make build-base`
- NOTE: the database connection doesn't seem to work over UCLA_WEB wifis, a more secure connection is needed (UCLA_WIFI)

## How to Run Backend Locally

- Build and run container using local Postgres database
  - `make dev`
  - To use production database (not recommended for local development):
    - `make prod`
- Navigate to [http://localhost](http://localhost)
- Access flask api directly at port [5000](http://localhost:5000/)
  - Use `localhost:5000/api/<insert_api_route_here>`
  - e.g. `localhost:5000/api/events`
- Stop running with `CTRL+C` or `make stop` in a separate terminal window

## Repo Breakdown

- Database config/data in `/database`
- Backend source code in `src/`
- tkinter GUIs in `tkinter/`
- Autodocumentation in `docs/`
- Beautiful Soup Scraping in `scraping/`
