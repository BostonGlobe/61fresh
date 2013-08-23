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

def classify(real_url_hash):
   
   API_KEY = "***REMOVED***"
   '''
   # Open database connection
   db = MySQLdb.connect(
       host = '127.0.0.1', 
       user = 'condor', 
       passwd = 'globelab', 
       db = 'condor', 
       port = 3307)
   '''
   db = MySQLdb.connect(
    host = '127.0.0.1', 
    user = 'admin', 
    passwd = 'chess123', 
    db = 'test', 
    port = 3306)

   db.autocommit(True)

   #call calais function
   calais = Calais(API_KEY, submitter="python-calais classify")

   #run from train set
   pkfile = open('savedclassifier.pickle','rb')
   classifier = pickle.load(pkfile)

   # prepare a cursor object using cursor() method
   cursor = db.cursor()

   # Prepare SQL query to INSERT a record into the database.
   sql = "SELECT embedly_blob,real_url_hash  FROM  url_info WHERE real_url_hash='" + real_url_hash + "' LIMIT 1;" 

   # Execute the SQL command
   cursor.execute(sql)

   # Fetch all the rows
   results = cursor.fetchall()

   #browse through results
   for row in results:

      #get results
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
            
      analysetext.encode("utf8")
      analysetext = analysetext.encode("utf8")
      analysetext= analysetext.replace('"', '\'')
      
      
      #classifier 1
      #naive bayes
      _topic = classifier.classify(analysetext)
      _score = classifier.get_score(analysetext)
      
      #classifier 2
      #opencalais crosscheck   
      try:
         result = calais.analyze(analysetext)
         topic =  result.get_topics()
         score =  result.get_topic_score()
      except:
         topic = "None"
         score = 0.0
         sqlerr = 'INSERT INTO error_classify (real_url_hash, text) VALUES("' + real_url_hash+ '","' + analysetext + '");'
         cursor.execute(sqlerr)
         
      print real_url_hash
      print analysetext
      print topic
      print _topic
      
      #create json output      
      jsonOutput = "{\"topic\":\"%s\" , \"score\":\"%f\" , \"_topic\":\"%s\" , \"_score\":\"%f\"}" % (topic, score, _topic, _score) 
      sqlupdate = "UPDATE url_info SET topic_blob=\'" + jsonOutput + "\' WHERE real_url_hash=\'" + real_url_hash + "\';"
      x = cursor.execute(sqlupdate)
      trace =  'trace: updated url_info, url hash [%s]: %d' % (real_url_hash, x)

      #update score
      if topic == "Sports":
         cursor.execute("UPDATE url_info SET sports_score=\'" + str(score) + "\' WHERE real_url_hash=\'" + real_url_hash + "\';")
      elif topic == "None" and _topic == "sports":
         cursor.execute("UPDATE url_info SET sports_score=\'" + str(_score) + "\' WHERE real_url_hash=\'" + real_url_hash + "\';")
      else:
         cursor.execute("UPDATE url_info SET sports_score='0' WHERE real_url_hash=\'" + real_url_hash + "\';")

   db.close()
   pkfile.close()

