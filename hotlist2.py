#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import nltk

sys.path.append('./classifier')
from calais import Calais
from nclassifier import Classifier
import codecs
import pickle
import time


parser = optparse.OptionParser()
parser.add_option('-a', '--age', help='max age of urls in hours. default value is 12',default='12')
parser.add_option('-p', '--popularity_weight', help='multiplier for popularity - higher values will give greater emphasis to popular articles over fresh articles. default is 100',default='100')
parser.add_option('-i', '--ignore_age', help='ignore recency & just return a straight popularity rank for the time period, default is false',default=False)
parser.add_option('-n', '--no_tweeters', help="don't return array of tweeters with each url - saves file size. default is False (tweeters will be returned).",default=False)
parser.add_option('-m', '--min', help="minimize file size. includes only title, url, age, source, first_tweeted, hotness",default=False)
parser.add_option('-r', '--num_results', help="number of results to return, default value is 50.",default=50)
parser.add_option('-t', '--hashtag', help="filter by the given hashtag, not domain list, default is false",default=False)
parser.add_option('-o', '--no_s3', help="don't upload to s3",default=False)
parser.add_option('-c', '--no_classify', help="don't run sports classifier",default=False)

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
if not opts.ignore_age:
	if int(opts.age)>72:
		opts.ignore_age=True 
	else:
		opts.ignore_age=False

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
non_hashtag_query = """select real_url as url,count(distinct user_id) as total_tweets, 
MIN(created_at) as first_tweeted, TIMESTAMPDIFF(HOUR,MIN(created_at),NOW()) as age, 
real_url_hash as hash, domain as source, embedly_blob,sports_score from tweeted_urls
left join url_info using(real_url_hash) 
where domain in (select domain from domains where domain_set='boston') 
group by real_url having age < %s;"""

