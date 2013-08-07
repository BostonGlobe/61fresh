#!/usr/bin/python

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import datetime
import json
import MySQLdb
import MySQLdb.cursors
from urllib import quote
import urllib2
import sys

hashtag = sys.argv[1]

conn = MySQLdb.connect(
	host='***REMOVED***',
 	user='condor',
 	passwd='condor',
 	db ='condor',
	use_unicode=True,
    charset="utf8",
    cursorclass = MySQLdb.cursors.DictCursor)
cur = conn.cursor()

cur.execute("SET time_zone='+0:00'")

recent_query = """
select real_url as url,count(distinct tweeted_urls.user_id) as total_tweets, MIN(tweeted_urls.created_at) as first_tweeted, 
	TIMESTAMPDIFF(HOUR,MIN(tweeted_urls.created_at),NOW()) as age, real_url_hash as hash, domain as source, embedly_blob 
from tweeted_urls left join url_info using(real_url_hash) 
	left join tweeted_hashtags using (tweet_id) 
where hashtag='"""+hashtag+"""'  
	and real_url is not null 
	and tweeted_urls.created_at>adddate(now(),interval -1 day) 
group by real_url 
having age < 24
order by total_tweets desc;
"""
links = []

cur.execute(recent_query)
for row in cur:
	frac_age = float(row['age'])/24.0
	if row['age'] < 4:
		multiplier = 1.20-frac_age
	elif row['age'] < 12:
		multiplier = 1.05-frac_age
	else:
		multiplier = 1.05-frac_age
	row['hotness'] = multiplier * row['total_tweets']
	links.append(row)

links.sort(key=lambda x: x['hotness'],reverse=True)

links = links[:10]

to_get_from_embedly = [x for x in links if x['embedly_blob'] is None]

if len(to_get_from_embedly) > 0:
	embedly_list = json.load(urllib2.urlopen("http://api.embed.ly/1/extract?key=***REMOVED***&urls=" + ','.join([quote(x['url']) for x in to_get_from_embedly])))

	for (link,embedly) in zip(to_get_from_embedly,embedly_list):
		embedly_blob = json.dumps(embedly)
		cur.execute("insert into url_info (real_url_hash,embedly_blob) values (%s,%s) on duplicate key update embedly_blob = %s",(link['hash'],embedly_blob,embedly_blob))
		for target in links:
			if target['hash'] == link['hash']:
				target['embedly_blob'] = embedly_blob
				break
	conn.commit()

for link in links:
	embedly = json.loads(link['embedly_blob'])
	del link['embedly_blob']
	link['first_tweeted'] = link['first_tweeted'].isoformat()
	link['title'] = embedly['title']
	link['description'] = embedly['description']
	for img in embedly['images']:
		if img['width'] > 300:
			link['image_url'] = img['url']
			break
	link['tweeters'] = []
	cur.execute("select screen_name, name, followers_count, profile_image_url, text, tweet_id, tweeted_urls.created_at as created_at from users join tweeted_urls using(user_id) join tweets using(tweet_id) where real_url_hash = %s group by tweeted_urls.user_id order by followers_count desc",(link['hash']))
	for row in cur:
		row['tweet_id'] = str(row['tweet_id'])
		row['created_at'] = row['created_at'].isoformat()
		link['tweeters'].append(row)
	del link['hash']

out = {	'generated_at': datetime.datetime.utcnow().isoformat(),
		'articles':links[:10]}

# print json.dumps(out,indent=1)
json_out = json.dumps(out,indent=1)
print json_out
s3_conn = S3Connection('***REMOVED***', '***REMOVED***')
k = Key(s3_conn.get_bucket('condor.globe.com'))
k.key = 'json/'+hashtag+'.json'
k.set_contents_from_string(json_out)
k.set_acl('public-read')