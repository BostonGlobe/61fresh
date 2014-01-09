#!/usr/bin/python

from ingest_lib import *
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
from boto.sqs.message import RawMessage
import json
import subprocess
import sys
import traceback

config = getConfig()

conn = SQSConnection(config["aws-s3"]["access-key-id"], config["aws-s3"]["secret-access-key"])

q = conn.create_queue('db-notifications')
q.set_message_class(RawMessage)

while True:
    try:
        messages = q.get_messages(wait_time_seconds=20)
        if len(messages) > 0:
            alert = json.loads(json.loads(messages[0].get_body())['Message'])['Event Message']
            if alert == "DB instance restarted":
                print "Bouncing..."
		subprocess.call(["bash","stop.sh"])
                subprocess.call(["bash","start.sh"])
                subprocess.call(["killall","node"])
	    q.delete_message(messages[0])
    except:
        traceback.print_exc(file=sys.stdout)
