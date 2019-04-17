import os

# to save the top path to /src, for changing directories later
SRC_PATH = os.path.dirname(os.path.abspath(__file__))
# this just traverses to subdirectories: each argument = 1 level down
ML_PATH = os.path.join(SRC_PATH, 'mappening', 'ml')
API_UTILS_PATH = os.path.join(SRC_PATH, 'mappening', 'api', 'utils')

# Updated coordinates of Bruin Bear
CENTER_LATITUDE = '34.070966'
CENTER_LONGITUDE = '-118.445'

# the time period before now, IN DAYS
# for finding and updating events instead of removing them 
BASE_EVENT_START_BOUND = 0
