# Interacting with events collection in mlab

from mappening.utils.database import events_internal_added_collection, test_collection
from mappening.api.utils import event_utils, event_filters
from mappening.api.utils.location_helpers import google_nearbySearch

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests, urllib
import time, dateutil.parser
from datetime import datetime, timedelta
import pytz
from pytz import timezone
from dateutil.tz import tzlocal
import json
import re
from tqdm import tqdm
from datetime import datetime
import dateutil.parser
import uuid
from collections import OrderedDict
from pytz import timezone

# Route Prefix: /api/v2/events
events = Blueprint('events', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(events)

@events.route('/', methods=['GET'])
def get_all_events():
    """
    :Route: /

    :Description: Returns a GeoJSON of all events within a few miles of UCLA

    """
    return event_utils.find_events_in_database(print_results=False)

@events.route('/test')
def test():
    return jsonify("HELLO")

# SEARCH
@events.route('/search', methods=['GET'])
def search_events():
    """
    :Route: /search?term=str&date=str&category=str&month=8

    :Description: Returns GeoJSON of all events filtered by date, search term, and/or category. The search term is case insensitive and searched for in the event name. Useful for a search bar.

    :param term: An optional query component/parameter for the search term to filter by
    :type term: str or None

    :param date: An optional query component/parameter for the date to filter by. Case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type date: str or None

    :param category: An optional query component/parameter for the event category to filter by
    :type category: str or None

    :param month: An optional query component/parameter that specifies which month to filter by. Accepts 1-12 to specify the month. Defaults to the current year, if a different year should be specified the `year` parameter must be set. Does NOT work with the `date` parameter.
    :type month: int or None

    :param year: An optional query component/parameter that specifies which year to filter by. Accepts the format YYYY and used with the `month` search filter.
    :type year: int or None

    """
    term = request.args.get('term')
    date = request.args.get('date')
    category = request.args.get('category')
    month = request.args.get('month')
    year = request.args.get('year')

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
    if month and event_utils.get_month(month):
        year_str = 2018
        if year and len(year) == 4:
            year_str = year
        else:
            now = datetime.now(tzlocal()).astimezone(pytz.timezone('America/Los_Angeles'))
            year_str = datetime.strftime(now, '%Y')
        month_str = event_utils.get_month(month)
        date_regex_str = '^{0}-{1}.*'.format(year_str, month_str)
        date_regex = re.compile(date_regex_str)
        search_dict['start_time'] = date_regex

    return event_utils.find_events_in_database(search_dict)

@events.route('/filter', methods=['GET'])
def filter_events():
    """
    :Route: /filter?when=period&time_period=morning&time_period=afternoon&date=April 20 2018&where=offcampus&popularity=50&food=True

    :Description: Returns GeoJSON of all events filtered by the specified filters. Filtering options include filtering by time, location, popularity, and whether or not an event has free food.

    :param when: An optional query component/parameter that specifies whether an event is happening now (event start time <= current time < event end time), is an upcoming event (event start time <= current time + 2 hours), or allows you to specify a time period with the `period` parameter. The parameter values can be `now`, `upcoming`, or `period`.
    :type when: str or None

    :param time_period: An optional query component/parameter that is only checked (and must be set) if the parameter `when` was set to value `time_period`. May have value `morning`, `afternoon`, or `night` where `morning` is from 3 am - 12 pm, `afternoon` is from 12 pm - 5 pm, and `night` is from 5 pm - 3 am. The start times are inclusive while the end times are exclusive. May have *multiple* values such as in example route above. Will return events that are in the morning or afternoon time period. A `date` must be specified or will return all events in database in the specified time periods.
    :type time_period: str or None

    :param date: An optional query component/parameter to specify what day to filter on. Does not work with `upcoming` or `now`. Case-insensitive string with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 20 April 2018)
    :type date: str or None

    :param where: An optional query component/parameter that specifies a location filter for events. The parameter values can be `nearby`, `oncampus`, or `offcampus` where `nearby` filters for events within a ~1000 ft (0.3 km) radius, `oncampus` gets locations within the UCLA boundary, and `offcampus` gets locations in Westwood and outside of the UCLA boundaries. A `date` may be specified or will return all events in database matching specified location parameters. For `nearby`, a `latitude` and `longitude` must be specified.
    :type where: str or None

    :param latitude: An optional query component/parameter used with the `nearby` filter. Must be passed in order to find events near the supplied coordinates.
    :type latitude: float or None

    :param longitude: An optional query component/parameter used with the `nearby` filter. Must be passed in order to find events near the supplied coordinates.
    :type longitude: float or None

    :param popularity: An optional query component/parameter that only returns events that meet a specified integer threshold: # interested || # going > this parameter value. Returns events sorted in decreasing order of popularity. Based on Facebook event data and may not result in changes.
    :type popularity: int or None

    :param food: An optional query component/parameter that gets events that have free food at them. May not be 100% accurate.
    :type food: boolean or None

    """
    when = request.args.get('when')
    time_period = request.args.getlist('time_period')
    date = request.args.get('date')
    where = request.args.get('where')
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    popularity = request.args.get('popularity') # popular, popular_threshold gone
    food = request.args.get('food')

    search_dict = {}
    unfiltered_events = []
    output = []

    # Get events as appropriate to use for filtering
    # Happening now, upcoming, and popular have custom mongo find parameters

    # Sets search dict to appropriate parameters for date
    if when and (when == 'now' or when == 'upcoming'):
      if when == 'now':
        event_filters.filter_by_happening_now(search_dict)
      elif when == 'upcoming':
        event_filters.filter_by_upcoming(search_dict)
    elif date:
      event_filters.get_day_events(search_dict, date)

    # Use current search dict and get events depending on whether or not
    # popularity filtering is occuring.
    if popularity:
        try:
          unfiltered_events = event_filters.filter_by_popular(search_dict, int(popularity))
        except:
          return 'Invalid popularity, needs to be integer!'
    else:
      unfiltered_events = event_utils.get_events_in_database(search_dict)

    # Add to search dict
    # Time filtering
    if when:
      if when == 'now' or when == 'upcoming':
        print('Filtering by now/when')
      elif when == 'period':
        if time_period:
          # Updates events to be filtered by time period
          unfiltered_events = event_filters.filter_by_time(unfiltered_events, time_period)
        else:
          return 'Expected time period to be set!'
      else:
        return 'Invalid value passed to `when` parameter.'

    # Location filtering
    if where:
      if where == 'nearby':
        if latitude and longitude and event_filters.is_valid_coords(latitude, longitude):
          unfiltered_events = event_filters.filter_by_nearby(unfiltered_events, float(latitude), float(longitude))
        else:
          return 'Expected valid coordinates to be passed!'
      elif where == 'oncampus':
        unfiltered_events = event_filters.filter_by_oncampus(unfiltered_events)
      elif where == 'offcampus':
        unfiltered_events = event_filters.filter_by_offcampus(unfiltered_events)
      else:
        return 'Invalid value passed to `where` parameter.'

    # Other filters
    # TODO JORGE IMPLEMENT ML
    # if food and food.lower() == "true":
    #   event_filters.filter_by_free_food(search_dict)

    # return 'Success!'

    return jsonify({'features': unfiltered_events, 'type': 'FeatureCollection'})

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

    :param event_date: An optional case-insensitive query parameter with raw date format or a commonly parseable format (e.g. DD MONTH YYYY -> 22 January 2018)
    :type event_date: str or None

    """
    # Iterate through all events and get unique list of all categories
    # If date was passed in, only check events starting on that date

    uniqueCats = set()
    if event_date:
        print("Using date parameter: " + event_date)
        date_regex_obj = event_utils.construct_date_regex(event_date)
        events_cursor = events_current_processed_collection.find({"categories": {"$exists": True}, "start_time": date_regex_obj})
    else:
        print("No date parameter given...")
        events_cursor = events_current_processed_collection.find({"categories": {"$exists": True}})
    if events_cursor.count() > 0:
        for event in events_cursor:
            categories = event["categories"]
            for cat in categories:
                uniqueCats.add(cat)
    else:
        print('Cannot find any events with categories!')
    return jsonify({'categories': list(uniqueCats)})

@events.route('/add', methods=['POST'])
def add_event():
  data = request.get_json()
  title = data['title']
  description = data['description']
  place = data['place']
  organization = data['organization']
  cover = data['cover']
  if cover == '':
    cover = '<NONE>'
  categories = data['categories']
  start_date = data['startDate']
  end_date = data['endDate']
  street = data['street']
  latitude = data['latitude']
  longitude = data['longitude']
  free_food = data['freeFood']

  try:
    latitude = float(latitude)
    longitude = float(longitude)
    if latitude < 34.056 or latitude > 34.079:
      return jsonify({'error': 'Latitude out of bounds!'})
    if longitude < -118.46 or longitude > -118.428:
      return jsonify({'error': 'Longitude out of bounds!'})
  except ValueError:
    return jsonify({'error': 'Please enter a valid latitude and longitude'})  

  start_date = dateutil.parser.parse(start_date)
  start_date = start_date.astimezone(timezone('US/Pacific'))
  start_date = datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S-0700')

  end_date = dateutil.parser.parse(end_date)
  end_date = end_date.astimezone(timezone('US/Pacific'))
  end_date = datetime.strftime(end_date, '%Y-%m-%dT%H:%M:%S-0700')

  event = OrderedDict()
  event['description'] = description
  event['start_time'] = start_date
  event['noreply_count'] = 0
  event['interested_count'] = None
  event['attending_count'] = 0
  event['id'] = uuid.uuid4().int >> 96
  event['categories'] = categories
  event['is_canceled'] = False
  event['maybe_count'] = 0
  event['name'] = title
  event['free_food'] = free_food
  event['cover'] = {
    'source': cover,
    'offset_x': 0,
    'offset_y': 0
  }


  event['place'] = {
    'id': uuid.uuid4().int >> 96,
    'location': {
      'city': 'Los Angeles',
      'country': 'United States',
      'zipcode': '90095',
      'state': 'CA',
      'street': street,
      'latitude': latitude,
      'longitude': longitude
    },
    'name': place
  }
  event['end_time'] = end_date
  res = events_internal_added_collection.insert_one(event)
  
  return jsonify({'error': None, 'id': str(res.inserted_id)})
