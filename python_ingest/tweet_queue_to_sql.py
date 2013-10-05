#!/usr/bin/python

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
import hashlib
import json
from ingest_lib import *

config = getConfig()

sqs_conn = SQSConnection(config["aws-s3"]["access-key-id"], config["aws-s3"]["secret-access-key"])
q = sqs_conn.create_queue('condor-tweets')

mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
cur.execute("SET time_zone='+0:00'")

def insertTweets(tweets):
	rows = [(tweet['id'], tweet['text'], tweet['created_at'], tweet['user_id'], tweet.get('retweeted_tweet_id',None)) for tweet in tweets]
	if len(rows) > 0:
		cur.executemany("INSERT IGNORE INTO tweets (tweet_id, text, created_at, user_id, retweeted_tweet_id) VALUES (%s,%s,%s,%s,%s)",rows)
		mysql_conn.commit()

def insertURLs(tweets):
	rows = []
	for tweet in tweets:
		rows.extend([(url, hashlib.sha1(url).hexdigest(), tweet['user_id'], tweet['id'], tweet['created_at']) for url in tweets['urls']])
	if len(rows) > 0:
		cur.executemany("INSERT IGNORE INTO tweeted_urls (url, url_hash, user_id, tweet_id, created_at) VALUES (%s,%s,%s,%s,%s)",rows)
		mysql_conn.commit()

def insertHashtags(tweets):
	rows = []
	for tweet in tweets:
		rows.extend([(hashtag, tweet['user_id'], tweet['id'], tweet['created_at']) for hashtag in tweets['hashtags']])
	if len(rows) > 0:
		cur.executemany("INSERT IGNORE INTO tweeted_hashtags (hashtag, user_id, tweet_id, created_at) VALUES (%s,%s,%s,%s)",rows)
		mysql_conn.commit()

def InsertMentions(tweets):
	rows = []
	for tweet in tweets:
		rows.extend([(mention, tweet['user_id'], tweet['id'], tweet['created_at']) for mention in tweets['mentions']])
	if len(rows) > 0:
		cur.executemany("INSERT IGNORE INTO tweeted_mentions (mentioned_user_id, user_id, tweet_id, created_at) VALUES (%s,%s,%s,%s)",rows)
		mysql_conn.commit()

@mainloop
def go():
	m = q.read(wait_time_seconds=60)
	if m is not None:
		tweets = json.loads(m.get_body())
		print "inserting %s tweets" % len(tweets)
		insertTweets(tweets)
		insertURLs(tweets)
		insertHashtags(tweets)
		InsertMentions(tweets)
		q.delete_message(m)

go()
