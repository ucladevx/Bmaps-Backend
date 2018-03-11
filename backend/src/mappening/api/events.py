"""
Welcome to the Mappening Events API! Through this RESTful interface, we provide you with all the events happening around UCLA. The easiest way to use this is to simply go to the url `api.ucladevx.com/events <http://api.ucladevx.com/events>`_ and take all the events. See the explanation of events below. We offer many ways to search and filter these events through our api though you could do it yourself.

-----------------
Event Object
-----------------
An *event* object is a GeoJSON which means it has the following keys:

* geometry: with a type of "Point" and coordinates for latitude and longitude
* id: a unique id for this event
* properties: this contains all the event information and will be explored below

**Mandatory Event Properties**

These properties must have a valid value for every event.

* category: All the categories can be seen by dynamically calling /event-categories. About half of events have a category and the rest have <NONE>
* event_name: String of event's name
* stats: JSON for events from Facebook with attendance stats from at ~6 hour accuracy. Will have 4 keys 'attending', 'noreply', 'interested', and 'maybe' each with a integer value.
* start_time: String start time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* is_cancelled: Boolean indicating event is cancelled

**Potential Event Properties**

If the actual event has no value, the value will be <NONE>. Make sure to check for none in your code to avoid errors.

* description: String description
* venue: A JSON with a location key with a mandatory country, city, latitude, and longitude. Other potential venue details such as name can be seen in the example event below
* cover_picture: A url to a photo for the event
* ticketing: A JSON with a single ticket_uri element with a url to the ticketing site or <NONE>
* end_time: String end time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* free_food: If event has free food, currently just a strong NO

**Sample Event**::

    {
      "geometry": {
        "coordinates": [
          -118.451994,
          34.071474
        ],
        "type": "Point"
      },
      "id": "1766863560001661",
      "properties": {
        "category": "<NONE>",
        "cover_picture": "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/27356375_1972757046097696_6206118120755555565_o.jpg?oh=2240b43f536e76f9cf00410f602af386&oe=5B136061",
        "description": "Hack on the Hill IV (HOTH) is a 12 hour, beginner-friendly hackathon designed to give beginners a glimpse into what a real hackathon would be and feel like. During HOTH, there are workshops, mentors, and amazing prizes for the best hacks. As a sequel to HOTH III, HOTH IV features double the attendance and hacking tracks hosted by different ACM committees. We are also excited to announce that we'll be providing select hardware for hacking as well! LEARN MORE AND SIGN-UP HERE (applications close 2/10 at midnight): https://hoth.splashthat.com/ Sponsored by IS Associates, a UCLA-sponsored organization that provides an educational forum for the management and understanding of information technology. Learn more at: https://isassociates.ucla.edu",
        "duplicate_occurrence": "NO",
        "end_time": "Sat, 17 Feb 2018 23:30:00 GMT-0800",
        "event_name": "ACM Hack | Hack on the Hill IV",
        "free_food": "NO",
        "hoster": {
          "id": "369769286554402",
          "name": "UCLA Class of 2020"
        },
        "is_cancelled": false,
        "start_time": "Sat, 17 Feb 2018 08:30:00 GMT-0800",
        "stats": {
          "attending": 97,
          "interested": 199,
          "maybe": 199,
          "noreply": 107
        },
        "ticketing": {
          "ticket_uri": "https://hoth.splashthat.com/"
        },
        "venue": {
          "id": "955967887795957",
          "location": {
            "city": "Los Angeles",
            "country": "United States",
            "latitude": 34.071474,
            "longitude": -118.451994,
            "state": "CA",
            "street": "330 De Neve Dr Ste L-16",
            "zip": "90024"
          },
          "name": "Carnesale Commons"
        }
      },
      "type": "Feature"
    }

-----------------
API DOCS
-----------------
"""
# Interacting with events collection in mlab

from mappening.utils.database import *
from mappening.api.utils import event_caller, event_utils

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests, urllib
import time, datetime, dateutil.parser
import json
import re
from tqdm import tqdm

events = Blueprint('events', __name__)

@events.route('/', methods=['GET'])
def get_all_events():
    """ 
    :Route: /

    :Description: Returns a GeoJSON of all events within a few miles of UCLA 

    """
    return event_utils.find_events_in_database(print_results=True)

# SEARCH

@events.route('/search/<search_term>', defaults={'event_date': None}, methods=['GET'])
@events.route('/search/<search_term>/<event_date>', methods=['GET'])
def search_events(search_term, event_date):
    """ 
    :Route: /search/<search_term>/<event_date>

    :Description: Returns GeoJSON of all events whose names contain the search term. Useful for a search bar. Can be used to search events on a particular day as well.

    :param str search_term: a case-insensitive string that should be a substring of event names

    :param event_date: an optional case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type event_date: str or None

    """
    output = []
    search_regex = re.compile('.*' + search_term + '.*', re.IGNORECASE)

    if event_date:
        print "Using date parameter: " + event_date 
        date_regex_obj = event_utils.construct_date_regex(event_date)
        events_cursor = ucla_events_collection.find({'name': search_regex, 'start_time': date_regex_obj})
    else:
        print "No date parameter given..."
        events_cursor = ucla_events_collection.find({'name': search_regex})

    if events_cursor.count() > 0:
        for event in events_cursor:
          output.append(event_utils.process_event_info(event))
    else:
        print("No event(s) matched '{}'".format(search_term))
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# SINGLE EVENT

