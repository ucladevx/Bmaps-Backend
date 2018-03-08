from flask import Flask
from flask_cors import CORS, cross_origin
from mappening.api.events.events import Events
from mappening.api.locations.locations import Locations
from mappening.auth.facebookAuth import fbAuth
from mappening.users.users import Users
from mappening.utils.process import Process

import os
from dotenv import load_dotenv

# Get environment vars for keeping sensitive info secure
# Has to come before blueprints that use the env vars
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Configure app and register blueprints
app = Flask(__name__)
app.register_blueprint(Events, url_prefix='/events')
app.register_blueprint(Locations, url_prefix='/locations')
app.register_blueprint(fbAuth, url_prefix='/auth')
app.register_blueprint(Users, url_prefix='/users')
app.register_blueprint(Process, url_prefix='/process')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(app)
