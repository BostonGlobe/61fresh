#!/usr/bin/python
import MySQLdb
import nltk
import sys
import json
from calais import Calais
from nclassifier import Classifier
import codecs
import pickle
import time

API_KEY = "***REMOVED***"


try:
	with open('config-local.json') as fh:
		config = json.load(fh)
except IOError:
	with open('config.json') as fh:
		config = json.load(fh)

db = MySQLdb.connect(
	host=config['mysql']['host'],
	port=config['mysql']['port'],
 	user=config['mysql']['user'],
 	passwd=config['mysql']['password'],
 	db=config['mysql']['database'],
	use_unicode=True,
    	charset="utf8")

db.autocommit(True)

calais = Calais(API_KEY, submitter="python-calais classify")

'''
run classifier
'''

'''
run from train set
'''
pkfile = open('savedclassifier.pickle','rb')
classifier = pickle.load(pkfile)

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Prepare SQL query to INSERT a record into the database.
sql = "SELECT embedly_blob,real_url_hash  FROM  url_info WHERE topic_blob IS NULL LIMIT 200;"
i = 0

# Execute the SQL command
cursor.execute(sql)

# Fetch all the rows
results = cursor.fetchall()
for row in results:
   print '-------------------------------------------------'
   i = i + 1
   real_url_hash = row[1]
   jsondecode = json.loads(row[0])
   title = jsondecode['title']
   description = jsondecode['description']
   url = jsondecode['url']

   if title and description and url:
      analysetext =  title + ' ' + description + ' ' + url
   else:
      analysetext = ' '
      if title:
         analysetext = analysetext  + ' ' +  title
      if description:
         analysetext = analysetext  + ' ' +  description
      if url:
         analysetext = analysetext  + ' ' +  url
   # analyse
   #x = classifier.classify(txtText)
  
   '''
   decode text
   if isinstance(analysetext, unicode):
      print ":: unicode"
   elif isinstance(analysetext, str):
      print ":: Not unicode"
   else: 
      print ":: error"
   unicode problem fix 
   '''

   analysetext.encode("utf8")
   analysetext = analysetext.encode("utf8")

   print i   
   '''
   if isinstance(analysetext, unicode):
      print ":: unicode"
   elif isinstance(analysetext, str):
      print ":: normal string"
   else: 
      print ":: error"
   '''

   '''
   classifier 1
   '''
   print analysetext
   _topic = classifier.classify(analysetext)
   _score = classifier.get_score(analysetext)
   if _topic:
      print 'topic:' + _topic
      print 'score:%f'% (_score*100)
   else:
      _topic = "None"
      _score = 0

   '''
   rate limit issues
   Submission Rate (per second), 4, 
   '''
   time.sleep( 0.3 )

   '''
   classifier 2
   '''
   #opencalais crosscheck
   print '================'
   if real_url_hash in ('e3cb4b6333506ffe5d746c9fabe32a00f9513f46', '76a134d8cb993198d89da02889592d3984a05861', 'c55fc7c88b1d9c0a58a1f29e44f9e0a69f1cc3fa'):
      result = calais.analyze("None")
   else:
      result = calais.analyze(analysetext)
   topic =  result.get_topics()
   score =  result.get_topic_score()
   if topic:
         print 'OC topic:' + topic
         print 'OC score:%f'% (score*100)
   else:
      topic = "None"
      score = 0
   print '================'
   jsonOutput = "{\"topic\":\"%s\" , \"score\":\"%f\" , \"_topic\":\"%s\" , \"_score\":\"%f\"}" % (topic, score, _topic, _score) 
   print jsonOutput

   sqlupdate = "UPDATE condor.url_info SET topic_blob=\'" + jsonOutput + "\' WHERE real_url_hash=\'" + real_url_hash + "\';"
   print sqlupdate
   x = cursor.execute(sqlupdate)
   print 'trace: updated url_info, url hash [%s]: %d' % (real_url_hash, x)

   '''
   update score
   '''
   if topic == "Sports":
      cursor.execute("UPDATE condor.url_info SET sports_score=\'" + str(score) + "\' WHERE real_url_hash=\'" + real_url_hash + "\';")
   elif topic == "None" and _topic == "sports":
      cursor.execute("UPDATE condor.url_info SET sports_score=\'" + str(_score) + "\' WHERE real_url_hash=\'" + real_url_hash + "\';")
   else:
      cursor.execute("UPDATE condor.url_info SET sports_score='0' WHERE real_url_hash=\'" + real_url_hash + "\';")

   '''
   debug, check the table
   '''
   cursor.execute("SELECT real_url_hash, topic_blob FROM condor.url_info where real_url_hash=\'" + real_url_hash + "\';")
   res = cursor.fetchall()
   for line in res:
      topic_blob_ =line[1]
      real_url_hash_ = line[0]
      print "URL:" + real_url_hash_
      print "TOPIC:" + topic_blob_
# disconnect
db.close()
pkfile.close()


