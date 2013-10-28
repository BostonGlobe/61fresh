#!/usr/bin/python

import json
from ingest_lib import *
import time

config = getConfig()

t = getTwitter(config)
tq = TweetQueue(config)
uq = UserQueue(config)

limited_search = RateLimitedAPICall(t.search.tweets,15*60,175)

search_since_id = '0'

mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
cur.execute("SET time_zone='+0:00'")

cur.execute("SELECT user_id FROM users")
existing_users = set([x['user_id'] for x in cur])
mysql_conn.close()

@mainloop
def do_search():
        global search_since_id
        response = limited_search(geocode='42.3583,-71.0603,10mi', result_type= 'recent', count=100, since_id=search_since_id,_timeout=15)
        tweets = [tweet.get('retweeted_status',tweet) for tweet in response['statuses']]
        tq.enqueueTweets(tweets)
        users = list(set([tweet['user']['id'] for tweet in tweets if tweet['user']['id'] not in existing_users]))
       	print "geo search got %s tweets, %s new users" % (len(tweets), len(users))
        if len(users) > 0:
            uq.enqueueUsers(users)
            existing_users.update(users)
        if len(tweets) > 0:
            search_since_id = response['search_metadata']['max_id_str']
        else:
            search_since_id = '0'

do_search()
