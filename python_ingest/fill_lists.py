#!/usr/bin/python

from ingest_lib import *
import time

config = getConfig()

t = getTwitter(config)

mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
cur.execute("SET time_zone='+0:00'")

users_per_fill = 30

@mainloop
def do_fill():
    cur.execute("SELECT user_id FROM users WHERE list_id IS NULL AND suspended = 0 LIMIT %s", users_per_fill)
    uids = [row['user_id'] for row in cur]
    if len(uids) == 0:
        print "No new users!"
        time.sleep(60)
    else:
        cur.execute('SELECT list_id, COUNT(*) as num FROM users WHERE list_id IS NOT NULL GROUP BY list_id ORDER BY list_id ASC')
        found_a_list_with_space = False
        target_list = -1
        existing_user_count = 0
        for row in cur:
            target_list = row['list_id']
            if row['num'] < 4999:
                found_a_list_with_space = True
                existing_user_count = row['num']
                break
        if found_a_list_with_space == False:
            target_list += 1
        slug = "a%s" % target_list
        uids = uids[:(4999-existing_user_count)]
        print "Adding %s users to list %s" % (len(uids), slug)
        uid_string = ",".join(map(str,uids))
        t.lists.members.create_all(owner_screen_name=config['twitter']['screen_name'],slug=slug,user_id=uid_string,_timeout=30)
        cur.execute("UPDATE users SET list_id = %s WHERE user_id IN ("+ uid_string +")", target_list) # Slipping uid_string in the bad, injection-prone way. Beware.
        time.sleep(5)

do_fill()
