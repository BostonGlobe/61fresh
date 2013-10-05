#!/usr/bin/python

import json
from ingest_lib import *
import sys
import time

config = getConfig()

t = getTwitter(config)
mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
q = TweetQueue(config)

limited_list_statuses = RateLimitedAPICall(t.lists.statuses,15*60,175)

class ListInfo:
    def __init__(self):
        self.pointer = 0
        self.updateFromDB()

    def updateFromDB(self):
        print "updating from db"
        cur.execute("SELECT list_id FROM users WHERE list_id IS NOT NULL GROUP BY list_id HAVING COUNT(*) > 4990")
        self.lists = ["a%s" % x['list_id'] for x in cur]
        self.last_updated = time.time()

    def getAList(self):
        out = self.lists[self.pointer]
        self.pointer += 1
        if self.pointer >= len(self.lists):
            self.pointer = 0
            if time.time() > (self.last_updated + 60*60):
                self.updateFromDB()
        return out
    
list_info = ListInfo()
latest_tweet_by_list = {}

def doList(this_list):
    print "doing list ", this_list
    response = limited_list_statuses(owner_screen_name=config['twitter']['screen_name'],slug=this_list,count=200)
    if len(response) > 0:
        print len(response)
        q.enqueueTweets(response)
        new_latest_tweet = response[0]['id']
        oldest_tweet = response[-1]['id']
        if this_list in latest_tweet_by_list:
            while oldest_tweet > latest_tweet_by_list[this_list]:
                print "Going back for more ", oldest_tweet
                response = limited_list_statuses(owner_screen_name=config['twitter']['screen_name'],slug=this_list,count=200,max_id=oldest_tweet)
                q.enqueueTweets(response)
                if len(response) == 0 or oldest_tweet == response[-1]['id']:
                    break
        latest_tweet_by_list[this_list] = new_latest_tweet


@mainloop
def go():
    doList(list_info.getAList())

go()
