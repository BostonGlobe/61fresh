#!/usr/bin/python

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import datetime
import json
import MySQLdb


conn = MySQLdb.connect(
	host='***REMOVED***',
 	user='condor',
 	passwd='condor',
 	db ='condor',
	use_unicode=True,
    charset="utf8")
cur = conn.cursor()

cur.execute("SET time_zone='+0:00'")

recent_query = 'select real_url, count(distinct user_id) as num from tweeted_urls where created_at > DATE_SUB(NOW(), INTERVAL 4 HOUR) and domain in ("somerville.patch.com","boston.schmap.com","metrowestdailynews.com","metro.us","dotnews.com","mbta.com","boston.eater.com","commonhealth.wbur.org","patriotledger.com","boston.redsox.mlb.com","news.harvard.edu","bostonrestaurants.blogspot.com","boston.craigslist.org","artery.wbur.org","patriots.com","bpdnews.com","bu.edu","digboston.com","universalhub.com","web.mit.edu","wgbhnews.org","wbur.org","necn.com","boston.cbslocal.com","nesn.com","bostonherald.com","bostonmagazine.com","bostinno.streetwise.co","bostonglobe.com","boston.com","radioboston.wbur.org","weather.boston.cbslocal.com","somervillebeat.com","live.boston.com","thecrimson.com","thesomervillenews.com","gazettenet.com","backbay.patch.com","barstoolsports.com","scoutsomerville.com","jewishboston.com","wgbh.org","somervillema.gov","commonwealthmagazine.org","publicartboston.com","bostonpads.backbaypads.com","epaper.bostonglobe.com","boston.sportsthenandnow.com","cambridgema.gov","stats.boston.cbslocal.com","allstonpudding.com","martywalsh.org","thebostoncalendar.com","vanyaland.com","weei.com","providencejournal.com") group by real_url'
background_query = 'select real_url, count(distinct user_id) as num from tweeted_urls where created_at > DATE_SUB(NOW(), INTERVAL 7 DAY) and domain in ("somerville.patch.com","boston.schmap.com","metrowestdailynews.com","metro.us","dotnews.com","mbta.com","boston.eater.com","commonhealth.wbur.org","patriotledger.com","boston.redsox.mlb.com","news.harvard.edu","bostonrestaurants.blogspot.com","boston.craigslist.org","artery.wbur.org","patriots.com","bpdnews.com","bu.edu","digboston.com","universalhub.com","web.mit.edu","wgbhnews.org","wbur.org","necn.com","boston.cbslocal.com","nesn.com","bostonherald.com","bostonmagazine.com","bostinno.streetwise.co","bostonglobe.com","boston.com","radioboston.wbur.org","weather.boston.cbslocal.com","somervillebeat.com","live.boston.com","thecrimson.com","thesomervillenews.com","gazettenet.com","backbay.patch.com","barstoolsports.com","scoutsomerville.com","jewishboston.com","wgbh.org","somervillema.gov","commonwealthmagazine.org","publicartboston.com","bostonpads.backbaypads.com","epaper.bostonglobe.com","boston.sportsthenandnow.com","cambridgema.gov","stats.boston.cbslocal.com","allstonpudding.com","martywalsh.org","thebostoncalendar.com","vanyaland.com","weei.com","providencejournal.com") group by real_url'

background_popularity = {}

cur.execute(background_query)
for row in cur:
	background_popularity[row[0]] = float(row[1])


links = []

cur.execute(recent_query)
for row in cur:
	# out.append({'url':row[0], 'hotness': row[1]-background_popularity[row[0]]})
	links.append({'url':row[0], 'hotness': (row[1]*row[1])/background_popularity[row[0]]})

links.sort(key=lambda x: x['hotness'],reverse=True)

out = {	'generated_at': datetime.datetime.utcnow().isoformat(),
		'links':links[:10]}


s3_conn = S3Connection('***REMOVED***', '***REMOVED***')
k = Key(s3_conn.get_bucket('condor.globe.com'))
k.key = 'json/daniel.json'
k.set_contents_from_string(json.dumps(out,indent=1))
k.set_acl('public-read')