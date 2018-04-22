from mappening.utils.database import events_current_collection
from mappening.api.utils import event_utils

from flask import Flask, jsonify, request, json, Blueprint
import requests
import json
import dateutil.parser
from datetime import datetime, timedelta
import pytz
from pytz import timezone
from dateutil.tz import tzlocal
from shapely.geometry import shape, Point
import os

# Route Prefix: /api/v2/events
event_filters = Blueprint('event_filters', __name__)

@event_filters.route('/filter', methods=['GET'])
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
        filter_by_happening_now(search_dict)
      elif when == 'upcoming':
        filter_by_upcoming(search_dict)
      elif when == 'time':
        if time:
          # Does not use search_dict
          return filter_by_time(time, day)
          # return jsonify({'time': time})
        else:
          return 'Expected time period to be set!'
      else:
        return 'Invalid value passed to `when` parameter.'

    # Location filtering
    if where:
      if where == 'nearby':
        filter_by_nearby(search_dict)
      elif where == 'oncampus':
        return filter_by_oncampus(day)
      elif where == 'offcampus':
        return filter_by_offcampus(day)
      else:
        return 'Invalid value passed to `where` parameter.'

    # Other filters
    if popular and popular.lower() == "true":
      if popular_threshold and popular_threshold.lower() == "true":
        return filter_by_popular(day, True)
      else:
        return filter_by_popular(day)

    if food and food.lower() == "true":
      filter_by_free_food(search_dict)
      
    # return 'Success!'

    return event_utils.find_events_in_database(search_dict)

# Get current time and get all events whose start time <= current time < end time
def filter_by_happening_now(search_dict):
  print("filter_by_happening_now")

  now = datetime.now(tzlocal()).astimezone(pytz.timezone('America/Los_Angeles'))
  now = datetime.strftime(now, '%Y-%m-%dT%H:%M%S%z')
  search_dict['$and'] = [ {"start_time":{"$lte": now}}, {"end_time":{"$gt": now}} ]

# Get current time and get all events whose start time is <= 2 hours for now
def filter_by_upcoming(search_dict):
  print("filter_by_upcoming")

  now = datetime.now(tzlocal()).astimezone(pytz.timezone('America/Los_Angeles'))
  in_two_hours = now + timedelta(hours=2)
  in_two_hours = datetime.strftime(in_two_hours, '%Y-%m-%dT%H:%M%S%z')

  search_dict['start_time'] = {"$lte": in_two_hours}

# Morning = events whose start time is >= 3 am and < 12 pm
# Afternoon = events whose start time is >= 12 pm and < 5 pm
# Night = events whose start time is >= 5 pm and < 3 am
def filter_by_time(time_period, day):
  print("filter_by_time")

  # Get all events on the given day
  search_dict = {}

  # If day is specified run only on events from specified day
  # Otherwise look at all events in database
  if day:
    date_regex = event_utils.construct_date_regex(day)
    search_dict['start_time'] = date_regex
  day_events = event_utils.get_events_in_database(search_dict)

  # Set bools for what events to filter for
  is_morning = False
  is_afternoon = False
  is_night = False

  if 'morning' in time_period:
    print('morning')
    is_morning = True
  if 'afternoon' in time_period:
    print('afternoon')
    is_afternoon = True
  if 'night' in time_period:
    print('night')
    is_night = True

  # Extract all events of matching time periods and return results
  filtered_events = []

  for event in day_events:
    start_time = event['properties']['start_time']

    # Try to parse date
    try:
        # Use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(start_time)
    except ValueError:
        # Got invalid date string
        print('Invalid date string, cannot be parsed!')
        return None

    # Get the date string by YYYY-MM-DD format
    start_hour = datetime.strftime(time_obj, '%H')
    # print "Start hour is " + start_hour

    # Check whether the event start time falls under the time period
    should_append = False
    if is_morning and start_hour >= '03' and start_hour < '12':
      # print('wow morning')
      should_append = True
    if is_afternoon and start_hour >= '12' and start_hour < '17':
      # print('wow afternoon')
      should_append = True
    if is_night and (start_hour >= '17' and start_hour <= '24') or (start_hour >= '00' and start_hour < '03'):
      # print('wow night')
      should_append = True

    # Make sure the event is only appended once
    if should_append:
      filtered_events.append(event)

  return jsonify({'features': filtered_events, 'type': 'FeatureCollection'})

