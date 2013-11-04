#!/usr/bin/python
# -*- coding: utf-8 -*-

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from bs4 import BeautifulSoup
import datetime
import json
import MySQLdb
import MySQLdb.cursors
from urllib import quote
import urllib2
import sys
import optparse
import nltk
import gensim
import re
import os

CONDOR_ENV = os.environ['CONDOR_ENV']
CONDOR_HOME = env = os.environ['CONDOR_HOME']

if not CONDOR_ENV:
	print "you must set the CONDOR_ENV bash variable (production, test, etc)"
if not CONDOR_HOME:
	condor_home="~/condor"

try:
	with open("%s/config/config-%s.json" % (CONDOR_HOME,CONDOR_ENV)) as fh:
		config = json.load(fh)
except IOError:
	with open('config/config.json') as fh:
		config = json.load(fh)

sys.path.append('./classifier')
from calais import Calais
from nclassifier import Classifier
import codecs
import pickle
import time

parser = optparse.OptionParser()
parser.add_option('-a', '--age', help='max age of urls in hours. default value is 12',default='12')
parser.add_option('-d', '--days_ago', help='Set this to look at 61fresh as it would have appeared x days ago. Default is zero.',default='0')
parser.add_option('-p', '--popularity_weight', help='multiplier for popularity - higher values will give greater emphasis to popular articles over fresh articles. default is 100',default='100')
parser.add_option('-i', '--ignore_age', help='ignore recency & just return a straight popularity rank for the time period, default is false',default=False)
parser.add_option('-n', '--no_tweeters', help="don't return array of tweeters with each url - saves file size. default is False (tweeters will be returned).",default=False)
parser.add_option('-m', '--min', help="minimize file size. includes only title, url, age, source, first_tweeted, hotness",default=False)
parser.add_option('-r', '--num_results', help="number of results to return, default value is 50.",default=50)
parser.add_option('-t', '--hashtag', help="filter by the given hashtag, not domain list, default is false",default=False)
parser.add_option('-o', '--no_s3', help="don't upload to s3",default=False)
parser.add_option('-c', '--no_classify', help="don't run sports classifier",default=False)
parser.add_option('-g', '--group_clusters', help="return clusters: groups of atricles about the same topic",default=False)
parser.add_option('-s', '--domain_group', help="domain set to use, default is boston",default='boston')
parser.add_option('-x', '--domain', help="filter results by domain")
parser.add_option('-v', '--subsets', help="domain subsets to use, default is blank",default='')
	
(opts, args) = parser.parse_args()

#print "domain is %s" % opts.domain

# for multi-day queries, don't consider recency, just a popularity rank
if not opts.ignore_age:
	if int(opts.age)>72:
		opts.ignore_age=True 
	else:
		opts.ignore_age=False

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

# generate subset filter sql if needed
subsets_sql=''
_subsets = opts.subsets.split(',')
for i in range(len(_subsets)):
	if (i!=0): 
		subsets_sql+=","
	subsets_sql+="'%s'" % _subsets[i]
if (len(opts.subsets))>0:
	subsets_sql = "and subset in (%s)" % subsets_sql

domain_sql = ''
if opts.domain:
	domain_sql =" and domain='%s'" % opts.domain
	

cur.execute("SET time_zone='+0:00'")
non_hashtag_query = """select real_url as url,count(distinct user_id) as total_tweets, 
MIN(created_at) as first_tweeted, TIMESTAMPDIFF(HOUR,MIN(created_at),DATE_SUB(NOW(),INTERVAL %s DAY)) as age, 
real_url_hash as hash, domain as source, embedly_blob,sports_score from tweeted_urls
left join url_info using(real_url_hash) 
where domain in (select domain from domains where domain_set=%s SUBSETS_SQL DOMAIN_SQL) 
and created_at < DATE_SUB(NOW(),INTERVAL %s DAY)
group by real_url having age < %s;"""

non_hashtag_query = non_hashtag_query.replace("SUBSETS_SQL",subsets_sql)
non_hashtag_query = non_hashtag_query.replace("DOMAIN_SQL",domain_sql)

