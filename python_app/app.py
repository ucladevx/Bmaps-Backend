# Starter app.py that connects to mlab database

from flask import Flask, jsonify, request, json
from flask_cors import CORS, cross_origin
import pymongo

import urllib, json
import time, datetime
import subprocess, warnings, ast

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/foo": {"origins": "http://localhost:5000"}})

### Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://devx_dora:3map5me@ds044709.mlab.com:44709/mappening_data' 

# Set up database connection.
client = pymongo.MongoClient(uri)
db = client.get_default_database()

SAMPLE_EVENT = {
    "category": "SPORTS_EVENT",
    "distance": "201",
    "stats": {
        "attending": 6,
        "noreply": 0,
        "declined": 0,
        "maybe": 17
    },
    "description": "Sale Dates and Times:\n\nPublic Onsale : Mon, 31 Jul 2017 at 10:00 AM",
    "ticketing": {
        "ticket_uri": "http://ticketmaster.evyy.net/c/253158/264167/4272?u=http%3A%2F%2Fwww.ticketmaster.com%2Fevent%2F0B0052F2C83031FF"
    },
    "venue": {
        "category": "Stadium, Arena & Sports Venue",
        "about": None,
        "name": "Pauley Pavilion",
        "emails": None,
        "profilePicture": "https://scontent.xx.fbcdn.net/v/t1.0-1/c0.0.200.200/p200x200/13307328_1098003300258056_4219368369848796126_n.jpg?oh=4ef65c9a3a3731005f2949d03486c296&oe=5A669BF7",
        "location": {
            "city": "Los Angeles",
            "zip": "90095",
            "country": "United States",
            "longitude": -118.44681959102,
            "state": "CA",
            "street": "301 Westwood Plz",
            "latitude": 34.070367696979
        },
        "id": "120576928000703",
        "categoryList": [
            "Stadium, Arena & Sports Venue",
            "College & University",
            "Local Service"
        ],
        "coverPicture": "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/13243765_1098011573590562_7221941184127202225_o.jpg?oh=491515a4c328283623447793bbe20c20&oe=5A61B04E"
    },
    "isDraft": False,
    "coverPicture": "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/20901600_1501172473284509_5191814843800482770_o.jpg?oh=e9d526ebc10e813518e0d662bbf6c35e&oe=5AA79A0E",
    "isCancelled": False,
    "place": {
        "location": {
            "city": "Los Angeles",
            "zip": "90095",
            "country": "United States",
            "longitude": -118.44681959102,
            "state": "CA",
            "street": "301 Westwood Plz",
            "latitude": 34.070367696979
        },
        "id": "120576928000703",
        "name": "Pauley Pavilion"
    },
    "startTime": "2017-11-03T18:00:00-0700",
    "id": "1939846499570426",
    "timeFromNow": 8624,
    "endTime": None,
    "type": "public",
    "profilePicture": "https://scontent.xx.fbcdn.net/v/t1.0-0/c78.0.200.200/p200x200/20881835_1501172473284509_5191814843800482770_n.jpg?oh=cfeba5fc42faf1eaa643cb6118c26e7d&oe=5A66AB7E",
    "name": "Women's Volleyball"
}

