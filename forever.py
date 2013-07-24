#!/usr/bin/python

import os
import time

while True:
	print "starting..."
	os.system("node run.js")
	print "looks like we crashed. sleeping for ten minutes."
	time.sleep(600)