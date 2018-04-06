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

# Route Prefix: /api/v1/events
eventsLegacy = Blueprint('eventsLegacy', __name__)

@eventsLegacy.route('/events', methods=['GET'])
def get_all_events():
    return event_utils.find_events_in_database(print_results=True, legacy=True)

# SEARCH

@eventsLegacy.route('/search/<search_term>', defaults={'event_date': None}, methods=['GET'])
@eventsLegacy.route('/search/<search_term>/<event_date>', methods=['GET'])
def search_events(search_term, event_date):
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
          output.append(event_utils.legacy_process_event(event))
    else:
        print("No event(s) matched '{}'".format(search_term))
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# SINGLE EVENT

@eventsLegacy.route('/event-name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    name_regex = re.compile(event_name, re.IGNORECASE)
    return event_utils.find_events_in_database({'name': name_regex}, True, legacy=True)

@eventsLegacy.route('/event-id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    return event_utils.find_events_in_database({'id': event_id}, True, legacy=True)

# MULTIPLE EVENTS

# Get all events with free food
@eventsLegacy.route('/event-food', methods=['GET'])
def get_free_food_events():
    return get_events_by_category('food', None)

@eventsLegacy.route('/event-date/<event_date>', methods=['GET'])
def get_events_by_date(event_date):
    date_regex_obj = event_utils.construct_date_regex(event_date)
    return event_utils.find_events_in_database('start_time', date_regex_obj, legacy=True)

@eventsLegacy.route('/events-by-category-and-date', defaults={'event_category': None}, methods=['GET'])
@eventsLegacy.route('/event-category/<event_category>', methods=['GET'])
def get_events_by_category(event_category):
    event_date = request.args['date']
    if event_category == None:
        event_category = request.args['event_category']

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
            output.append(event_utils.legacy_process_event(event))
    else:
        print("No event(s) matched '{}'".format(event_category))
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# CATEGORIES

@eventsLegacy.route('/event_categories', defaults={'event_date': None}, methods=['GET'])
@eventsLegacy.route('/event-categories-by-date/<event_date>', methods=['GET'])
def get_event_categories(event_date):
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
