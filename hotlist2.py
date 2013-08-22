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
import optparse

parser = optparse.OptionParser()
parser.add_option('-a', '--age', help='max age of urls in hours. default value is 12',default='12')
parser.add_option('-p', '--popularity_weight', help='multiplier for popularity - higher values will give greater emphasis to popular articles over fresh articles. default is 100',default='100')
parser.add_option('-n', '--no_tweeters', help="don't return array of tweeters with each url - saves file size. default is False (tweeters will be returned).",default=False)
parser.add_option('-m', '--min', help="minimize file size. includes only title, url, age, source, first_tweeted, hotness",default=False)
parser.add_option('-r', '--num_results', help="number of results to return, default value is 50.",default=50)
parser.add_option('-t', '--hashtag', help="filter by the given hashtag, not domain list, default is false",default=False)
parser.add_option('-o', '--no_s3', help="don't upload to s3",default=False)

(opts, args) = parser.parse_args()

#print "age: %s" % opts.age
#print "popularity_weight: %s" % opts.popularity_weight
#print "no_tweeters: %s" % opts.no_tweeters

#exit(0)
#if len(sys.argv)>1:
#	age_in_hours = int(sys.argv[1])
#else:
#	age_in_hours = 12

#popularity_weight=100

# for multi-day queries, don't consider recency, just a popularity rank
if opts.age>72:
	ignore_age=True 
else:
	ignore_age=False

try:
	with open('config-local.json') as fh:
		config = json.load(fh)
except IOError:
	with open('config.json') as fh:
		config = json.load(fh)

conn = MySQLdb.connect(
	host=config['mysql']['host'],
	port=config['mysql']['port'],
 	user=config['mysql']['user'],
 	passwd=config['mysql']['password'],
 	db=config['mysql']['database'],
	use_unicode=True,
    charset="utf8",
    cursorclass = MySQLdb.cursors.DictCursor)
cur = conn.cursor()

cur.execute("SET time_zone='+0:00'")
non_hashtag_query = """select real_url as url, count(distinct user_id) as total_tweets, 
MIN(created_at) as first_tweeted, TIMESTAMPDIFF(HOUR,MIN(created_at),NOW()) as age, 
real_url_hash as hash, domain as source, embedly_blob,sports_score from tweeted_urls 
left join url_info using(real_url_hash) 
where domain in (select domain from domains where domain_set='boston') 
group by real_url having age < %s;"""

hashtag_query = """
select real_url as url,count(distinct tweeted_urls.user_id) as total_tweets, MIN(tweeted_urls.created_at) as first_tweeted, 
	TIMESTAMPDIFF(HOUR,MIN(tweeted_urls.created_at),NOW()) as age, real_url_hash as hash, domain as source, embedly_blob 
from tweeted_urls left join url_info using(real_url_hash) 
	left join tweeted_hashtags using (tweet_id) 
where hashtag='%s'  
	and real_url is not null 
	and real_url <> 'error'
	and tweeted_urls.created_at>adddate(now(),interval -24 hour)
group by real_url 
having age < 24
order by total_tweets desc;
"""
query = ""
if (opts.hashtag):
	query = hashtag_query % opts.hashtag
else:
	query = non_hashtag_query % opts.age

links = []

cur.execute(query)

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
	popularity_factor = float((row['total_tweets']-2)*int(opts.popularity_weight))
	age_factor = float(age * age)
	row['popularity_factor'] = popularity_factor
	row['age_factor'] = age_factor
	if ignore_age:
		row['hotness'] = popularity_factor
	else:
		row['hotness'] = popularity_factor / age_factor
		
	links.append(row)

links.sort(key=lambda x: x['hotness'],reverse=True)

links = links[:int(opts.num_results)]

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

def getLinksCorrelation(a,b):
	return sum([a['keywords'].get(x,0)*b['keywords'].get(x,0) for x in a['keywords'].keys()])

for link in links:
	embedly = json.loads(link['embedly_blob'])
	if not opts.min: link['keywords'] = {kw['name']:kw['score'] for kw in embedly['keywords']}
	del link['embedly_blob']
	link['first_tweeted'] = link['first_tweeted'].isoformat()
	link['title'] = embedly['title']
	if not opts.min: link['description'] = embedly['description']
	if not opts.min:
		for img in embedly['images']:
			if img['width'] > 300:
				link['image_url'] = img['url']
				break
	link['tweeters'] = []
	if not opts.no_tweeters and not opts.min:
		cur.execute("select screen_name, name, followers_count, profile_image_url, text, tweet_id, tweeted_urls.created_at as created_at from users join tweeted_urls using(user_id) join tweets using(tweet_id) where real_url_hash = %s group by tweeted_urls.user_id order by followers_count desc",(link['hash']))
		for row in cur:
			row['tweet_id'] = str(row['tweet_id'])
			row['created_at'] = row['created_at'].isoformat()
			link['tweeters'].append(row)
	del link['hash']

if not opts.min: correlation_matrix = [[getLinksCorrelation(x,y) for x in links] for y in links]
else: correlation_matrix = []

out = {	'generated_at': datetime.datetime.utcnow().isoformat(),
		'age_in_hours':opts.age,
		'popularity_weight':opts.popularity_weight,
		'diagnostics':True,
		'correlation': correlation_matrix,
		'articles':links[:int(opts.num_results)]}
# print json.dumps(out,indent=1)

_json = json.dumps(out)
print _json
if not opts.no_s3:
	s3_conn = S3Connection('***REMOVED***', '***REMOVED***')
	k = Key(s3_conn.get_bucket('condor.globe.com'))
	if opts.hashtag:
		k.key = 'json/hashtags/'+opts.hashtag+'.json'
	else:
		k.key = "json/articles_%s.json" % opts.age

	k.set_contents_from_string(_json)
	k.set_acl('public-read')
	k.set_contents_from_string(_json)
	k.set_acl('public-read')
