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
import os

parser = optparse.OptionParser()
parser.add_option('-a', '--age', help='max age of urls in day. default value is 7',default='7')
parser.add_option('-r', '--num_results', help="number of results to return, default value is 25.",default=25)

(opts, args) = parser.parse_args()


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
query = """select tweeted_urls.domain,count(distinct tweeted_urls.user_id) num_users
from tweeted_urls,domains,users
where created_at>adddate(now(),interval -%s day)
and domain_set='boston'
and tweeted_urls.user_id=users.user_id
and domains.domain=tweeted_urls.domain
group by tweeted_urls.domain
order by num_users desc limit %s;""" % (opts.age,opts.num_results)

cur.execute(query)

links = []
for row in cur:
	links.append(row)


out = {	'generated_at': datetime.datetime.utcnow().isoformat() + "Z",
		'age_in_days':opts.age,
		'domains':links}

_json = json.dumps(out)
print _json
#s3_conn = S3Connection('***REMOVED***', '***REMOVED***')
#k = Key(s3_conn.get_bucket('condor.globe.com'))
#k.key = 'json/leaders/top_domains.json'

#k.set_contents_from_string(_json)
#k.set_acl('public-read')
#k.set_contents_from_string(_json)
#k.set_acl('public-read')
