from mappening.utils.database import locations_collection
from mappening.api.utils import location_utils, location_helpers, tokenize

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import re
import os
from operator import itemgetter

# Route Prefix: /api/v2/locations
locations = Blueprint('locations', __name__)

# Enable Cross Origin Resource Sharing (CORS)
# cors = CORS(locations)

@locations.route('/', methods=['GET'])
def get_all_locations():
    """ 
    :Route: /

    :Description: Returns a JSON of all UCLA/Westwood locations in the database

    """
    output = []

    locations_cursor = locations_collection.find({}, {'_id': False})
    if locations_cursor.count() > 0:
      for loc in locations_cursor:
        output.append({"location": loc})
    else:
        print 'Cannot find any locations!'

    # Output typically contains name, city, country, latitude, longitude, state,
    # street, and zip for each location
    return jsonify({'locations': output})

# LOCATIONS SEARCH

@locations.route('/search', methods=['GET'])
def get_location_results():
    """ 
    :Route: /search?term=str&count=0

    :Description: Returns a JSON of all UCLA/Westwood locations filtered by the case-insensitive search `term` and limited by `count` in the number of returned results.

    :param term: A query component/parameter for the search term to filter by
    :type term: str

    :param count: An optional query component/parameter to limit the number of results returned by the search method
    :type count: int or None

    """
    term = request.args.get('term')
    count = request.args.get('count')

    if count:
      try:
        count = int(count)
      except:
        return 'Invalid count parameter, needs to be integer!'

    search_results = location_utils.search_locations(term)

    if not search_results:
      return "There were no results!"
    elif not count or count <= 0:
      return jsonify({"Locations": search_results})
    else:
      output = []
      limit = min(count, len(search_results))

      for i in range(0, limit):
        output.append(search_results[i])
      return jsonify({'Locations': output})

# GOOGLE WRAPPER

# Run Google Maps TextSearch on given query and print all results in JSON
# Print all results in JSON, a wrapper for Google's API
@locations.route('/google/search', methods=['GET'])
def get_google_search():
    """ 
    :Route: /google/search?api=text&term=str

    :Description: Returns a JSON of location results given by the Google Maps TextSearch or NearbySearch API on a given query. Essentially a wrapper for Google's Places API. The NearbySearch returns more results than TextSearch.

    :param term: A query component/parameter for the search term to filter by
    :type term: str

    :param api: An optional query component/parameter to specify which Google Maps Search API to use. Takes values `text` or `nearby` with the default value being `text`
    :type api: str or None

    """
    term = request.args.get('term')
    api = request.args.get('api')

    output = []

    # Default is text search API
    if api and api == 'text' or not api:
      output = location_helpers.google_textSearch(term)
    elif api and api == 'nearby':
      output = location_helpers.google_nearbySearch(term)
  

    return jsonify({'results': output})

@locations.route('/test', methods=['GET'])
def get_test():
    output = location_utils.get_locations_from_collection()
    # location_utils.add_locations_from_collection

    return jsonify({'results': output})
