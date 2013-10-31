#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import MySQLdb.cursors
import os
import datetime

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
	with open('%s/config/config.json' % CONDOR_HOME) as fh:
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

cutoff = datetime.datetime.utcnow()-datetime.timedelta(days=14)

tables = ['tweeted_urls','tweeted_hashtags','tweeted_mentions','tweets']

copy_query = "INSERT IGNORE INTO condor_archive.archive_%s (SELECT * FROM %s WHERE created_at < %%s)"
delete_query = "DELETE FROM %s WHERE created_at < %%s"

cur.execute("SET time_zone='+0:00'")

for table in tables:
	cur.execute(copy_query%(table,table),(cutoff,))
	conn.commit()
	# cur.execute(delete_query%(table),(cutoff,))
	# conn.commit()