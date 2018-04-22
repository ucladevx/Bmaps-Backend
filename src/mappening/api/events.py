# Interacting with events collection in mlab

from mappening.utils.database import events_current_collection
from mappening.api.utils import event_caller, event_utils, event_filters

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests, urllib
import time, datetime, dateutil.parser
import json
import re
from tqdm import tqdm

# Route Prefix: /api/v2/events
events = Blueprint('events', __name__)

# Enable Cross Origin Resource Sharing (CORS)
# cors = CORS(events)

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
    :Route: /search?term=str&date=str&category=str

    :Description: Returns GeoJSON of all events filtered by date, search term, and/or category. The search term is case insensitive and searched for in the event name. Useful for a search bar.

    :param term: An optional query component/parameter for the search term to filter by
    :type term: str or None

    :param date: A query component/parameter for the date to filter by. Case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type date: str or None

    :param category: A query component/parameter for the event category to filter by
    :type category: str or None

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

@events.route('/filter', methods=['GET'])
def filter_events():
    """
    :Route: /filter?when=time&time=morning&time=afternoon&day=April 20 2018&where=offcampus&popular=False&popular_threshold=False&food=True

    :Description: Returns GeoJSON of all events filtered by the specified filters. Filtering options include filtering by time, location, popularity, and whether or not an event has free food.

    :param when: An optional query component/parameter that specifies whether an event is happening now (event start time <= current time < event end time), is an upcoming event (event start time <= current time + 2 hours), or allows you to specify a time period with the `time` parameter. The parameter values can be `now`, `upcoming`, or `time`. 
    :type when: str or None

    :param time: An optional query component/parameter that is only checked (and must be set) if the parameter `when` was set to value `time`. May have value `morning`, `afternoon`, or `night` where `morning` is from 3 am - 12 pm, `afternoon` is from 12 pm - 5 pm, and `night` is from 5 pm - 3 am. The start times are inclusive while the end times are exclusive. May have *multiple* values such as in example route above. Will return events that are in the morning or afternoon time period. A `day` must be specified or will return all events in database in the specified time periods.
    :type time: str or None

    :param day: An optional query component/parameter. Used with parameters `time`, `where`, and `popular`. Case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 20 April 2018)
    :type day: str or None

    :param where: An optional query component/parameter that specifies a location filter for events. The parameter values can be `nearby`, `oncampus`, or `offcampus` where `nearby` filters for events within a TODO radius, `oncampus` gets locations within the UCLA boundary, and `offcampus` gets locations in Westwood and outside of the UCLA boundaries. A `day` may be specified or will return all events in database matching specified location parameters.
    :type where: str or None

    :param popular: An optional query component/parameter that returns events sorted in decreasing order of popularity. Based on Facebook event data and may not result in changes. A `day` must be specified or will return results using all events in the database.
    :type popular: boolean or None

    :param popular_threshold: An optional query component/parameter that only returns events that meet the following threshold: # interested || # going > 100. Returns events sorted in decreasing order of popularity. Based on Facebook event data and may not result in changes.
    :type popular_threshold: boolean or None

    :param food: An optional query component/parameter that gets events that have free food at them. May not be 100% accurate.
    :type food: boolean or None

    """
    when = request.args.get('when')
    time = request.args.getlist('time')
    day = request.args.get('day')
    where = request.args.get('where')
    popular = request.args.get('popular')
    popular_threshold = request.args.get('popular_threshold')
    food = request.args.get('food')

    search_dict = {}
    output = []

    # today = datetime.now(tzlocal()).astimezone(pytz.timezone('America/Los_Angeles'))
    # today = datetime.strftime(today, '%Y-%m-%d')

    # Add to search dict 
    # Time filtering
    if when:
      if when == 'now':
        event_filters.filter_by_happening_now(search_dict)
      elif when == 'upcoming':
        event_filters.filter_by_upcoming(search_dict)
      elif when == 'time':
        if time:
          # Does not use search_dict
          return event_filters.filter_by_time(time, day)
          # return jsonify({'time': time})
        else:
          return 'Expected time period to be set!'
      else:
        return 'Invalid value passed to `when` parameter.'

    # Location filtering
    if where:
      if where == 'nearby':
        event_filters.filter_by_nearby(search_dict)
      elif where == 'oncampus':
        return event_filters.filter_by_oncampus(day)
      elif where == 'offcampus':
        return event_filters.filter_by_offcampus(day)
      else:
        return 'Invalid value passed to `where` parameter.'

    # Other filters
    if popular and popular.lower() == "true":
      if popular_threshold and popular_threshold.lower() == "true":
        return event_filters.filter_by_popular(day, True)
      else:
        return event_filters.filter_by_popular(day)

    if food and food.lower() == "true":
      event_filters.filter_by_free_food(search_dict)
      
    # return 'Success!'

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

    :param event_date: An optional case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type event_date: str or None

    """
    # Iterate through all events and get unique list of all categories
    # If date was passed in, only check events starting on that date
    uniqueList = []
    output = []

    if event_date:
        print "Using date parameter: " + event_date
        date_regex_obj = event_utils.construct_date_regex(event_date)
        events_cursor = events_current_collection.find({"category": {"$exists": True}, "start_time": date_regex_obj})
    else:
        print "No date parameter given..."
        events_cursor = events_current_collection.find({"category": {"$exists": True}})

    if events_cursor.count() > 0:
        for event in events_cursor:
            if event["category"].title() not in uniqueList:
                uniqueList.append(event["category"].title())
        for category in uniqueList:
            output.append({"category": category})
    else:
        print('Cannot find any events with categories!')
    return jsonify({'categories': output})
