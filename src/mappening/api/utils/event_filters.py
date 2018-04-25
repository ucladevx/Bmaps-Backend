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
from haversine import haversine

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

# Get current location of user and get all events whose coordinates are within a certain radius of the user
# TODO JORGE for frontend implementation? Or however he gets current location
def filter_by_nearby(search_dict, latitude, longitude, day):
  print("filter_by_nearby")

  # Get all events on the given day
  # If day is specified look only at events on given day
  # Or consider all events in database
  nearby_events = []
  search_dict = {}
  
  if day:
    date_regex = event_utils.construct_date_regex(day)
    search_dict['start_time'] = date_regex
  events = event_utils.get_events_in_database(search_dict)

  user_location = (latitude, longitude)

  for event in events:
    event_longitude = event['properties']['place']['location']['longitude']
    event_latitude = event['properties']['place']['location']['latitude']

    # Construct point based on event coordinates
    event_location = (event_latitude, event_longitude)

    # Within ~1000 feet or 0.3 km
    if haversine(user_location, event_location) < 0.3: 
      nearby_events.append(event)

  return jsonify({'features': nearby_events, 'type': 'FeatureCollection'})

# Get all events that have free food
def filter_by_free_food(search_dict):
  print("filter_by_free_food")
  # TODO JORGE ml

def is_float(value):
  try:
    float(value)
    return True
  except:
    return False
