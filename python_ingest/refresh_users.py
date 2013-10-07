#!/usr/bin/python

from ingest_lib import *
import time

config = getConfig()

t = getTwitter(config)

limited_refresh = RateLimitedAPICall(t.users.lookup,15*60,175)

mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
cur.execute("SET time_zone='+0:00'")


@mainloop
def do_refresh():
    cur.execute("SELECT user_id FROM users ORDER BY last_updated ASC LIMIT 100")
    uids = [row['user_id'] for row in cur]
    uid_string = ",".join(map(str,uids))
    response = limited_refresh(user_id=uid_string,_timeout=30)
    print "refreshing %s users" % len(response)
    info_dict = {x['id']:x for x in response}
    for uid in uids:
        if uid in info_dict:
            ui = info_dict[uid]
            info_tuple = (ui['screen_name'],ui['friends_count'],ui['followers_count'],ui['profile_image_url'],uid)
            cur.execute("UPDATE users SET screen_name = %s, friends_count = %s, followers_count = %s, name = %s, profile_image_url = %s, suspended = 0 WHERE user_id = %s",info_tuple)
        else:
            cur.execute("UPDATE users SET suspended = 1 WHERE user_id = %s",(uid,))

do_refresh()
