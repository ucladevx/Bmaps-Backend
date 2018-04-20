from mappening.utils.secrets import MLAB_USERNAME, MLAB_PASSWORD

from pymongo import MongoClient

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
events_uri = 'mongodb://{0}:{1}@ds014388.mlab.com:14388/events'.format(MLAB_USERNAME, MLAB_PASSWORD)
locations_uri = 'mongodb://{0}:{1}@ds014388.mlab.com:14388/locations'.format(MLAB_USERNAME, MLAB_PASSWORD)
users_uri = 'mongodb://{0}:{1}@ds014388.mlab.com:14388/users'.format(MLAB_USERNAME, MLAB_PASSWORD)
tkinter_uri = 'mongodb://{0}:{1}@ds014388.mlab.com:14388/tkinter'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connections
events_client = MongoClient(events_uri)
events_db = events_client['events'] 

locations_client = MongoClient(locations_uri)
locations_db = locations_client['locations'] 

users_client = MongoClient(users_uri)
users_db = users_client['users'] 

tkinter_client = MongoClient(tkinter_uri)
tkinter_db = tkinter_client['tkinter'] 

print("Connected to database!")

# Get all the collections

#### EVENTS
events_current_collection = events_db.events_current
events_ml_collection = events_db.events_ml
events_test_collection = events_db.events_test

### PAGES
pages_saved_collection = events_db.pages_saved
pages_ignored_collection = events_db.pages_ignored

#### LOCATIONS
locations_collection = locations_db.locations
unknown_locations_collection = locations_db.unknown_locations

#### USERS
users_collection = users_db.users
# map_users_collection = users_db.map_users
# dead_users_collection = users_db.dead_users

#### TKINTER
UCLA_locations_collection = tkinter_db.UCLA_locations
UCLA_TODO_locations_collection = tkinter_db.UCLA_TODO_locations

API_unknown_locations_collection = tkinter_db.API_unknown_locations
API_known_locations_collection = tkinter_db.API_known_locations
API_TODO_locations_collection = tkinter_db.API_TODO_locations

print("Got database collections...")
