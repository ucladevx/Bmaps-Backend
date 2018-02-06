# Starter app.py that connects to mlab database

from flask import Flask, jsonify, request, json
from flask_cors import CORS, cross_origin

import os
from dotenv import load_dotenv

# Get environment vars for keeping sensitive info secure
# Has to come before blueprints that use the env vars
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

from facebookAuth import FbAuth
from users import Users
from events import Events, populate_ucla_events_database
from locations import Locations
from process import Process
import pymongo
import json

import schedule
import time
from threading import Thread

# Configure app and register blueprints
app = Flask(__name__)
app.register_blueprint(FbAuth)
app.register_blueprint(Users)
app.register_blueprint(Events)
app.register_blueprint(Locations)
app.register_blueprint(Process)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(app)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection.
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 

@app.route('/')
def index():
    return "Mappening is running!"

def event_thread_func():
    # schedule.every().day.at('18:14').do(populate_ucla_events_database)
    print('1st schedule')
    # time INSIDE container, which is GMT both local and AWS, +7/8 hours from Los Angeles with DST
    # so 12:00 GMT is 3/4 AM in LA
    schedule.every().day.at('12:00').do(populate_ucla_events_database)
    while True:
        schedule.run_pending()
        # kind of like a check every interval of time, if any jobs should run
        time.sleep(30)

if __name__ == "__main__":
    # another thread to run the periodic events update, daily
    event_update_thread = Thread(target = event_thread_func)
    event_update_thread.start()

    # if debug is true, will run 2 instances at once (so two copies of all threads)
    app.run(host='0.0.0.0', debug=False)
    # Flask defaults to port 5000

