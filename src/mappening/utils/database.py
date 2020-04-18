from mappening.utils.secrets import MLAB_USERNAME, MLAB_PASSWORD, MLAB_HOST

from pymongo import MongoClient

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
events_uri = 'mongodb://{0}:{1}@{2}/events?retryWrites=false'.format(MLAB_USERNAME, MLAB_PASSWORD, MLAB_HOST)
locations_uri = 'mongodb://{0}:{1}@{2}/locations'.format(MLAB_USERNAME, MLAB_PASSWORD, MLAB_HOST)
users_uri = 'mongodb://{0}:{1}@{2}/users'.format(MLAB_USERNAME, MLAB_PASSWORD, MLAB_HOST)
test_uri ='mongodb://{0}:{1}@ds261828.mlab.com:61828/test_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connections
events_client = MongoClient(events_uri)
events_db = events_client['events']

locations_client = MongoClient(locations_uri)
locations_db = locations_client['locations']

users_client = MongoClient(users_uri)
users_db = users_client['users']

test_client = MongoClient(test_uri)
test_db = test_client['test_data']


print("Connected to database!")

# Get all the collections

#### EVENTS

"""
how it works as of 2018/05/18:

every unique source website of events (e.g. FB, Eventbrite, UCLA club list)
has its own "raw" database, for just inserting the unprocessed returned data from API / scraping directly
At the same time, process the raw data (add category / location, reformat fields to be standard)
and add to a single processed database of events from all sources
the website uses this processed database's info directly (no processing needed when pulling it out)
"""


# get events from facebook scraped with puppeteer 
events_fb_puppeteer_collection = events_db.events_facebook_puppeteer

# the eventbrite accumulating db
events_eventbrite_collection = events_db.events_eventbrite
# the facebook accumulating db, used to be events_ml_collection
events_fb_collection = events_db.events_fb
# change the name of this test db to automatically make a new one if it doesn't exist already in mLab
events_test_collection = events_db.events_test
# the final, aggregated database of all events from all sources, processed for frontend
events_current_processed_collection = events_db.events_current_processed
# processed events from facebook
events_facebook_processed_collection = events_db.events_facebook_processed

events_internal_added_collection = events_db.events_internal_added

# a db for logs when running on AWS
events_log_collection = events_db.events_log

### FACEBOOK PAGES
fb_pages_saved_collection = events_db.fb_pages_saved
fb_pages_ignored_collection = events_db.fb_pages_ignored

#### LOCATIONS
locations_collection = locations_db.locations
unknown_locations_collection = locations_db.unknown_locations

test_collection = test_db.events
print("Got database collections...")
