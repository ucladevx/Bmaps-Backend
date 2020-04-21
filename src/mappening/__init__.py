from flask import Flask
from flask_cors import CORS, cross_origin
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy

from mappening.api.events import events
from mappening.api.locations import locations
from mappening.utils.secrets import POSTGRES_URI

# Configure app and register blueprints
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URI

db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)

app.register_blueprint(events, url_prefix='/api/events')
app.register_blueprint(locations, url_prefix='/api/locations')

app.config['SECRET_KEY'] = 'whats mappening'

# Enable Cross Origin Resource Sharing (CORS)
# This makes the CORS feature cover all routes in the app
cors = CORS(app)

Compress(app)
