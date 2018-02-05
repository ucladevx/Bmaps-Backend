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
    print('Schedule 3 times a day')
    # time INSIDE container, which is GMT both local and AWS, +8 hours from Los Angeles without DST
    # so 13:00 GMT --> 5 AM in LA, 21:00 GMT --> 1 PM, 03:00 GMT --> 7 PM, if DST: all LA hours +1
    schedule.every().day.at('13:00').do(populate_ucla_events_database)
    # update later than the hour, removing events starting at those hours, for late people
    schedule.every().day.at('21:10').do(populate_ucla_events_database)
    schedule.every().day.at('03:10').do(populate_ucla_events_database)
    while True:
        schedule.run_pending()
        # kind of like a check every interval of time, if any jobs should run
        time.sleep(30)

if __name__ == "__main__":
    # another thread to run the periodic events update, daily
    event_update_thread = Thread(target = event_thread_func)
    event_update_thread.start()

    code_update_date = "2/4/18"
    print("Updated on: {0}".format(code_update_date))

    # if debug is true, will run 2 instances at once (so two copies of all threads)
    app.run(host='0.0.0.0', debug=False)
    # Flask defaults to port 5000

