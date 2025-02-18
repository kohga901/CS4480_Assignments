import urllib.parse
from urllib.request import *
from urllib.parse import *
from urllib.error import *
import urllib
import urllib.request
import json
from socket import *
import re
from threading import Thread
from datetime import datetime
from time import gmtime, strftime
import time

state = False

def function():
    if (state):
        print(True)
    else:
        print(False)

date = "Sun, 10 May 2020 02:01:00 GMT"

def Get_IFMS_Header(response):
    header = "If-Modified-Since:"
    index = response.find(header)
    print(index)
    string = response[index : index + 48]
    return string

def Store_In_Cache(first_line, response_from_origin):
    # Parse the response from the origin.
    parsed = response_from_origin.split("\r\n\r\n")
    parsed = parsed[0]
    parsed += "\r\n"
    # Get the date.
    time_formatted = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    # Add the date of when the object is stored in the cache.
    parsed += f"Last-Modified: {time_formatted} \r\n\r\n"
    # cache[first_line] = parsed
    return parsed
blocklist = []
# message = 'HTTP/1.1 200 OK\r\nDate: Sun, 26 Sep 2010 20:09:20 GMT\r\nServer: Apache/2.0.52 (CentOS)\r\nIf-Modified-Since: Tue, 30 Oct 2007 17:00:02 GMT\r\nETag: "17dc6-a5c-bf716880"\r\nAccept-Ranges: bytes\r\nContent-Length: 2652\r\nKeep-Alive: timeout=10, max=100\r\nConnection: Keep-Alive\r\nContent-Type: text/html; charset=ISO-8859-1\r\n\r\n'
# response = Store_In_Cache("", message)

blocklist.append('flux')

def Is_URL_Blocked(host):
    for blocked_domain in blocklist:
        if (host in blocked_domain):
            return True
    return False
state = Is_URL_Blocked("flux")
print(state)