hashtag_query = """
select real_url as url,count(distinct tweeted_urls.user_id) as total_tweets, MIN(tweeted_urls.created_at) as first_tweeted, 
	TIMESTAMPDIFF(HOUR,MIN(tweeted_urls.created_at),DATE_SUB(NOW(),INTERVAL %s DAY)) as age, real_url_hash as hash, domain as source, embedly_blob, sports_score 
from tweeted_urls left join url_info using(real_url_hash) 
	left join tweeted_hashtags using (tweet_id) 
where hashtag=%s  
	and real_url is not null 
	and real_url <> 'error'
	and tweeted_urls.created_at > DATE_SUB(NOW(),INTERVAL (%s+2) DAY)
	and tweeted_urls.created_at < DATE_SUB(NOW(),INTERVAL %s DAY)
group by real_url 
having age < 24
order by total_tweets desc;
"""
query = ""
if (opts.hashtag):
	cur.execute(hashtag_query,(opts.days_ago,opts.hashtag,opts.days_ago,opts.days_ago))
else:
	cur.execute(non_hashtag_query,(opts.days_ago,opts.domain_group,opts.days_ago,opts.age))

links = []

def hotnessKernel(tweets,age):
	popularity_factor = float((tweets-2)*int(opts.popularity_weight))
	age_factor = float(age * age)
	if opts.ignore_age:
		hotness = popularity_factor
	else:
		hotness = popularity_factor / age_factor
	return {'hotness':hotness,'age_factor':age_factor,'popularity_factor':popularity_factor}


def calculateHotness(link):
	link.update(hotnessKernel(link['weighted_tweets'],link['age']))

def clusterHotness(cluster):
	age = max([link['age'] for link in cluster])
	tweets = sum([link['weighted_tweets'] for link in cluster])
	return hotnessKernel(tweets,age)['hotness']

links = list(cur.fetchall())

links = [x for x in links if "bostinno.streetwise.co/channels/" not in x['url']]

for link in links:
	link['tweeters'] = []
	if not opts.no_tweeters and not opts.min:
		link['weighted_tweets'] = 0
		cur.execute("select screen_name, name, followers_count, profile_image_url, text, tweet_id, tweeted_urls.created_at as created_at, retweeted_tweet_id, home_domain, home_domain_percent from users join tweeted_urls using(user_id) join tweets using(tweet_id) where real_url_hash = %s group by tweeted_urls.user_id order by followers_count desc",(link['hash']))
		for row in cur:
			#if row['home_domain'] == link['source']:
			if row['home_domain_percent']:
				home_domain_factor = row['home_domain_percent']*3
				if home_domain_factor>100:
					home_domain_factor=100
				tweet_weight = 1-home_domain_factor/100.0
				row['tweet_weight']=tweet_weight
				link['weighted_tweets'] += tweet_weight
			else:
				link['weighted_tweets'] += 1
				row['tweet_weight']=1
			if row['retweeted_tweet_id'] is None:
				del row['retweeted_tweet_id']
#			row['home_domain'] = row['home_domain'] == link['source']
			row['tweet_id'] = str(row['tweet_id'])
			row['created_at'] = row['created_at'].isoformat() + "Z"
			link['tweeters'].append(row)
	else:
		link['weighted_tweets'] = link['total_tweets']
	link['age']+=1
	calculateHotness(link)


links.sort(key=lambda x: x['hotness'],reverse=True)

links = links[:int(opts.num_results)]

all_to_get_from_embedly = [x for x in links if x['embedly_blob'] is None]

