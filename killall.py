#!/usr/bin/python

import MySQLdb
import MySQLdb.cursors

conn = MySQLdb.connect(
	host='***REMOVED***',
 	user='condor',
 	passwd='condor',
 	db ='condor',
	use_unicode=True,
    charset="utf8",
    cursorclass = MySQLdb.cursors.DictCursor)

cur = conn.cursor()
to_kill = []

cur.execute("show processlist")
for row in cur:
	if row['Info'] is not None and row['Info'].startswith("select screen_name, name, followers_count, profile_image_url, text, tweet_id, tweeted_urls.created_a"):
		to_kill.append(row['Id'])

for pid in to_kill:
	cur.execute("kill %s"%pid)
