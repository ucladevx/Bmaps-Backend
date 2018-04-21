from mappening.utils.database import events_current_collection
from mappening.api.utils import event_utils

from flask import Flask, jsonify, request, json, Blueprint
import requests
import json
from datetime import datetime, timedelta
import pytz
from pytz import timezone

# Route Prefix: /api/v2/events
event_filters = Blueprint('event_filters', __name__)

@event_filters.route('/filter', methods=['GET'])
def filter_events():
    """
    :Route: /filter?when=time&time=morning&time=afternoon&where=offcampus&popular=False&popular_threshold=False&food=True

    :Description: Returns GeoJSON of all events filtered by the specified filters. Filtering options include filtering by time, location, popularity, and whether or not an event has free food.

    :param when: An optional query component/parameter that specifies whether an event is happening now (event start time <= current time < event end time), is an upcoming event (event start time <= current time + 2 hours), or allows you to specify a time period with the `time` parameter. The parameter values can be `now`, `upcoming`, or `time`.
    :type term: str or None

    :param time: An optional query component/parameter that is only checked (and must be set) if the parameter `when` was set to value `time`. May have value `morning`, `afternoon`, or `night` where `morning` is from 3 am - 12 pm, `afternoon` is from 12 pm - 5 pm, and `night` is from 5 pm - 3 am. The start times are inclusive while the end times are exclusive. May have *multiple* values such as in example route above. Will return events that are in the morning or afternoon time period.
    :type date: str or None

    :param where: An optional query component/parameter that specifies a location filter for events. The parameter values can be `nearby`, `oncampus`, or `offcampus` where `nearby` filters for events within a TODO radius, `oncampus` gets locations within the UCLA boundary, and `offcampus` gets locations in Westwood and outside of the UCLA boundaries.
    :type category: str or None

    :param popular: An optional query component/parameter that returns events sorted in decreasing order of popularity. Based on Facebook event data and may not result in changes.
    :type category: boolean or None

    :param popular_threshold: An optional query component/parameter that only returns events that meet the following threshold: # interested || # going > 100. Returns events sorted in decreasing order of popularity. Based on Facebook event data and may not result in changes.
    :type category: boolean or None

    :param food: An optional query component/parameter that gets events that have free food at them. May not be 100% accurate.
    :type category: boolean or None

    """
    when = request.args.get('when')
    time = request.args.getlist('time')
    where = request.args.get('where')
    popular = request.args.get('popular')
    popular_threshold = request.args.get('popular_threshold')
    food = request.args.get('food')

    search_dict = {}
    output = []

    # Add to search dict 
    # Time filtering
    if when:
      if when == 'now':
        filter_by_happening_now(search_dict)
      elif when == 'upcoming':
        filter_by_upcoming(search_dict)
      elif when == 'time':
        if time:
          filter_by_time(search_dict, time)
          return jsonify({'time': time})
        else:
          return 'Expected time period to be set!'
      else:
        return 'Invalid value passed to `when` parameter.'

    # Location filtering
    if where:
      if where == 'nearby':
        filter_by_nearby(search_dict)
      elif where == 'oncampus':
        filter_by_oncampus(search_dict)
      elif where == 'offcampus':
        filter_by_offcampus(search_dict)
      else:
        return 'Invalid value passed to `where` parameter.'

    # Other filters
    if popular and popular.lower() == "true":
        if popular_threshold and popular_threshold.lower() == "true":
          filter_by_popular(search_dict, popular_threshold)
        else:
          filter_by_popular(search_dict)

    if food and food.lower() == "true":
      filter_by_free_food(search_dict)
      
    # return 'Success!'

    return event_utils.find_events_in_database(search_dict)


    # if term:
    #     term_regex = re.compile('.*' + term + '.*', re.IGNORECASE)
    #     search_dict["$or"] = [ {"name":term_regex}, {"description":term_regex} ] 
    # if date:
    #     date_regex = event_utils.construct_date_regex(date)
    #     search_dict['start_time'] = date_regex
    # if category:
    #     cat_regex_obj = re.compile('^{0}|{0}$'.format(category.upper()))
    #     search_dict['category'] = cat_regex_obj
    #     print(search_dict)

    # return event_utils.find_events_in_database(search_dict)

# Get current time and get all events whose start time <= current time < end time
def filter_by_happening_now(search_dict):
  print("filter_by_happening_now")

  now = pytz.timezone('America/Los_Angeles').localize(datetime.now())
  now = datetime.strftime(now, '%a, %d %b %Y %H:%M:%S')
  search_dict['$and'] = [ {"start_time":{"$lte": now}}, {"end_time":{"$gt": now}} ]

# Get current time and get all events whose start time is <= 2 hours for now
def filter_by_upcoming(search_dict):
  print("filter_by_upcoming")
  # in_two_hours = datetime.now() + timedelta(hours=2)
  # search_dict['start_time'] = {"$lte": in_two_hours}

# Morning = events whose start time is >= 3 am and < 12 pm
# Afternoon = events whose start time is >= 12 pm and < 5 pm
# Night = events whose start time is >= 5 pm and < 3 am
def filter_by_time(search_dict, time_period):
  print("filter_by_time")

# Using Facebook event statistics, sort by the number of people interested.
# Enable specification of top # of events to return or a threshold
# If (interested || going > 100) then popular
def filter_by_popular(search_dict, threshold=None):
  if threshold:
    print("filter_by_popular theshold")
  else:
    print("filter_by_popular")

# Get event location and check whether coordinates are within the UCLA boundary
# as specified by ucla_border.geojson
def filter_by_oncampus(search_dict):
  print("filter_by_oncampus")

# Get event location and check whether coordinates are within the UCLA boundary
# as specified by ucla_border.geojson. If NOT, then use.
def filter_by_offcampus(search_dict):
  print("filter_by_offcampus")

# Get current location of user and get all events whose coordinates are within
# a TODO radius of the user
def filter_by_nearby(search_dict):
  print("filter_by_nearby")
  # TODO JORGE

# Get all events that have free food
def filter_by_free_food(search_dict):
  print("filter_by_free_food")
  # TODO JORGE