hashtag_query = """
select real_url as url,count(distinct tweeted_urls.user_id) as total_tweets, MIN(tweeted_urls.created_at) as first_tweeted, 
	TIMESTAMPDIFF(HOUR,MIN(tweeted_urls.created_at),NOW()) as age, real_url_hash as hash, domain as source, embedly_blob, sports_score 
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

links = cur.fetchall()

for link in links:
	link['tweeters'] = []
	if not opts.no_tweeters and not opts.min:
		link['weighted_tweets'] = 0
		cur.execute("select screen_name, name, followers_count, profile_image_url, text, tweet_id, tweeted_urls.created_at as created_at, retweeted_tweet_id, home_domain from users join tweeted_urls using(user_id) join tweets using(tweet_id) where real_url_hash = %s group by tweeted_urls.user_id order by followers_count desc",(link['hash']))
		for row in cur:
			if row['home_domain'] != link['source']:
				link['weighted_tweets'] += 1
			del row['home_domain']
			if row['retweeted_tweet_id'] is None:
				del row['retweeted_tweet_id']
#			row['home_domain'] = row['home_domain'] == link['source']
			row['tweet_id'] = str(row['tweet_id'])
			row['created_at'] = row['created_at'].isoformat()
			link['tweeters'].append(row)
	else:
		link['weighted_tweets'] = link['total_tweets']

	link['age']+=1
	age = link['age']
	popularity_factor = float((link['weighted_tweets']-2)*int(opts.popularity_weight))
	age_factor = float(age * age)
	link['popularity_factor'] = popularity_factor
	link['age_factor'] = age_factor
	if opts.ignore_age:
		link['hotness'] = popularity_factor
	else:
		link['hotness'] = popularity_factor / age_factor

links.sort(key=lambda x: x['hotness'],reverse=True)

links = links[:int(opts.num_results)]

all_to_get_from_embedly = [x for x in links if x['embedly_blob'] is None]

while len(all_to_get_from_embedly) > 0:
	to_get_from_embedly = all_to_get_from_embedly[:10]
	all_to_get_from_embedly = all_to_get_from_embedly[10:]
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

if not opts.min and not opts.no_classify:
	calais = Calais("***REMOVED***", submitter="python-calais classify")
	with open('savedclassifier.pickle','rb') as pkfile:
		classifier = pickle.load(pkfile)

for link in links:
	embedly = json.loads(link['embedly_blob'])

	if (not opts.min and not opts.no_classify) and link['sports_score'] is None:
		analysetext = ' '.join([embedly.get(x,'') for x in ['title', 'description', 'url'] if embedly.get(x,'') is not None])
		analysetext.encode("utf8")
		analysetext = analysetext.encode("utf8")
		analysetext= analysetext.replace('"', '\'')

		#core features extracted from classifier runs
		sportslist=['sports','nesn','weei','espn',#super types
			'Baseball','Hockey','Basketball','Football',#sports types
			'Tennis','Soccer','Lacrosse','Softball', 'Soccer','Flat track roller derby',#sports types
			'pitch','quarterback','team','win','loss','lost', 'player', 'champion','league', 'game','score','Competition',' inning', 'record','played',#sports terms
			'Women\'s football','Rugby','Red Sox','RedSox','Sox','red_sox','Bruin','Celtic','Yankees','White Sox',#teams and clubs
			'New England Patriots', 'Patriots', 'Lobsters', 'New England Revolution','Boston Breakers','Boston Cannons',#teams and clubs
			'New England Riptide','Boston Aztec','Boston Massacre','Boston Blazers','Boston Militia','Boston Thirteens',#teams and clubs
			'Jim Baker','Steve Buckley','Gerry Callahan','Michael Gee','Karen Guregian','George Edward Kimball','George E. Kimball',#Oped writers
			'Kevin Mannix','Tony Massarotti', 'Amalie Benjamin','Gordon Edes','Chris Gasper','Jackie MacMullan','Bob Ryan','Dan Shaughnessy',#Oped writers
			'Fluto Shinzawa','Marc J. Spears','Steve Addazio',#Oped writers
			'Gillette Stadium','Foxborough','Fenway','TD Garden','Ferncroft Country Club','Dilboy Stadium','Harvard Stadium','Martin Softball Field',
			'Amesbury Sports Park','Aleppo Shrine Auditorium',#venues
			'ACC football','MLB','NHL','/NFL/',' NFL ','WTT','MLS','NWSL','MLL','NPF','WPSL','WFTDA','NLL','WFA','AMNRL',#Leagues and Conferences
			'World Series','AL Pennant','Stanley Cup','NBA','Super Bowl','AFC','US Open','U.S. Open','Superliga','Steinfeld','Cowles','WPSL','Championship','Premiership'#championship
			'Red Auerbach', 'Dana Barros', 'Bob Bigelow', 'Larry Bird', 'Walter Brown', 'Bob Cousy', 'Dave Cowens',
			'Bill Curley', 'Kevin Garnett', 'John Havlicek', 'Tom Heinsohn', 'Ron Lee', 'Reggie Lewis', 'Kevin McHale', 'Don Nelson',#sports people boston
			'Shaquille O\'Neal', 'Robert Parish', 'Paul Pierce', 'Doc Rivers', 'Rajon Rondo', 'Bill Russell', 'Josh Beckett',
			'Wade Boggs', 'Roger Clemens', 'Joe Cronin', 'Bobby Doerr', 'Jacoby Ellsbury', 'Carlton Fisk', 'Nomar Garciaparra',
			'Mike Lowell', 'Jim Rice', 'Pedro Martinez', 'Tommy McCarthy', 'Lou Merloni', 'David Ortiz', 'Dustin Pedroia',
			'Johnny Pesky', 'Manny Ramírez', 'Curt Schilling', 'Jason Varitek', 'Tim Wakefield', 'George Wood', 'Ted Williams',
			'Carl Yastrzemski', 'Cy Young', 'Bruce Armstrong', 'Tom Brady', 'Bill Belichick', 'Drew Bledsoe', 'Troy Brown',
			'Tedy Bruschi', 'Doug Flutie', 'Rob Gronkowski', 'John Hannah', 'Robert Kraft', 'Randy Moss', 'Jim Plunkett',
			'Matt Ryan', 'Richard Seymour', 'Andre Tippett', 'Adam Vinatieri', 'Wes Welker', 'Tony Amonte', 'Patrice Bergeron',
			'Ray Bourque', 'Frank Brimsek', 'Zdeno Chara', 'Don Cherry', 'Rick DiPietro', 'Phil Esposito', 'Jim Fahey', 'Hal Gill',
			'Cam Neely', 'Terry O\'Reilly', 'Bobby Orr', 'Milt Schmidt', 'Eddie Shore', 'Jeremy Roenick', 'Brad Park', 'Mark Recchi', 'Tim Thomas',
			'Tim Tebow','Michael Phelps','Usain Bolt','Derek Jeter','Peyton Manning','Drew Brees','Gabby Douglas','Aaron Rodgers','LeBron James','David Beckham'#sports people forbes usa all
			]
	
	
		#feature counter >= 2 works
		feature_counter = 0
		for entry in sportslist:
			if analysetext.lower().find(entry.lower()) >= 0:
				feature_counter += 1

		#classifier 1
		#naive bayes
		_topic = classifier.classify(analysetext)
		_score = classifier.get_score(analysetext)

		#classifier 2
		#opencalais crosscheck   
		try:
			result = calais.analyze(analysetext)
			topic =  result.get_topics()
			score =  result.get_topic_score()
		except:
			topic = "None"
			score = 0.0

		classifier_json = json.dumps({'topic':topic,'score':score,'_topic':_topic,'_score':_score})
		if topic == "Sports" and feature_counter < 2:
			sports_score = str(score)
		elif topic == "None" and _topic == "sports" and feature_counter < 2:
			sports_score = str(_score)
		elif feature_counter >= 2:
			sports_score = '1.0'
		else:
			sports_score = '0.0'
		link['sports_score'] = sports_score
		cur.execute("update url_info set topic_blob=%s, sports_score=%s where real_url_hash=%s",(classifier_json,sports_score,link['hash']))
		conn.commit()

#	if not opts.min: 
#		link['keywords'] = {kw['name']:kw['score'] for kw in embedly['keywords']}
	del link['embedly_blob']
	link['first_tweeted'] = link['first_tweeted'].isoformat()
	link['title'] = embedly['title']
	if not opts.min: link['description'] = embedly['description']
	if not opts.min:
		for img in embedly['images']:
			if img['width'] > 300:
				link['image_url'] = img['url']
				break
	del link['hash']

#if not opts.min: correlation_matrix = [[getLinksCorrelation(x,y) for x in links] for y in links]
#else: correlation_matrix = []
correlation_matrix = []
out = {	'generated_at': datetime.datetime.utcnow().isoformat(),
		'age_in_hours':opts.age,
		'popularity_weight':opts.popularity_weight,
		'diagnostics':True,
		'correlation': correlation_matrix,
		'ignore_age':opts.ignore_age,
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
