from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack
import pandas as pd
import cPickle as pickle


# Needed to get access to mappening.utils.database when running just this file since this is under mappening.ml
import sys
sys.path.insert(0,'./../..')

from mappening.utils.database import events_ml_collection

def gatherCategorizedEvents():
    """Return panda dataframe of events with category, description, and name"""
    allCategorizedEvents = []
    allEvents = events_ml_collection.find({}, {"category": 1, "description": 1, "name": 1, "hoster": 1, "_id": 0})
    count = 0
    for e in allEvents:
        count += 1
        e['hoster'] = e['hoster']['name']
        if 'category' in e and 'description' in e and 'name' in e:
            allCategorizedEvents.append(e)
    modernEvents = reduceCategories(allCategorizedEvents)
    print count, "total events, learning from the", len(modernEvents), "well categorized events"
    return pd.DataFrame(modernEvents)

def reduceCategories(events):
    """Legacy Facebook events have old categories that are consolidated, OTHER will be discarded from the training data"""
    categoryMapping = {
        u'BOOK': u'LITERATURE',
        u'COMEDY': u'COMEDY_PERFORMANCE',
        u'CLASS': u'OTHER',
        u'DINING': u'FOOD',
        u'FAMILY': u'OTHER',
        u'FESTIVAL': u'PARTY',
        u'FOOD_TASTING': u'FOOD',
        u'FUNDRAISER': u'CAUSE',
        u'LECTURE': u'OTHER',
        u'MOVIE': u'FILM',
        u'NEIGHBORHOOD': u'OTHER',
        u'NIGHTLIFE': u'OTHER',
        u'RELIGIOUS': u'RELIGION',
        u'VOLUNTEERING': u'CAUSE',
        u'WORKSHOP': u'OTHER'
    }

    for e in events:
        category = e['category']
        if category in categoryMapping:
            e['category'] = categoryMapping[category]
    reducedEvents = [e for e in events if e['category'] != u'OTHER']
    return reducedEvents

def trainModels():
    X = gatherCategorizedEvents()

    # create the transform
    nameVectorizer = TfidfVectorizer(stop_words='english')
    detailVectorizer = TfidfVectorizer(stop_words='english')

    # tokenize and build vocab on name and description seperately
    X_name_transform = nameVectorizer.fit_transform(X['name'])
    X_details_transform = detailVectorizer.fit_transform(X['description'])
    #TODO: Learn on hoster details too
    X_total_transform = hstack([X_name_transform, X_details_transform])

    # train model
    rf = RandomForestClassifier(n_estimators=150, max_depth=None)
    rf.fit(X_total_transform, X['category'])

    #save model
    with open(r"categorizationModel.pickle", "wb") as output_file:
        pickle.dump(rf, output_file)

    with open(r"nameVectorizer.pickle", "wb") as output_file:
        pickle.dump(nameVectorizer, output_file)

    with open(r"detailVectorizer.pickle", "wb") as output_file:
        pickle.dump(detailVectorizer, output_file)

if __name__ == "__main__":
    trainModels()