def getFacebookData():
    """
    https://stackoverflow.com/questions/3058723/programmatically-getting-an-access-token-for-using-the-facebook-graph-api
    Get Facebook App Access Token using App ID and Secret

    """
    # warnings to hide warnings about outdated facebook module
    warnings.filterwarnings('ignore', category=DeprecationWarning)

    # katrina's app info, how to hide later?
    FACEBOOK_APP_ID = '353855031743097'
    FACEBOOK_APP_SECRET = '2831879e276d90955f3aafe0627d3673'

    # put in URL arguments and their values to a dict
    oauth_args = dict(  client_id     = FACEBOOK_APP_ID,
                        client_secret = FACEBOOK_APP_SECRET,
                        grant_type    = 'client_credentials')
    # get ready to access by curl command, and construct URL in correct format using above args and vals
    oauth_curl_cmd = ['curl',
                    'https://graph.facebook.com/oauth/access_token?' + urllib.urlencode(oauth_args)]
    # subprocess makes a new child process with Popen: runs the curl command,
    # PIPE literally is same as bash pipe | (give output of this curl command as input of another)
    # communicate puts in data for stdin (not used here) and reads data from stdout / stderr into
    # tuple (stdout, stderr), and [0] accesses the stdout info
    oauth_response = subprocess.Popen(oauth_curl_cmd,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE).communicate()[0]
    print(type(oauth_response))
    try:
        # takes a JSON string and turns into actual JSON, with key access_token
        app_access_token = ast.literal_eval(oauth_response)['access_token']
    except KeyError:
        print('Unable to grab an access token!')
        exit(1)

    # URL call to endpoint set up by server from https://github.com/tobilg/facebook-events-by-location
    baseurl = 'http://fb_events:3000/events?'

    # location of bruin bear
    latitude = 34.070964
    longitude = -118.444757
    # for going back and forward in days using seconds
    seconds_in_day = 86400
    now_time = time.mktime(datetime.datetime.now().timetuple())
    start_t = now_time
    end_t = now_time + seconds_in_day
    # sort by some number, options: time, distance, venue, popularity
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

@app.route('/')
def printFromDB():
    # Get collection (group of documents). Nothing is required to create a 
    # collection; it is created automatically when we insert.
    # Alternative format: map_collection = db['map_test']
    map_collection = db.map_test

    # FB_EVENTS = getFacebookData()
    # Insert a document into the collection
    map_collection.insert_one(SAMPLE_EVENT)
    # map_collection.insert_many(FB_EVENTS)

    # Find a document in the collection
    # find_one() gets first document in collection
    # print (map_collection.find_one())
    # find_one() with search term
    print (map_collection.find_one({"id": "1939846499570426"}))
    # find_one() with search term to print particular field
    # print (map_collection.find_one({"id": 111})['name'])

    # Find more than one document in a collection
    # find() returns a Cursor instance, which allows us to iterate over all 
    # matching documents.
    for post in map_collection.find():
        # print(post['name'] + " is #" + post['id']) 
        print("{} = {}".format(post['name'], post['id']))

    # Get count of documents matching a query
    print (map_collection.count())
    # print (map_collection.find({"name": "Dora"}).count())

    # Update an entry
    # Set value of entry
    query = {'name': "Women's Volleyball"}
    map_collection.update_one(query, {'$set': {'name': "Volleyball Thing"}})
    print (map_collection.find_one({"name": "Volleyball Thing"}))
    
    # Increment value of entry
    # WARNING: IDs ARE STRINGS, NOT INTS
    query = {'name': "Volleyball Thing"}
    map_collection.update_one(query, {'$inc': {'stats.attending': 100}})
    print (map_collection.find_one({"name": "Volleyball Thing"}))
    
    # Clear collection 
    ### Since this is an example, we'll clean up after ourselves.
    db.drop_collection('map_test')

    # Only close the connection when your app is terminating
    client.close()

    return "Success!"

def populateDatabase():
    map_collection = db['map_events']
    # at least 1 event in database
    if map_collection.count() > 0:
        return
    current_events = getFacebookData()
    map_collection.insert_many(current_events)

@app.route('/api/events', methods=['GET'])
@cross_origin(origin='localhost',headers=['Content-Type','Authorization'])
def get_all_events():
    events_collection = db['map_events']

    output = []
    for event in events_collection.find():
      print ("Event: " + event["name"].encode('ascii', 'ignore'))
      output.append({
        'event_name': event['name'], 
        'logistics': event['venue'],
        'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No',
        'people_going': event['stats']
      })
    return jsonify({'map_events': output})

# /<> defaults to strings without any slashes
@app.route('/api/event/<event_name>', methods=['GET'])
@cross_origin(origin='localhost',headers=['Content-Type','Authorization'])
def get_one_event(event_name):
    events_collection = db['map_events']
    event = events_collection.find_one({'name': event_name})
    if event:
      output = {
        'event_name': event['name'], 
        'logistics': event['venue'],
        'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No',
        'people_going': event['stats']
      }
    else:
      output = "No event of name '{}'".format(event_name)
    return jsonify({'map_event': output})

if __name__ == "__main__":
    populateDatabase()
    app.run(host='0.0.0.0', debug=True)

    # Flask defaults to port 5000
