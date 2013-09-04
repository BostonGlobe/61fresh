#!/usr/bin/python

import json
import MySQLdb
import MySQLdb.cursors

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

cur.execute("select user_id, domain, count(*) as num from tweeted_urls where domain is not null group by user_id, domain order by num asc")

users = {}

for row in cur:
	if row['user_id'] not in users:
		users[row['user_id']] = {'total': 0}
	users[row['user_id']]['domain'] = row['domain']
	users[row['user_id']]['domain_count'] = row['num']
	users[row['user_id']]['total'] += row['num']

for uid in users:
	u = users[uid]
	if (u['total'] > 20) and u['domain'] not in ['twitter.com','instagram.com','facebook.com','youtube.com','vine.co']:
		pct = 100*u['domain_count']/u['total']
		cur.execute("update users set home_domain = %s, home_domain_percent = %s where user_id = %s", (u['domain'], pct, uid))
conn.commit()
