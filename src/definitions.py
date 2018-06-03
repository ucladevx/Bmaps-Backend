import os

# to save the top path to /src, for changing directories later
SRC_PATH = os.path.dirname(os.path.abspath(__file__))
# this just traverses to subdirectories: each argument = 1 level down
ML_PATH = os.path.join(SRC_PATH, 'mappening', 'ml')