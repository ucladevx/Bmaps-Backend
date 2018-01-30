from ourDb import events_collection, total_events_collection
import re
import nltk
import string

from gensim.models import Phrases
from nltk.corpus import wordnet as wn

class PreprocessText:
    def matchNotX(strg, search=re.compile(r'[^!#$%&()*+,-./:;<=>?@\\^_}|{~0123456789]').search):
        """make sure word has something than punctuation"""
        return bool(search(strg)) #make sure word has something other than punctuation

    def preprocess(texts):
        stoplist = set('for a of the and to in . / '.split())
        stoplist = set(nltk.corpus.stopwords.words('english')) | stoplist | set(string.punctuation)
        return [[word.strip(string.punctuation).lower() for word in document if word not in stoplist and matchNotX(word)] for document in texts]

    ##generating phrases
    def getPhrases(texts):
        texts = getMedTerms(texts)
        bigram = Phrases(texts, min_count=10)
        return bigram


    def topBigrams(texts, n, tri=False):
        flatTexts = []
        for text in texts:
            for word in text:
                flatTexts.append(word)
        bigram_measures = nltk.collocations.BigramAssocMeasures()
        trigram_measures = nltk.collocations.TrigramAssocMeasures()
        topAnswers = []
        if tri:
            finder = nltk.collocations.TrigramCollocationFinder.from_words(flatTexts)
            finder.apply_freq_filter(7)
            return finder.nbest(trigram_measures.pmi, n)
        else:
            finder = nltk.collocations.BigramCollocationFinder.from_words(flatTexts)
            finder.apply_freq_filter(7)
            return finder.nbest(bigram_measures.pmi, n)

def gatherCategorizedEvents():
    allCategorizedEvents = []
    allEvents = total_events_collection.find({}, {"category": 1, "description": 1, "name": 1})
    count = 0
    for e in allEvents:
        count += 1
        if e.get('category', None) != None:
            allCategorizedEvents.append(e)
    print count, "events and using the", len(allCategorizedEvents), "categorized events"
    return allCategorizedEvents

X = gatherCategorizedEvents()
print(X)
