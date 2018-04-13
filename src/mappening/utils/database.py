from mappening.utils.secrets import MLAB_USERNAME, MLAB_PASSWORD

from pymongo import MongoClient

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection.
client = MongoClient(uri)
db = client['mappening_data']

print "Connected to database!"

# Get all the collections

# events.py
events_current_collection = db.events_current
pages_saved_collection = db.pages_saved
events_ml_collection = db.events_ml

# event_caller.py
# pages_saved_collection = db.saved_pages
# events_ml_collection = db.events_ml
unknown_locations_collection = db.unknown_locations

# locations.py
# events_ml_collection = db.events_ml
UCLA_locations_collection = db.UCLA_locations
tkinter_UCLA_locations_collection = db.tkinter_UCLA_locations
tkinter_unknown_locations_collection = db.tkinter_unknown_locations
tkinter_TODO_locations_collection = db.tkinter_TODO_locations

# facebook.py
users_collection = db.users

# users.py
# map_users_collection = db.map_users

# test
test_collection = db.test

print "Got database collections..."
