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
import re

directory = sys.argv[1]
out = {}
import os, os.path

def upload_to_s3(folder,s): 
	s3_conn = S3Connection('***REMOVED***', '***REMOVED***')
	k = Key(s3_conn.get_bucket('condor.globe.com'))
	k.key = 'json/'+folder+'.json'
#	print "key %s" % k.key
	k.set_contents_from_string(s)
	k.set_acl('public-read')



for root, _, files in os.walk(directory):
	for f in files:
		fullpath = os.path.join(root, f)
		elems = re.split('\W+',fullpath)
		f = open(fullpath, 'r')
		text = f.read()
		if len(elems)==3:
			# ex: json_stage/articles.json
			out[elems[1]]=json.loads(text)
			upload_to_s3('json/'+elems[1]+'.json',text)
			
		if len(elems)==4:
			# ex: json_stage/hashtags/articles.json
			if elems[1] not in out:
				out[elems[1]]=[]
			upload_to_s3('json/'+elems[1]+'/'+elems[2]+'.json',text)
			_json = json.loads(text)
			out[elems[1]].append({'name':elems[2],'data':_json})

json_out = json.dumps(out,indent=1)

upload_to_s3('json/'+directory+'.json',json_out)
print json_out

