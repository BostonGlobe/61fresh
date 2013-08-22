"""
test file:
"""
from urllib import urlopen
url = "http://www.gutenberg.org/files/100/100.txt"
raw = urlopen(url).read()
print raw[11100:11600]
