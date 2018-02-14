from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin

import nltk
nltk.download('perluniprops')
nltk.download('nonbreaking_prefixes')
nltk.download('stopwords')
nltk.download('punkt')

import re
import string
from tqdm import tqdm
from nltk.tokenize.moses import MosesTokenizer, MosesDetokenizer

from nltk.corpus import wordnet as wn

Process = Blueprint('Process', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Process)

@Process.route('/api/process/<text>', methods=['GET'])
def processText(text):
    tokenizer = MosesTokenizer() #tokenizers are basically an advanced split
    detokenizer = MosesDetokenizer()

    # text = "testing this. UCLA ackerman for Boelter 3400 why engr 4 at UCLA. Rstaurat of Los Angeles LA, Room 4760 @ the place - UCLA"
    # print "Original text: " + text

    processed_text = tokenizer.tokenize(text)

    # print "Tokenized text: " + " ".join(processed_text)

    # Need to detokenize to get all the weird symbols back as symbols
    # Am I doing this badly
    # Wanted to get & not amp and ' not apos'
    processed_text = detokenizer.detokenize(processed_text)

    # print "Detokenized text: " + " ".join(processed_text)

    processed_text = preprocess(processed_text)

    # print "Processed text: " + " ".join(processed_text)

    return " ".join(processed_text) #jsonify(processed_text)

def matchNotX(strg, search=re.compile(r'[^!#$%&()*+,-./:;<=>?@\\^_}|{~0123456789]').search):
    """make sure word has something than punctuation"""
    return bool(search(strg)) #make sure word has something other than punctuation

def preprocess(text):
    """Remove all useless words and punct, make lowercase"""
    # Dorm Dormitory Building Bldg Ofc Office 
    # TODO why is it case sensitive wtf
    stoplist = set('for a of the and to in . / center field plaza residential los ucla angeles la westwood room dormitory dorm building bldg ofc office hall the & @ at - ,'.split())
    stoplist = set(nltk.corpus.stopwords.words('english')) | stoplist | set(string.punctuation)
    return [word.strip(string.punctuation).lower() for word in text if word.lower() not in stoplist and matchNotX(word)]    
