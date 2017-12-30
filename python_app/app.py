# Starter app.py that connects to mlab database

from flask import Flask, jsonify, request, json
from flask_cors import CORS, cross_origin
from facebookAuth import FbAuth
from users import Users
from events import Events, populate_ucla_events_database
import pymongo
import json
import schedule
import time

data = json.load(open('secrets.json'))

# Configure app and register blueprints
app = Flask(__name__)
app.register_blueprint(FbAuth)
app.register_blueprint(Users)
app.register_blueprint(Events)
app.config['SECRET_KEY'] = data['APP_SECRET_KEY']

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(app)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = data['MLAB_USERNAME']
MLAB_PASSWORD = data['MLAB_PASSWORD']

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection.
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 

@app.route('/')
def index():
    return "Mappening is running!"
    
if __name__ == "__main__":
    # schedule.every().day.at('15:39').do(populate_ucla_events_database)
    # schedule.every().minute.do(populate_ucla_events_database)
    # while True:
    #     print('check schedule for jobs')
    #     schedule.run_pending()
    #     time.sleep(10)

    app.run(host='0.0.0.0', debug=True)
    # Flask defaults to port 5000