# Using Facebook event statistics, sort by the number of people interested.
# Enable specification of top # of events to return or a threshold
# If (interested || going > 100) then popular
def filter_by_popular(day, use_threshold=False):
  # Sort events by # of interested
  # Get all events on the given day
  # If day is specified look only at events on given day
  # Or consider all events in database
  sorted_events = []
  if day:
    date_regex = event_utils.construct_date_regex(day)
    events_cursor = events_current_collection.find({'start_time': date_regex}).sort('interested_count', -1)
  else:
    events_cursor = events_current_collection.find({}).sort('interested_count', -1)

  if events_cursor.count() > 0:
    for event in events_cursor:
      processed_event = event_utils.process_event_info(event)
      if use_threshold:
        print("filter_by_popular theshold")
        if processed_event['properties']['stats'].get('attending', 0) >= 50 or processed_event['properties']['stats'].get('interested', 0) >= 50:
          sorted_events.append(processed_event)
      else:
        print("filter_by_popular")
        sorted_events.append(processed_event)
  else:
    print('No events found with attributes: {\'start_time\': date_regex}')

  return jsonify({'features': sorted_events, 'type': 'FeatureCollection'})

# Get event location and check whether coordinates are within the UCLA boundary
# as specified by ucla_border.geojson
def filter_by_oncampus(day):
  print("filter_by_oncampus")

  # Load GeoJSON file containing Polygon coordinates of UCLA
  ucla_path = os.path.join(os.path.dirname(__file__), 'ucla_border.geojson')
  with open(ucla_path) as f:
    js = json.load(f)

  # Create polygon shape from coordinates of UCLA's boundary
  polygon = shape(js['features'][0]['geometry'])

  # Get all events on the given day
  # If day is specified look only at events on given day
  # Or consider all events in database
  oncampus_events = []
  search_dict = {}

  if day:
    date_regex = event_utils.construct_date_regex(day)
    search_dict['start_time'] = date_regex
  events = event_utils.get_events_in_database(search_dict)

  for event in events:
    longitude = event['properties']['place']['location']['longitude']
    latitude = event['properties']['place']['location']['latitude']

    # Construct point based on event coordinates
    point = Point(longitude, latitude)

    if polygon.contains(point):
      oncampus_events.append(event)

  return jsonify({'features': oncampus_events, 'type': 'FeatureCollection'})

# Get event location and check whether coordinates are within the UCLA boundary
# as specified by ucla_border.geojson. If NOT, then use.
def filter_by_offcampus(day):
  print("filter_by_offcampus")

  # Load GeoJSON file containing Polygon coordinates of UCLA
  ucla_path = os.path.join(os.path.dirname(__file__), 'ucla_border.geojson')
  with open(ucla_path) as f:
    js = json.load(f)

  # Create polygon shape from coordinates of UCLA's boundary
  polygon = shape(js['features'][0]['geometry'])

  # Get all events on the given day
  # If day is specified look only at events on given day
  # Or consider all events in database
  offcampus_events = []
  search_dict = {}
  
  if day:
    date_regex = event_utils.construct_date_regex(day)
    search_dict['start_time'] = date_regex
  events = event_utils.get_events_in_database(search_dict)

  for event in events:
    longitude = event['properties']['place']['location']['longitude']
    latitude = event['properties']['place']['location']['latitude']

    # Construct point based on event coordinates
    point = Point(longitude, latitude)

    if not polygon.contains(point):
      offcampus_events.append(event)

  return jsonify({'features': offcampus_events, 'type': 'FeatureCollection'})

# Get current location of user and get all events whose coordinates are within
# a TODO radius of the user
def filter_by_nearby(search_dict):
  print("filter_by_nearby")
  # TODO JORGE

# Get all events that have free food
def filter_by_free_food(search_dict):
  print("filter_by_free_food")
  # TODO JORGE
