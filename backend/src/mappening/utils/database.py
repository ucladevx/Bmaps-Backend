import os
from pymongo import MongoClient

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection.
client = MongoClient(uri)
db = client['mappening_data']

print "Connected to database!"

# Get all the collections

# events.py
ucla_events_collection = db.ucla_events
saved_pages_collection = db.saved_pages
events_ml_collection = db.events_ml

# event_caller.py
# saved_pages_collection = db.saved_pages
# events_ml_collection = db.events_ml
unknown_locations_collection = db.unknown_locations

# locations.py
# events_ml_collection = db.events_ml
UCLA_locations_collection = db.UCLA_locations
tkinter_UCLA_locations_collection = db.tkinter_UCLA_locations
tkinter_unknown_locations_collection = db.tkinter_unknown_locations
tkinter_TODO_locations_collection = db.tkinter_TODO_locations

# facebook.py
map_users_collection = db.map_users

# users.py
# map_users_collection = db.map_users

print "Got database collections..."
