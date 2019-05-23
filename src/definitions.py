import os

# to save the top path to /src, for changing directories later
SRC_PATH = os.path.dirname(os.path.abspath(__file__))
# this just traverses to subdirectories: each argument = 1 level down
ML_PATH = os.path.join(SRC_PATH, 'mappening', 'ml')
API_UTILS_PATH = os.path.join(SRC_PATH, 'mappening', 'api', 'utils')

# Updated coordinates of Bruin Bear
CENTER_LATITUDE = '34.070966'
CENTER_LONGITUDE = '-118.445'

# Latitude and Longitude range from (-90, 90) and (-180, 180)
INVALID_COORDINATE = 420

# For comprehension: School of Theater, Film, TV within radius 700
# Hammer Museum within radius 1300, Saffron and Rose within radius 1800
RADIUS = "2000"

# the time period before now, IN DAYS
# for finding and updating events instead of removing them 
BASE_EVENT_START_BOUND = 0

