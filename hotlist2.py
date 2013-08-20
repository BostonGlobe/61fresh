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

if len(sys.argv)>1:
	age_in_hours = float(sys.argv[1])
else:
	age_in_hours = 12

popularity_weight=100

# for multi-day queries, don't consider recency, just a popularity rank
if age_in_hours>72:
	ignore_age=True 
else:
	ignore_age=False

conn = MySQLdb.connect(
	host='***REMOVED***',
 	user='condor',
 	passwd='globelab',
 	db ='condor',
	use_unicode=True,
    charset="utf8",
    cursorclass = MySQLdb.cursors.DictCursor)
cur = conn.cursor()

cur.execute("SET time_zone='+0:00'")
recent_query = """select real_url as url, count(distinct user_id) as total_tweets, 
MIN(created_at) as first_tweeted, TIMESTAMPDIFF(HOUR,MIN(created_at),NOW()) as age, 
real_url_hash as hash, domain as source, embedly_blob from tweeted_urls 
left join url_info using(real_url_hash) 
where domain in (select domain from domains where domain_set='boston') 
group by real_url having age < %s;""" % (age_in_hours)

links = []

cur.execute(recent_query)

#for row in cur:
#	frac_age = float(row['age'])/24.0
#	if (frac_age)
#	if row['age'] < 4:
#		multiplier = 4-(3*frac_age) 
#	elif row['age'] < 12:
#		multiplier = 1.05-frac_age
#	else:
#		multiplier = 1.05-frac_age
#	row['hotness'] = multiplier * row['total_tweets']

for row in cur:
	row['age']+=1
	age = row['age']
	popularity_factor = float((row['total_tweets']-2)*popularity_weight)
	age_factor = float(age * age)
	row['popularity_factor'] = popularity_factor
	row['age_factor'] = age_factor
	if ignore_age:
		row['hotness'] = popularity_factor
	else:
		row['hotness'] = popularity_factor / age_factor
		
	links.append(row)

links.sort(key=lambda x: x['hotness'],reverse=True)

links = links[:20]

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

out = {'generated_at': datetime.datetime.utcnow().isoformat(), 'age_in_hours':age_in_hours,'popularity_weight':popularity_weight,'diagnostics':True,
		'articles':links[:50]}
# print json.dumps(out,indent=1)

s3_conn = S3Connection('***REMOVED***', '***REMOVED***')
k = Key(s3_conn.get_bucket('condor.globe.com'))
k.key = 'json/hotlist2.json'
_json = json.dumps(out)
k.set_contents_from_string(_json)
k.set_acl('public-read')
print _json
k.set_contents_from_string(_json)
k.set_acl('public-read')
