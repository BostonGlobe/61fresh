import sys
sys.path.append('./classifier')
import MySQLdb
import nltk
import json
from calais import Calais
from nclassifier import Classifier
import codecs
import pickle
import time
import classifyfreshlib

urlx = 'c55fc7c88b1d9c0a58a1f29e44f9e0a69f1cc3fa'
classifyfreshlib.classify(urlx)


