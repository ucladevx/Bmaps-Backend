from flask import Flask
from flask_cors import CORS, cross_origin

from mappening.api.eventsLegacy import eventsLegacy
from mappening.api.events import events
from mappening.api.locations import locations
from mappening.api.users import users             # TODO: finish
# from mappening.api.preferences import preferences # TODO: finish
from mappening.auth.auth import auth

# Configure app and register blueprints
app = Flask(__name__)
#TODO: Remove this legacy code Spring 2018
app.register_blueprint(eventsLegacy, url_prefix='/api/v1/events')
app.register_blueprint(events, url_prefix='/api/v2/events')
app.register_blueprint(locations, url_prefix='/api/v2/locations')
app.register_blueprint(auth, url_prefix='/api/v2/auth') # Not actually public API
app.register_blueprint(users, url_prefix='/api/v2/users')

app.config['SECRET_KEY'] = 'whats mappening'
# app.permanent_session_lifetime = datetime.timedelta(minutes=20)
# app.config['CORS_HEADERS'] = 'Content-Type'

# Enable Cross Origin Resource Sharing (CORS)
# This makes the CORS feature cover all routes in the app
cors = CORS(app)
