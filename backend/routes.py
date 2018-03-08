/api/locations/

# Get all locations
@locations.route('/', methods=['GET'])

# UPDATE DB

# Add locations to db from total_events_collection
# Should be hooked up so everytime we get new events we add their location data to db
@locations.route('/add/<collection>', methods=['PUT'])

# API

# Pretty print of above route json
@locations.route('/search/<place_query>', methods=['GET'])

# Get top result from coordinates
# TODO FIX IMPLEMENTATION
@locations.route('/search/<place_query>/<num_results>', methods=['GET'])

# GOOGLE WRAPPER 

# Perform google text search on given string query
# Print all results in JSON, a wrapper
@locations.route('/google/search/text/<place_query>', methods=['GET'])

# Perform google nearby search on given string query
# Print all results in JSON, a wrapper
@locations.route('/google/search/nearby/<place_query>', methods=['GET'])


# UTILS

# Given location string get all relevant locations found in our db, json
# @locations.route('/coordinates/<place_query>', methods=['GET'])


# TEST

# Given unknown locations, run through locations api and add to appropriate databases for manual verification
@locations.route('/process/unknown', methods=['POST'])

# Go through events_ml_collection and run every location name through locations api
# See if resulting coordinates match what actual location data for event is
# Manually verify any conflicting results
23546567890
@locations.route('/test/locations', methods=['GET'])


# JSON, one-time functions

# Given JSON file insert locations to db
# e.g. sampleData.json
@locations.route('/insert_locations', methods=['POST'])

# Go through JSON file and add all tokenized names to alternate names
# TODO write to file
@locations.route('/tokenize_names', methods=['GET'])

# Go through json file and add all names with UCLA stripped from it to alternate names
# TODO write to file
@locations.route('/UCLA_names', methods=['GET'])

# Given JSON data, fill out missing information of street/zip/latitude/longitude using google api results
# May be incorrect
@locations.route('/location_data', methods=['GET'])

