# Run this file to backfill/rerun the algorithm for events_current_processed_collection
import pickle
import pandas as pd
from scipy.sparse import hstack
import itertools
import os
import numpy as np

# Needed to get access to mappening.utils.database when running just this file since this is under mappening.ml
if __name__ == "__main__":
    import sys
    sys.path.insert(0,'./../..')
    
# use this to change to this folder, since this might be run from anywhere in project...
from definitions import ML_PATH
from mappening.utils.database import events_current_processed_collection

# https://stackoverflow.com/questions/431684/how-do-i-change-directory-cd-in-python/13197763#13197763
# make a nice cd command that auto changes directory back when exited
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
        
def labelFreeFood(events):
    """
    :param X: should be list of dictionary elements
    Returns list of events updated with a list of categories
    """

    #ensure there is a name and description for machine learning
    for event in events:
        if 'name' not in event:
            event['name'] = ''
        if 'description' not in event:
            event['description'] = ''

    # Load data
    X = pd.DataFrame(events)
    # change path to load these files, for sure (correct directory)
    with cd(ML_PATH):
        with open(r"foodModel.pickle", "r") as model:
            classifier = pickle.load(model)
        with open(r"nameFoodVectorizer.pickle", "r") as model:
            nameVectorizer = pickle.load(model)
        with open(r"detailFoodVectorizer.pickle", "r") as model:
            detailVectorizer = pickle.load(model)

    X_name_transform = nameVectorizer.transform(X['name'])
    X_details_transform = detailVectorizer.transform(X['description'])
    X_total_transform = hstack([X_name_transform, X_details_transform])
    y_pred = classifier.predict(X_total_transform)

    for i, event in enumerate(events):
        # Turn numpy bool into boolean 
        event[u'free_food'] = bool(y_pred[i])
        
    #UNDO initial empty desctiption and name adds
    if event['name'] == '':
        del event['name']
    if event['description'] == '':
        del event['description']

    return events

def labelFoodAllCurrentEvents():
    """
    :Description: For backfilling the databases with free food tags, takes all the events in 
        events_current_processed_collection and replaces them with all events having a list of free food labels now
    """
    allEvents = [e for e in events_current_processed_collection.find()]
    print(allEvents)
    events_current_processed_collection.drop()
    allEvents = labelFreeFood(allEvents)
    for e in allEvents:
        events_current_processed_collection.insert(e)


if __name__ == "__main__":
    labelFoodAllCurrentEvents()