@events.route('/name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    """
    :Route: /name/<event_name>

    :Description: Returns GeoJSON of singular event matching event name

    :param str event_name: case-insensitive name string to search database for exact match

    """
    name_regex = re.compile(event_name, re.IGNORECASE)
    return event_utils.find_events_in_database('name', name_regex, True)

@events.route('/id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    """
    :Route: /id/<event_id>

    :Description: Returns GeoJSON of singular event matching event ID

    :param str event_id: ID string to search database for exact match

    """
    return event_utils.find_events_in_database('id', event_id, True)

# MULTIPLE EVENTS

# Get all events with free food
# TODO: ml => free food 
@events.route('/food', methods=['GET'])
def get_free_food_events():
    return get_events_by_category('food', None)

@events.route('/date/<event_date>', methods=['GET'])
def get_events_by_date(event_date):
    """
    :Route: /date/<event_date>
    
    :Description: Returns GeoJSON of all events starting on given date
    
    :param str event_date: case-insensitive date string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)

    """
    date_regex_obj = event_utils.construct_date_regex(event_date)
    return event_utils.find_events_in_database('start_time', date_regex_obj)

@events.route('/category/<event_category>', defaults={'event_date': None}, methods=['GET'])
@events.route('/category/<event_category>/<event_date>', methods=['GET'])
def get_events_by_category(event_category, event_date):
    """
    :Route: /category/<event_category>/<event_date>
        
    :Description: Returns GeoJSON of all events of the given category. Can also find all events of a certain category that start on the given date as well.
    
    :param str event_category: case-insensitive category string to match with event categories (e.g. food, theater)

    :param event_date: an optional case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type event_date: str or None

    """
    output = []

    # Handle event category
    regex_str = '^{0}|{0}$'.format(event_category.upper())
    cat_regex_obj = re.compile(regex_str)

    if event_date:
        print "Using date parameter: " + event_date 
        date_regex_obj = event_utils.construct_date_regex(event_date)
        events_cursor = ucla_events_collection.find({"category": cat_regex_obj, "start_time": date_regex_obj})
    else:
        print "No date parameter given..."
        events_cursor = ucla_events_collection.find({"category": cat_regex_obj})

    if events_cursor.count() > 0:
        for event in events_cursor:
            output.append(event_utils.process_event_info(event))
    else:
        print("No event(s) matched '{}'".format(event_category))
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# CATEGORIES

@events.route('/categories', defaults={'event_date': None}, methods=['GET'])
@events.route('/categories/<event_date>', methods=['GET'])
def get_event_categories(event_date):
    """
    :Route: /categories/<event_date>
    
    :Description: Returns JSON of all event categories used in all events. Can also find all event categories for events that start on a given date. Potential Categories: Crafts, Art, Causes, Comedy, Dance, Drinks, Film, Fitness, Food, Games, Gardening, Health, Home, Literature, Music, Other, Party, Religion, Shopping, Sports, Theater, Wellness Conference, Lecture, Neighborhood, Networking
    
    :param event_date: an optional case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type event_date: str or None

    """
    # Iterate through all events and get unique list of all categories
    # If date was passed in, only check events starting on that date
    uniqueList = []
    output = []

    if event_date:
        print "Using date parameter: " + event_date 
        date_regex_obj = event_utils.construct_date_regex(event_date)
        events_cursor = ucla_events_collection.find({"category": {"$exists": True}, "start_time": date_regex_obj})
    else:
        print "No date parameter given..."
        events_cursor = ucla_events_collection.find({"category": {"$exists": True}})

    if events_cursor.count() > 0:
        for event in events_cursor:
            if event["category"].title() not in uniqueList:
                uniqueList.append(event["category"].title())
        for category in uniqueList:
            output.append({"category": category})
    else:
        print('Cannot find any events with categories!')
    return jsonify({'categories': output})

# DELETE

# If needed, clean database of duplicate documents
# NOT a public route
@events.route('/remove-duplicates', methods=['DELETE'])
def remove_db_duplicates():
    total_dups = []

    # Difference between append and extend: extend flattens out lists to add elements, append adds 1 element
    total_dups.extend(event_utils.clean_collection(ucla_events_collection))
    total_dups.extend(event_utils.clean_collection(saved_pages_collection))
    total_dups.extend(event_utils.clean_collection(events_ml_collection))

    return jsonify(total_dups)

