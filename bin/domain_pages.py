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
from commands import *


parser = optparse.OptionParser()
parser.add_option('-a', '--age', help='max age of urls in day. default value is 1',default='1')
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

# loop through domains (top n?)
# for each domain, generate 2 pages with top articles in last 12 hours / 7 days
#		-html
# 	-json
print "start"
cur.execute("SET time_zone='+0:00'")
query = """select tweeted_urls.domain,count(distinct tweeted_urls.user_id) num_users
from tweeted_urls,domains,users
where created_at>adddate(now(),interval -%s day)
and domain_set='boston'
and tweeted_urls.user_id=users.user_id
and domains.domain=tweeted_urls.domain
group by tweeted_urls.domain
order by num_users desc limit %s;""" % (opts.age,opts.num_results)

print query

cur.execute(query)


basedir = "%s/www/json/domains" % CONDOR_HOME
try:
	os.mkdir(basedir)
except:
	print ""

for row in cur:
	domain = row['domain']
	print "processing %s" % domain
	cmd ="python27 %s/hotlist2.py --no_classify=1 --domain=%s --num_results=25 --age=24 --ignore_age=1>%s/%s.json" % (CONDOR_HOME,domain,basedir,domain)
#	print cmd
	status, text = getstatusoutput(cmd)
#	print text