while len(all_to_get_from_embedly) > 0:
	to_get_from_embedly = all_to_get_from_embedly[:10]
	all_to_get_from_embedly = all_to_get_from_embedly[10:]
	try:
		embedly_list = json.load(urllib2.urlopen("http://api.embed.ly/1/extract?key=***REMOVED***&urls=" + ','.join([quote(x['url']) for x in to_get_from_embedly])))
		for (link,embedly) in zip(to_get_from_embedly,embedly_list):
			if link['source'] == "bostonherald.com" and embedly['description'] is None: # Never let it be said that we are not gracious to our competitors and their goofy markup
				try:
					soup = BeautifulSoup(urllib2.urlopen(embedly['url']))
					for foo in soup.find_all("div",class_="field-item"):
						ps = foo.find_all("p")
						if len(ps) > 0:
							embedly['description'] = ps[0].string
							break
				except:
					pass

			embedly_blob = json.dumps(embedly)
			cur.execute("insert into url_info (real_url_hash,embedly_blob) values (%s,%s) on duplicate key update embedly_blob = %s",(link['hash'],embedly_blob,embedly_blob))
			for target in links:
				if target['hash'] == link['hash']:
					target['embedly_blob'] = embedly_blob
					break
		conn.commit()
	except:
		dead_hashes = [x['hash'] for x in to_get_from_embedly]
		links = [x for x in links if x['hash'] not in dead_hashes]


links_hash = {}
for link in links:
	embedly = json.loads(link['embedly_blob'])
	real_url = embedly['url']
	link['url'] = real_url
	if real_url in links_hash:
		links_hash[real_url]['age'] = max(links_hash[real_url]['age'],link['age'])
		links_hash[real_url]['first_tweeted'] = min(links_hash[real_url]['first_tweeted'],link['first_tweeted'])
		links_hash[real_url]['total_tweets'] = links_hash[real_url]['total_tweets']+link['total_tweets']
		links_hash[real_url]['weighted_tweets'] = links_hash[real_url]['weighted_tweets']+link['weighted_tweets']
		calculateHotness(links_hash[real_url])
		links_hash[real_url]['tweeters'].extend(link['tweeters'])
		links_hash[real_url]['tweeters'].sort(key=lambda x: x['followers_count'],reverse=True)
	else:
		links_hash[real_url] = link

links = links_hash.values()

links.sort(key=lambda x: x['hotness'],reverse=True)


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

	del link['embedly_blob']
	link['first_tweeted'] = link['first_tweeted'].isoformat() + "Z"
	if embedly['title'] is not None:
		link['title'] = embedly['title']
	else:
		link['title'] = link['source']
	if not opts.min: link['description'] = embedly['description']
	if not opts.min:
		for img in embedly['images']:
			if img['width'] > 300:
				link['image_url'] = img['url']
				break
	del link['hash']

out = {	'generated_at': datetime.datetime.utcnow().isoformat() + "Z",
		'age_in_hours':opts.age,
		'popularity_weight':opts.popularity_weight,
		'diagnostics':True,
		'ignore_age':opts.ignore_age,
		'articles':links[:int(opts.num_results)]}

if (not opts.min and opts.group_clusters):
	docs = [' '.join([x for x in [link.get('title',None), link.get('description',None)] if x is not None]) for link in links]

	with open('stoplist.json') as fh:
		stoplist = json.load(fh)

	texts = [[word for word in re.split('\W+',document.lower()) if word not in stoplist and len(word) > 1] for document in docs]

	all_tokens = sum(texts, [])
	tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
	texts = [[word for word in text if word not in tokens_once] for text in texts]

	dictionary = gensim.corpora.Dictionary(texts)
	lsi = gensim.models.LsiModel(corpus=[dictionary.doc2bow(text) for text in texts], id2word=dictionary, num_topics=50)

	index = gensim.similarities.MatrixSimilarity(lsi[[dictionary.doc2bow(text) for text in texts]])

	ids = set(range(len(texts)))
	clusters = []
	while len(ids) > 0:
	    text_id = min(ids)
	    text = texts[text_id]
	    cluster_ids = [x[0] for x in enumerate(index[lsi[dictionary.doc2bow(text)]]) if x[1]>0.4 or x[0]==text_id]
	    cluster_links = [links[x] for x in cluster_ids if x in ids]
	    cluster_links.sort(key=lambda x: x['hotness'],reverse=True)
	    if len(cluster_links)> 0:
	    	clusters.append(cluster_links)
	    ids.difference_update(cluster_ids)

	clusters.sort(key=clusterHotness,reverse=True)

	out['clusters'] = clusters[:int(opts.num_results)]
	del out['articles']

_json = json.dumps(out)
print _json
