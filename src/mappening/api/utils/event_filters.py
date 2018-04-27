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

# Get the day's events
def get_day_events(search_dict, day):
  date_regex = event_utils.construct_date_regex(day)
  search_dict['start_time'] = date_regex

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

# Morning = events whose start/end time is >= 3 am and < 12 pm
# Afternoon = events whose start/end time is >= 12 pm and < 5 pm
# Night = events whose start/end time is >= 5 pm and < 3 am
def filter_by_time(unfiltered_events, time_period):
  print("filter_by_time")

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

  for event in unfiltered_events:
    start_time = event['properties']['start_time']
    end_time = event['properties']['start_time']

    # Try to parse date
    try:
        # Use dateutil parser to get time zone
        start_time_obj = dateutil.parser.parse(start_time)
        end_time_obj = dateutil.parser.parse(end_time)
    except ValueError:
        # Got invalid date string
        print('Invalid date string, cannot be parsed!')
        return None

    # Get the date string by YYYY-MM-DD format
    start_hour = datetime.strftime(start_time_obj, '%H')
    end_hour = datetime.strftime(end_time_obj, '%H')
    # print "Start hour is " + start_hour

    # Check whether the event start time falls under the time period
    should_append = False
    if is_morning and ((start_hour >= '03' and start_hour < '12') or (end_hour >= '03' and end_hour < '12')):
      # print('wow morning')
      should_append = True
    if is_afternoon and ((start_hour >= '12' and start_hour < '17') or (end_hour >= '12' and end_hour < '17')):
      # print('wow afternoon')
      should_append = True
    if is_night and (((start_hour >= '17' and start_hour <= '24') or (start_hour >= '00' and start_hour < '03')) or ((end_hour >= '17' and end_hour <= '24') or (end_hour >= '00' and end_hour < '03'))):
      # print('wow night')
      should_append = True

    # Make sure the event is only appended once
    if should_append:
      filtered_events.append(event)

  return filtered_events

# Using Facebook event statistics, sort by the number of people interested.
# Enable specification of top # of events to return or a threshold
# If (interested || going > 50) then popular
def filter_by_popular(search_dict, use_threshold=False):
  # Sort events by # of interested
  sorted_events = []
  events_cursor = events_current_collection.find(search_dict).sort('interested_count', -1)

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

  return sorted_events

# Get event location and check whether coordinates are within the UCLA boundary
# as specified by ucla_border.geojson
def filter_by_oncampus(unfiltered_events):
  print("filter_by_oncampus")

  # Load GeoJSON file containing Polygon coordinates of UCLA
  ucla_path = os.path.join(os.path.dirname(__file__), 'ucla_border.geojson')
  with open(ucla_path) as f:
    js = json.load(f)

  # Create polygon shape from coordinates of UCLA's boundary
  polygon = shape(js['features'][0]['geometry'])

  oncampus_events = []

  for event in unfiltered_events:
    longitude = event['properties']['place']['location']['longitude']
    latitude = event['properties']['place']['location']['latitude']

    # Construct point based on event coordinates
    point = Point(longitude, latitude)

    if polygon.contains(point):
      oncampus_events.append(event)

  return jsonify({'features': oncampus_events, 'type': 'FeatureCollection'})

# Get event location and check whether coordinates are within the UCLA boundary
# as specified by ucla_border.geojson. If NOT, then use.
def filter_by_offcampus(unfiltered_events):
  print("filter_by_offcampus")

  # Load GeoJSON file containing Polygon coordinates of UCLA
  ucla_path = os.path.join(os.path.dirname(__file__), 'ucla_border.geojson')
  with open(ucla_path) as f:
    js = json.load(f)

  # Create polygon shape from coordinates of UCLA's boundary
  polygon = shape(js['features'][0]['geometry'])

  offcampus_events = []

  for event in unfiltered_events:
    longitude = event['properties']['place']['location']['longitude']
    latitude = event['properties']['place']['location']['latitude']

    # Construct point based on event coordinates
    point = Point(longitude, latitude)

    if not polygon.contains(point):
      offcampus_events.append(event)

  return jsonify({'features': offcampus_events, 'type': 'FeatureCollection'})

# Get current location of user and get all events whose coordinates are within a certain radius of the user
# TODO JORGE for frontend implementation? Or however he gets current location
def filter_by_nearby(unfiltered_events, latitude, longitude):
  print("filter_by_nearby")

  nearby_events = []
  user_location = (latitude, longitude)

  for event in unfiltered_events:
    event_longitude = event['properties']['place']['location']['longitude']
    event_latitude = event['properties']['place']['location']['latitude']

    # Construct point based on event coordinates
    event_location = (event_latitude, event_longitude)

    # Within ~1000 feet or 0.3 km
    if haversine(user_location, event_location) < 0.3: 
      nearby_events.append(event)

  return jsonify({'features': nearby_events, 'type': 'FeatureCollection'})

# Get all events that have free food
# def filter_by_free_food(search_dict):
#   print("filter_by_free_food")
  # TODO JORGE ml

def is_float(value):
  try:
    float(value)
    return True
  except:
    return False
