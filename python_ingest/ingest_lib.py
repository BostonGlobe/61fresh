#/usr/bin/python

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
from dateutil.parser import parse
import json
import MySQLdb
import MySQLdb.cursors
import os
import sys
import time
import twitter

def getConfig():
	CONDOR_ENV = os.environ['CONDOR_ENV']
	CONDOR_HOME = env = os.environ['CONDOR_HOME']

	if not CONDOR_ENV:
		print "you must set the CONDOR_ENV bash variable (production, test, etc)"
	if not CONDOR_HOME:
		condor_home="~/condor"

	try:
		with open("%s/config/config-%s.json" % (CONDOR_HOME,CONDOR_ENV)) as fh:
			config = json.load(fh)
	except IOError:
		with open('%s/config/config.json' % CONDOR_HOME) as fh:
			config = json.load(fh)
	return config

def getTwitter(config):
	return twitter.Twitter(auth=twitter.OAuth(config['twitter']['access_token'],
											  config['twitter']['access_token_secret'],
											  config['twitter']['consumer_key'],
											  config['twitter']['consumer_secret']))

def getMySQL(config):
	conn = MySQLdb.connect(
		host=config['mysql']['host'],
		port=config['mysql']['port'],
	 	user=config['mysql']['user'],
	 	passwd=config['mysql']['password'],
	 	db=config['mysql']['database'],
		use_unicode=True,
	    charset="utf8",
	    cursorclass = MySQLdb.cursors.DictCursor)
	return conn

class TweetQueue:
	def __init__(self,config):
		self.conn = SQSConnection(config["aws-s3"]["access-key-id"], config["aws-s3"]["secret-access-key"])
		self.q = self.conn.create_queue('condor-tweets')

	def enqueueTweets(tweets):
		if len(tweets) > 0:
			m = Message()
			m.set_body(json.dumps(map(slimTweet,tweets)))
			self.q.write(m)


class UserQueue:
	def __init__(self,config):
		self.conn = SQSConnection(config["aws-s3"]["access-key-id"], config["aws-s3"]["secret-access-key"])
		self.q = self.conn.create_queue('condor-users')

	def enqueueUsers(users):
		if len(users) > 0:
			m = Message()
			m.set_body(json.dumps(users))
			self.q.write(m)


def slimTweet(tweet):
	out = {'id': tweet['id'],
		   'text': tweet['text'],
		   'created_at': dateutil.parser.parse(tweet['created_at']).isoformat(),
		   'user_id': tweet['user']['id']}
	if 'retweeted_status' in tweet:
		out['retweeted_tweet_id'] = tweet['retweeted_status']['id_str']
	out['urls'] = [x['expanded_url'] for x in tweet['entities']['urls']]
	if 'media' in tweet['entities']:
		out['urls'].extend([x['expanded_url'] for x in tweet['entities']['media']])
	out['hashtags'] = [x['text'] for x in tweet['entities']['hashtags']]
	out['user_mentions'] = [x['id'] for x in tweet['entities']['user_mentions']]
	return out

def mainloop(fn):
	def new(*args):
		while 1:
			try:
				fn(*args)
			except (KeyboardInterrupt, SystemExit):
        		raise
    		except:
    			print sys.exc_info()
    			time.sleep(5)
    return new


class RateLimitedAPICall:
    def __init__(self,api_method,window_length,calls_per_window):
        self.api_method = api_method
        self.window_length = window_length
        self.calls_per_window = calls_per_window
        self.window_end = 0
    
    def __call__(self,**kwargs):
        now = time.time()
        if now > self.window_end:
            self.window_end = now+self.window_length
            self.calls_left = self.calls_per_window
        seconds_per_call = float(self.window_length)/self.calls_per_window
        seconds_to_sleep = self.window_end-seconds_per_call*self.calls_left-now
        self.calls_left -= 1
        if seconds_to_sleep < 0:
            print "Didn't have to sleep. Looks like we're falling behind!"
        else:
            time.sleep(seconds_to_sleep)
        return self.api_method(**kwargs)