from mappening.utils.database import events_fb_collection
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

# checks if the event overlaps the time period at all
# all arguments are datetime objects (can be compared and subtracted)
def in_time_range(event_start, event_end, period_start, period_end):
  if period_start <= event_start < period_end:
    return True
  if event_end:
    if event_start < period_end and event_end >= period_start:
      return True
  return False

# Morning = events whose start/end time is >= 3 am and < 12 pm
# Afternoon = events whose start/end time is >= 12 pm and < 5 pm
# Night = events whose start/end time is >= 5 pm and < 3 am

# End bound is not exclusive, so end of 1 period and start of another should be same
# Night is special case: 2 disjoint periods, if only looking at the current day
# each period needs even number of bounds, with bounds as tuples following (HH,MM) format
period_bounds = {
  'morning':   [(3,0), (12,0)],
  'afternoon': [(12,0), (17,0)],
  'night':     [(0,0), (3,0), (17,0), (24,0)]
}

# time_periods = list of strings of periods, e.g. ['morning', 'evening']
def filter_by_time(unfiltered_events, time_periods):
  print("filter_by_times: " + str(time_periods))

  # Extract all events of matching time periods and return results
  filtered_events = []

  for event in unfiltered_events:
    start_time = event['properties']['start_time']
    end_time = event['properties'].get('end_time')

    # Try to parse date
    end_time_obj = None
    try:
        # Use dateutil parser to get time zone
        start_time_obj = dateutil.parser.parse(start_time)
        if end_time:
          end_time_obj = dateutil.parser.parse(end_time)
    except ValueError:
        # Got invalid date string
        print('Invalid date string, cannot be parsed!')
        return None

    # Check for any kind of overlap of event and time period
    # If no end time is supplied, just make sure that the start time falls under the time period
    # TODO someone aka Katrina should check over this logic lmao
    plan_to_append = False
    for period in time_periods:
      bounds_list = period_bounds.get(period)
      if bounds_list and not plan_to_append:
        # just getting out info from list of lists of period bounds tuples, 1 period at a time
        for i in xrange(0, len(bounds_list), 2):
          period_start = start_time_obj.replace(hour=bounds_list[i][0], minute=bounds_list[i][1])
          num_days_ahead = bounds_list[i+1][0] / 24
          hours_past_day = bounds_list[i+1][0] % 24
          period_end = start_time_obj.replace(hour=hours_past_day, minute=bounds_list[i+1][1]) + timedelta(days=num_days_ahead)
          if in_time_range(start_time_obj, end_time_obj, period_start, period_end):
            plan_to_append = True
            break

    if plan_to_append:
      filtered_events.append(event)
  return filtered_events

# Using Facebook event statistics, sort by the number of people interested.
# Enable specification of top # of events to return or a threshold
# If (interested || going > threshold, default 50) then popular
def filter_by_popular(search_dict, threshold=50):
  # Sort events by # of interested
  sorted_events = []
  events_cursor = events_fb_collection.find(search_dict).sort('interested_count', -1)

  if events_cursor.count() > 0:
    print("filter_by_popular with threshold {0}".format(threshold))
    for event in events_cursor:
      processed_event = event_utils.process_event_info(event)
      if processed_event['properties']['stats'].get('attending', 0) >= threshold or processed_event['properties']['stats'].get('interested', 0) >= threshold:
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

  return oncampus_events

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

  return offcampus_events

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

  return nearby_events

# Get all events that have free food
# def filter_by_free_food(search_dict):
#   print("filter_by_free_food")
  # TODO JORGE ml

def is_valid_coords(in_lat, in_long):
  try:
    in_lat = float(in_lat)
    in_long = float(in_long)
  except:
    return False
  if in_lat <= 90 and in_lat >= -90 and in_long <= 180 and in_long >= -180:
    return True
  return False
