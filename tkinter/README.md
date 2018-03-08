# Using Mappening's Internal Tools

## Overview
GUI to ease checking/correcting location JSON data from scraping Facebook

## Built With
- Tkinter
- Selenium
- Google Chrome/chromedriver
- mLab: Database-as-a-Service cloud-hosted MongoDB
- Pymongo: Database Connector between MongoDB and Flask

## Setting Up the Environment
- Get the `.env` file which contains sensitive information from a dev and add it to tkinter/
- (Optional) use the *.ttf font files to get the fonts used by tkinter
- If you have `pip` installed:
  - `make setup` of `make sudo-setup`
  - If this fails:
    - Install MiniConda from this bash script: [https://conda.io/miniconda.html](https://conda.io/miniconda.html)
      - `chmod +x Miniconda2-latest-WHATEVER-VERSION.sh`
      - `./Miniconda2-latest-WHATEVER-VERSION.sh`
    - Update conda if necessary: `conda update -n base conda`
    - Create conda environment: `conda create --name myenv pip python=2`
    - Activate conda env: `conda activate myenv`
    - `make setup`
    - Add tkinter/ folder to your path
      - `export PATH=$PATH:/path/to/Mappening-Backend/tkinter/`
    - Hopefully it works now :\
    - Deactivate conda env: `conda deactivate`
    - (Optional) remove conda env: `conda env remove --name myenv`
- UCLA_WIFI not UCLA_WEB

## Processing Unknown Locations
- `unknown_locations` is a collection of locations scraped from Facebook events that don't have corresponding location data
- `tkinter_UCLA_locations` is a duplicate of `unknown_locations` that will be modified by `tkinterUCLA.py`
  - Process these unknown event locations with `make ucla`
  - Confirm whether or not the location name is part of UCLA/Westwood area, otherwise reject
- Once `tkinter_UCLA_locations` has been processed:
  - Populate `tkinter_unknown_locations` with the unknown locations and whatever location data our locations API can find
    - `curl -d -X POST http://localhost:5000/api/test_unknown_locations`
    - If out locations API doesn't find any info, adds location to `tkinter_TODO_locations`
  - Process the unknown locations that have been processed by our locations API
    - `make unknown`
    - Takes location data in `tkinter_unknown_locations`
    - Correct: added to `tkinter_known_locations`
    - Wrong: updated and kept in `tkinter_unknown_locations` for secondary approval
    - Location name doesn't match what our locations API found: added to `tkinter_TODO_locations` alongside locations that our locations API didn't find additional info for
