#!/usr/bin/python

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
from collections import deque
import dateutil.parser
import hashlib
import json
from ingest_lib import *

config = getConfig()

sqs_conn = SQSConnection(config["aws-s3"]["access-key-id"], config["aws-s3"]["secret-access-key"])
q = sqs_conn.create_queue('condor-tweets')

mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
cur.execute("SET time_zone='+0:00'")

class TweetMemory:
    def __init__(self, max_len):
        self.max_len = max_len
        self.tset = set()
        self.tqueue = deque()

    def pare(self, tweets):
        out = []
        for tweet in tweets:
            if tweet['id'] not in self.tset:
                out.append(tweet)
                self.tset.add(tweet['id'])
                self.tqueue.append(tweet['id'])
        while len(self.tqueue) > self.max_len:
            self.tset.remove(self.tqueue.popleft())
        return out


def insertTweets(tweets):
    rows = [(tweet['id'], tweet['text'], tweet['created_at'], tweet['user_id'], tweet.get('retweeted_tweet_id',None)) for tweet in tweets]
    if len(rows) > 0:
        cur.executemany("INSERT IGNORE INTO tweets (tweet_id, text, created_at, user_id, retweeted_tweet_id) VALUES (%s,%s,%s,%s,%s)",rows)
        mysql_conn.commit()

def insertURLs(tweets):
    rows = []
    for tweet in tweets:
        rows.extend([(url, hashlib.sha1(url).hexdigest(), tweet['user_id'], tweet['id'], tweet['created_at']) for url in tweet['urls']])
    if len(rows) > 0:
        cur.executemany("INSERT IGNORE INTO tweeted_urls (url, url_hash, user_id, tweet_id, created_at) VALUES (%s,%s,%s,%s,%s)",rows)
        mysql_conn.commit()

def insertHashtags(tweets):
    rows = []
    for tweet in tweets:
        rows.extend([(hashtag, tweet['user_id'], tweet['id'], tweet['created_at']) for hashtag in tweet['hashtags']])
    if len(rows) > 0:
        cur.executemany("INSERT IGNORE INTO tweeted_hashtags (hashtag, user_id, tweet_id, created_at) VALUES (%s,%s,%s,%s)",rows)
        mysql_conn.commit()

def InsertMentions(tweets):
    rows = []
    for tweet in tweets:
        rows.extend([(mention, tweet['user_id'], tweet['id'], tweet['created_at']) for mention in tweet['user_mentions']])
    if len(rows) > 0:
        cur.executemany("INSERT IGNORE INTO tweeted_mentions (mentioned_user_id, user_id, tweet_id, created_at) VALUES (%s,%s,%s,%s)",rows)
        mysql_conn.commit()

tweet_memory = TweetMemory(100000)

@mainloop
def go():
    m = q.read(wait_time_seconds=20)
    if m is not None:
        tweets = json.loads(m.get_body())
        rec_size = len(tweets)
        tweets = tweet_memory.pare(tweets)
        for tweet in tweets:
            tweet['created_at']=dateutil.parser.parse(tweet['created_at'])
            if tweet['created_at'].utcoffset().total_seconds()<1.0:
                tweet['created_at'] = tweet['created_at'].replace(tzinfo=None)  # MySQL doesn't know about timezones, so we're doing this so it doesn't show a warning
            else:
                raise ValueError('Tweet created_at is not in UTC.')
        print "inserting %s new tweets out of %s" % (len(tweets), rec_size)
        #print [x['created_at'] for x in tweets]
        insertTweets(tweets)
        insertURLs(tweets)
        insertHashtags(tweets)
        InsertMentions(tweets)
        q.delete_message(m)

go()
