# Interacting with events collection in mlab
# TODO: hide app id/secret

from flask import Flask, jsonify, request, json, Blueprint
import pymongo
import urllib, json
import time, datetime
import subprocess, warnings, ast

Events = Blueprint('Events', __name__)

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
FACEBOOK_APP_ID = '353855031743097'
FACEBOOK_APP_SECRET = '2831879e276d90955f3aafe0627d3673'

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://devx_dora:3map5me@ds044709.mlab.com:44709/mappening_data'

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 
events_collection = db.map_events

# Returns JSON of all events
@Events.route('/api/events', methods=['GET'])
def get_all_events():
    output = []
    for event in events_collection.find():
      print ("Event: " + event["name"].encode('ascii', 'ignore'))
      output.append({
        '_id': event['id'],
        'event_name': event['name'], 
        'description': event['description'],
        'start_time': event['startTime'],
        'end_time': event['endTime'],
        'venue': event['venue'],
        'stats': event['stats'],
        'category': event['category'],
        'cover_picture': event['coverPicture'],
        'is_cancelled': event['isCancelled'],
        'ticketing': event['ticketing'] if 'ticketing' in event else "None",
        'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
      })
    return jsonify(output)

# Returns JSON of singular event by event name
# /<> defaults to strings without any slashes
@Events.route('/api/event/<event_name>', methods=['GET'])
def get_one_event(event_name):
    event = events_collection.find_one({'name': event_name})
    if event:
      output = {
        '_id': event['id'],
        'event_name': event['name'], 
        'description': event['description'],
        'start_time': event['startTime'],
        'end_time': event['endTime'],
        'venue': event['venue'],
        'stats': event['stats'],
        'category': event['category'],
        'cover_picture': event['coverPicture'],
        'is_cancelled': event['isCancelled'],
        'ticketing': event['ticketing'] if 'ticketing' in event else "None",
        'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
      }
    else:
      output = "No event of name '{}'".format(event_name)
    return jsonify({'map_event': output})

# Get all UCLA-related Facebook events and add to database
# TODO: Don't add duplicates, error checking
@Events.route('/api/populate-ucla-events-database')
def populate_ucla_events_database():
    # Location of Bruin Bear
    current_events = get_facebook_events(34.070964, -118.444757)
    events_collection.insert_many(current_events)
    return "Populated events database!"

# Can also access fb events this way
# http://localhost:3000/events?
# lat=40.710803
# &lng=-73.964040
# &distance=100
# &sort=venue
# &accessToken=353855031743097|2831879e276d90955f3aafe0627d3673

# Gets Facebook App access token using App ID and Secret
# https://stackoverflow.com/questions/3058723/programmatically-getting-an-access-token-for-using-the-facebook-graph-api
def get_facebook_events(latitude, longitude):
    # Hide warnings about outdated Facebook module
    warnings.filterwarnings('ignore', category=DeprecationWarning)

    # Add URL arguments and their values to a dict
    oauth_args = dict(  client_id     = FACEBOOK_APP_ID,
                        client_secret = FACEBOOK_APP_SECRET,
                        grant_type    = 'client_credentials')

    # Get ready to access by curl command
    # Construct URL in correct format using oauth_args
    oauth_curl_cmd = ['curl', 'https://graph.facebook.com/oauth/access_token?' 
                      + urllib.urlencode(oauth_args)]

    # Subprocess makes a new child process with Popen: 
    # Runs the curl command,
    # PIPE is same as bash pipe | (output of this curl command is input to next)
    # Communicate puts in data for stdin (not used here) and reads data from 
    # stdout / stderr into tuple (stdout, stderr), and [0] accesses the stdout
    oauth_response = subprocess.Popen(oauth_curl_cmd,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE).communicate()[0]
    print(type(oauth_response))

    try:
        # Takes a JSON string and turns into actual JSON, with key access_token
        app_access_token = ast.literal_eval(oauth_response)['access_token']
    except KeyError:
        print('Unable to grab an access token!')
        exit(1)

    # URL call to endpoint set up by server from 
    # https://github.com/tobilg/facebook-events-by-location
    baseurl = 'http://fb_events:3000/events?'

    # Location
    fb_latitude = latitude
    fb_longitude = longitude

    # Going back and forward in days using seconds
    seconds_in_day = 86400
    now_time = time.mktime(datetime.datetime.now().timetuple())
    start_t = now_time
    end_t = now_time + seconds_in_day

    # Sort by some number, options: time, distance, venue, popularity
    sort_type = 'time'

    event_args = dict(  accessToken = app_access_token,
                        lat         = latitude,
                        lng         = longitude,
                        since       = start_t,
                        until       = end_t,
                        sort        = sort_type,
                        distance    = 1 )

    fb_url = baseurl + urllib.urlencode(event_args)
    print(fb_url)

    response = urllib.urlopen(fb_url)
    print(type(response))
    data = json.loads(response.read())
    print(type(data))

    return data['events']
