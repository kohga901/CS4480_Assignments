from socket import *
import logging
import urllib
import urllib.parse
import urllib.request
logging.basicConfig(level=logging.DEBUG)

def Check_Validity_Of_Request(request):
    request = request.split()

    # Check if the method of the request is valid.
    method = Check_Method(request[0])
    if (method == 2):
        return 501
    elif (method == 1):
        return 400
    
    # Check if the URL is valid.
    URL = Check_URL(request[1])
    if (URL == False):
        return 400
    
    # Check if the HTTP version is valid.
    version = Check_Version(request[2])
    if (version == False):
        return 400

    # If there are headers, check if the header is valid.


# Returns 0 if method is GET 
# Returns 1 if method is invalid
# Returns 2 if method is unimplemented
def Check_Method(request_message):
    request_methods = {b"GET", b"DELETE", b"PUT", b"PATCH", b"POST"}
    if (request_message[0] == b"GET"): 
        return 0
    if (request_methods.__contains__(request_message[0])):
        return 2
    else:
        return 1

def Check_URL(URL):
    try:
        response = urllib.request.urlopen(URL.decode())
        return True
    except:
        return False
def Check_Version(version):
    decoded = version.decode()
    HTTP_part = decoded[0:7]
    if (HTTP_part == "HTTP/1.0"):
        return True
    else:
        return False

# request_to_string = request_message.decode()
# Check_Validity(request_to_string)
