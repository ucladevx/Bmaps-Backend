#if trainModels() doesn't have cateogirzationModel appear in git, its b/c theres a hard limit of 100MB to files, so lower complexity of training model
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.externals import joblib 
from scipy.sparse import hstack
import pandas as pd

##Needed to get access to mappening.utils.database since this is under mappening.ml
import sys
sys.path.insert(0,'./../..')
from mappening.utils.secrets import MLAB_USERNAME, MLAB_PASSWORD
from pymongo import MongoClient
import pandas as pd

old_mappening_uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connections
events_client = MongoClient(old_mappening_uri)
events_db = events_client['mappening_data']
events_ml = events_db.events_ml

def gatherFreeFoodEvents():
    """Return panda dataframe of events with category, description, and name"""
    allFreeFoodLabeledEvents = []
    allEvents = events_ml.find({}, {"free_food": 1, "description": 1, "name": 1, "hoster": 1, "_id": 0})
    count = 0
    for e in allEvents:
        count += 1
        e['hoster'] = e['hoster']['name']
        if 'free_food' in e and 'description' in e and 'name' in e:
            allFreeFoodLabeledEvents.append(e)
    print(count, "total events, learning from the", len(allFreeFoodLabeledEvents), "well labeled events")
    return pd.DataFrame(allFreeFoodLabeledEvents)

def trainFoodModel():
    X = gatherFreeFoodEvents()

    # create the transform
    nameVectorizer = TfidfVectorizer(stop_words='english')
    detailVectorizer = TfidfVectorizer(stop_words='english')

    # tokenize and build vocab on name and description seperately
    X_name_transform = nameVectorizer.fit_transform(X['name'])
    X_details_transform = detailVectorizer.fit_transform(X['description'])
    #TODO: Learn on hoster details too
    X_total_transform = hstack([X_name_transform, X_details_transform])

    # train model
    rf = RandomForestClassifier(n_estimators=10, max_depth=60)
    rf.fit(X_total_transform, X['free_food'])

    # save model
    joblib.dump(rf, 'foodModel.jl')
    joblib.dump(nameVectorizer, 'nameFoodVectorizer.jl')
    joblib.dump(detailVectorizer, 'detailFoodVectorizer.jl')
    print("Successfully trained and saved categorization models")

if __name__ == "__main__":
    trainFoodModel()
