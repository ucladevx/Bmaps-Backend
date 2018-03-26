# TO BE DELETED AT A LATER DATE, ONCE ALL CODE IS SWITCHED THIS SHOULD BE TEMPORARY.
# IF THIS CODE STILL EXISTS AT THE END OF SPRING 2018 SOMEONE FAILED

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
eventsLegacy = Blueprint('eventsLegacy', __name__)

@eventsLegacy.route('/', methods=['GET'])
def get_all_events():
    """
    :Route: /

    :Description: Returns a GeoJSON of all events within a few miles of UCLA

    """
    return event_utils.find_events_in_database(print_results=True)

# SEARCH

@eventsLegacy.route('/search/<search_term>', defaults={'event_date': None}, methods=['GET'])
@eventsLegacy.route('/search/<search_term>/<event_date>', methods=['GET'])
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
          output.append(legacy_process_event(event))
    else:
        print("No event(s) matched '{}'".format(search_term))
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# SINGLE EVENT

@eventsLegacy.route('/name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    """
    :Route: /name/<event_name>

    :Description: Returns GeoJSON of singular event matching event name

    :param str event_name: case-insensitive name string to search database for exact match

    """
    name_regex = re.compile(event_name, re.IGNORECASE)
    return event_utils.find_events_in_database({'name': name_regex}, True)

@eventsLegacy.route('/id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    """
    :Route: /id/<event_id>

    :Description: Returns GeoJSON of singular event matching event ID

    :param str event_id: ID string to search database for exact match

    """
    return event_utils.find_events_in_database({'id': event_id}, True)

# MULTIPLE EVENTS

# Get all events with free food
# TODO: ml => free food
@eventsLegacy.route('/food', methods=['GET'])
def get_free_food_events():
    return get_events_by_category('food', None)

@eventsLegacy.route('/date/<event_date>', methods=['GET'])
def get_events_by_date(event_date):
    """
    :Route: /date/<event_date>

    :Description: Returns GeoJSON of all events starting on given date

    :param str event_date: case-insensitive date string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)

    """
    date_regex_obj = event_utils.construct_date_regex(event_date)
    return event_utils.find_events_in_database('start_time', date_regex_obj)

@eventsLegacy.route('/category/<event_category>', defaults={'event_date': None}, methods=['GET'])
@eventsLegacy.route('/category/<event_category>/<event_date>', methods=['GET'])
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
            output.append(legacy_process_event(event))
    else:
        print("No event(s) matched '{}'".format(event_category))
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# CATEGORIES

@eventsLegacy.route('/categories', defaults={'event_date': None}, methods=['GET'])
@eventsLegacy.route('/categories/<event_date>', methods=['GET'])
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
@eventsLegacy.route('/remove-duplicates', methods=['DELETE'])
def remove_db_duplicates():
    total_dups = []

    # Difference between append and extend: extend flattens out lists to add elements, append adds 1 element
    total_dups.extend(event_utils.clean_collection(ucla_events_collection))
    total_dups.extend(event_utils.clean_collection(saved_pages_collection))
    total_dups.extend(event_utils.clean_collection(events_ml_collection))

    return jsonify(total_dups)


def legacy_process_event(event):
    formatted_info = {
        # will ALWAYS have an ID
        'id': event['id'],
        'type': 'Feature',
        'geometry': {
            # no coordinates? default to Bruin Bear
            'coordinates': [
                event['place']['location'].get('longitude', event_caller.CENTER_LONGITUDE),
                event['place']['location'].get('latitude', event_caller.CENTER_LATITUDE)
            ],
            'type': 'Point'
        },
        'properties': {
            'event_name': event.get('name', '<NONE>'),
            'description': event.get('description', '<NONE>'),
            'hoster': event.get('hoster', '<MISSING HOST>'),
            'start_time': event_utils.processed_time(event.get('start_time', '<NONE>')),
            'end_time': event_utils.processed_time(event.get('end_time', '<NONE>')),
            'venue': event['place'],
            'stats': {
                'attending': event['attending_count'],
                'noreply': event['noreply_count'],
                'interested': event['interested_count'],
                'maybe': event['maybe_count']
            },
            # TODO: whenever category is checked, run Jorge's online ML algorithm
            'category': event.get('category', '<NONE>'),
            'cover_picture': event['cover'].get('source', '<NONE>') if 'cover' in event else '<NONE>',
            'is_cancelled': event.get('is_canceled', False),
            'ticketing': {
                'ticket_uri': event.get('ticket_uri', '<NONE>')
            },
            'free_food': 'YES' if 'category' in event and 'FOOD' == event['category'] else 'NO',
            'duplicate_occurrence': 'YES' if 'duplicate_occurrence' in event else 'NO',
            'time_updated': event.get('time_updated', '<UNKNOWN TIME>')
        }
    }
    return formatted_info
