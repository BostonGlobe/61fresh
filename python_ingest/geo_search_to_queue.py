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

@mainloop
def do_search():
        response = limited_search(geocode='42.3583,-71.0603,10mi', result_type= 'recent', count=100, since_id=search_since_id)
        tweets = [tweet.get('retweeted_status',tweet) for tweet in response['statuses']]
        tq.enqueueTweets(tweets)
        uq.enqueueUsers([tweet['user']['id'] for tweet in tweets])
        search_since_id = response['search_metadata']['max_id_str']

do_search()