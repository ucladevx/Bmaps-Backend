"""
Welcome to the Mappening Events API! Through this RESTful interface, we provide you with all the events happening around UCLA. The easiest way to use this is to simply go to the url `api.ucladevx.com/events <http://api.ucladevx.com/v2/events>`_ and take all the events. See the explanation of events below. We offer many ways to search and filter these events through our api though you could do it yourself.

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
* name: String of event's name
* stats: JSON for events from Facebook with attendance stats from at ~6 hour accuracy. Will have 4 keys 'attending', 'noreply', 'interested', and 'maybe' each with a integer value.
* start_time: String start time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* is_cancelled: Boolean indicating event is cancelled

**Potential Event Properties**
If these details aren't present, the JSON keys won't be present
* description: String description
* place: JSON with a location key with a mandatory country, city, latitude, and longitude. Other potential place details such as name can be seen in the example event below
* hoster: string of the host name
* ticket_uri: link to event ticketing
* end_time: String end time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* free_food: If event has free food, currently just a strong NO

**Sample Event**::

{
  geometry: {
    coordinates: [-118.44681959102,
      34.070367696979
    ],
    type: "Point"
  },
  id: "175752283196850",
  properties: {
    cover_picture: "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/27021656_1621551394602436_6299488329760837839_o.jpg?oh=057a6b50a89f8a1fa3684c7c25563b86&oe=5B035F3D",
    description: "LA Hacks is one of the biggest student-run hackathons on the West Coast, held every spring at UCLA’s iconic Pauley Pavilion. Over 1000 students from distinguished universities across the nation work together in teams to challenge themselves and create something beyond their comfort level - all in the span of 36 hours. Collaborate and build creative solutions to problems, while pushing the limits of your mind and body to make something amazing. From Evan Spiegel (CEO, Snapchat) and Sean Rad (CEO, Tinder), to 8 time gold medalist, Apolo Ohno, and a special pre-screening of HBO’s Silicon Valley, LA Hacks has welcomed many leaders and role models in tech. With industry mentors, technical workshops, and founder panels, LA Hacks works to broaden the scope of technology. EVENT DETAILS: Date: March 30th - April 1st, 2018 Location: Pauley Pavilion WHO WE ARE: LA Hacks epitomizes innovation, perseverance, and also pushing hackers to test their potential. We are UCLA students from many corners of campus, all united by one big goal: to give over 1000 college students the opportunity to come together and collaborate with industry leaders and innovative companies to develop impactful products with cutting-edge technologies.",
    end_time: "2018-04-01T15:00:00-0700",
    hoster: "LA Hacks",
    is_canceled: false,
    name: "LA Hacks 2018",
    place: {
      location: {
        city: "Los Angeles",
        country: "United States",
        latitude: 34.070367696979,
        longitude: -118.44681959102,
        state: "CA",
        street: "301 Westwood Plz",
        zip: "90095"
      },
      name: "Pauley Pavilion"
    },
    start_time: "2018-03-30T16:00:00-0700",
    stats: {
      attending: 179,
      interested: 1473,
      maybe: 1473,
      noreply: 293
    },
    time_updated: "2018-03-25 19:10:07.585374"
  },
  type: "Feature"
}
"""
# Interacting with events collection in mlab

from mappening.utils.database import ucla_events_collection, saved_pages_collection, events_ml_collection
from mappening.api.utils import event_caller, event_utils

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests, urllib
import time, datetime, dateutil.parser
import json
import re
from tqdm import tqdm

# Route Prefix: /api/events
events = Blueprint('events', __name__)

@events.route('/', methods=['GET'])
def get_all_events():
    """
    :Route: /

    :Description: Returns a GeoJSON of all events within a few miles of UCLA

    """
    return event_utils.find_events_in_database(print_results=True)

# SEARCH
@events.route('/search', methods=['GET'])
def search_events():
    """
    :Route: /search

    :Description: Returns GeoJSON of all events filtered by date, search term, and category. The search term is case insensitive and searched for in the event name. Useful for a search bar.
    """
    term = request.args.get('term')
    date = request.args.get('date')
    category = request.args.get('category')

    search_dict = {}
    output = []

    # Add to search dict
    if term:
        term_regex = re.compile('.*' + term + '.*', re.IGNORECASE)
        search_dict["$or"] = [ {"name":term_regex}, {"description":term_regex} ] # MongoDB's syntax for find name in name or description
    if date:
        date_regex = event_utils.construct_date_regex(date)
        search_dict['start_time'] = date_regex
    if category:
        cat_regex_obj = re.compile('^{0}|{0}$'.format(category.upper()))
        search_dict['category'] = cat_regex_obj
        print(search_dict)

    return event_utils.find_events_in_database(search_dict)

# SINGLE EVENT
#TODO: Combine into one
@events.route('/name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    """
    :Route: /name/<event_name>

    :Description: Returns GeoJSON of singular event matching event name

    :param str event_name: case-insensitive name string to search database for exact match

    """
    name_regex = re.compile(event_name, re.IGNORECASE)
    search_dict = {'name': name_regex}
    return event_utils.find_events_in_database(search_dict, name_regex, True )

@events.route('/id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    """
    :Route: /id/<event_id>

    :Description: Returns GeoJSON of singular event matching event ID

    :param str event_id: ID string to search database for exact match

    """
    search_dict = {'id': event_id}
    return event_utils.find_events_in_database(search_dict, True)

# MULTIPLE EVENTS
#TODO: Allow all events to be returned on date not just those that start on that datetime
#TODO: Change this to search for category list when you implement ml category model

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
# TODO: NOT a public route @Jason do you need this here or where or what
@events.route('/remove-duplicates', methods=['DELETE'])
def remove_db_duplicates():
    total_dups = []

    # Difference between append and extend: extend flattens out lists to add elements, append adds 1 element
    total_dups.extend(event_utils.clean_collection(ucla_events_collection))
    total_dups.extend(event_utils.clean_collection(saved_pages_collection))
    total_dups.extend(event_utils.clean_collection(events_ml_collection))

    return jsonify(total_dups)
