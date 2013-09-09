#!/usr/bin/python

import json
import MySQLdb
import MySQLdb.cursors

if not CONDOR_ENV:
	print "you must set the CONDOR_ENV bash variable (production, test, etc)"
if not CONDOR_HOME:
	condor_home="~/condor"

try:
	with open("%s/config/config-%s.json" % (CONDOR_HOME,CONDOR_ENV)) as fh:
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

query = """select users.user_id,users.screen_name screen_name,count(*) cnt
from users,tweeted_urls,domains 
where tweeted_urls.domain=domains.domain
and tweeted_urls.user_id=users.user_id
and domains.domain_set='boston'
and tweeted_urls.created_at>adddate(now(),interval -7 day)
group by users.user_id
order by cnt desc limit 1000;
"""
cur.execute(query)

users = {}
# for each user, get top domains.
for row in cur:
	query2= """select users.user_id user_id,users.screen_name screen_name, domain,count(*) num from tweeted_urls,users
	where tweeted_urls.user_id = users.user_id
	and users.screen_name='%s'
	group by domain order by num asc;
	""" % row['screen_name']
	cur2=conn.cursor()
	cur2.execute(query2)
	for row in cur2:
		print "%s\t%s\t%s" % (row['screen_name'],row['num'], row['domain'])
		if row['user_id'] not in users:
			users[row['user_id']] = {'total': 0}
		users[row['user_id']]['screen_name'] = row['screen_name']
		users[row['user_id']]['domain'] = row['domain']
		users[row['user_id']]['domain_count'] = row['num']
		users[row['user_id']]['total'] += row['num']
	print ""

print "----"
print "----"
print "----"
print "----"

for uid in users:
	u = users[uid]
	print "%s \t %s \t %s \t %s" % (u['screen_name'],u['total'],u['domain_count'],u['domain'])
	if (u['total'] > 20) and (float(u['domain_count'])/float(u['total'])) >= 0.5:
		if u['domain'] not in ['twitter.com','instagram.com']:
			print "hit"
			cur.execute("update users set home_domain = %s where user_id = %s", (u['domain'],uid))
conn.commit()
