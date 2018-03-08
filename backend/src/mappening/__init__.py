import os
import mappening.utils.secrets

from flask import Flask
from flask_cors import CORS, cross_origin

from mappening.api.events import events
from mappening.api.pages import pages
from mappening.api.locations import locations
from mappening.auth.facebook import auth
from mappening.auth.users import users
from mappening.utils.tokenize import tokenize

# Configure app and register blueprints
app = Flask(__name__)
app.register_blueprint(events, url_prefix='/api/events')
app.register_blueprint(pages, url_prefix='/api/pages')
app.register_blueprint(locations, url_prefix='/api/locations')
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(users, url_prefix='/users')
app.register_blueprint(tokenize, url_prefix='/tokenize')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(app)
