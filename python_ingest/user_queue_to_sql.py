#!/usr/bin/python

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
import json
from ingest_lib import *

config = getConfig()

sqs_conn = SQSConnection(config["aws-s3"]["access-key-id"], config["aws-s3"]["secret-access-key"])
q = sqs_conn.create_queue('condor-users')

mysql_conn = getMySQL(config)
cur = mysql_conn.cursor()
cur.execute("SET time_zone='+0:00'")

cur.execute("SELECT user_id FROM users")
existing_users = set([x['user_id'] for x in cur])

@mainloop
def go():
    m = q.read(wait_time_seconds=20)
    if m is not None:
        users = json.loads(m.get_body())
        rec_size = len(users)
        users = [x for x in users if x not in existing_users]
        print "inserting %s new users out of %s" % (rec_size,len(users))
        if len(users) > 0:
            cur.executemany("INSERT IGNORE INTO users (user_id) VALUES (%s)",[(x,) for x in users])
            mysql_conn.commit()
            existing_users.update(users)
        q.delete_message(m)

go()
    
