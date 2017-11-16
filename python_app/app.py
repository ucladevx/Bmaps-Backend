# Starter app.py that connects to mlab database

from flask import Flask, jsonify, request, json
from flask_cors import CORS, cross_origin
from facebookAuth import FbAuth
from users import Users
from events import Events
import pymongo

# Configure app and register blueprints
app = Flask(__name__)
app.register_blueprint(FbAuth)
app.register_blueprint(Users)
app.register_blueprint(Events)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(app)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://devx_dora:3map5me@ds044709.mlab.com:44709/mappening_data' 

# Set up database connection.
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 

@app.route('/')
def index():
    return "Mappening is running!"
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
    # Flask defaults to port 5000
