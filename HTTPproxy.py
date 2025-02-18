# Place imports here
import signal
from optparse import OptionParser
import sys
from socket import *
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime
import time

logging.basicConfig(level=logging.DEBUG)

# The cache that stores the objects in the proxy.
# The cache uses a dictionary to store information.
# The key is the first line of a request message. (e.g. GET URL Version).
# The value is the object with a If-Modified-Since header.
cache = {}
cache_status = False
blocklist = []
blocklist_status = False

# Signal handler for pressing ctrl-c
def ctrl_c_pressed(signal, frame):
    sys.exit(0)

# Checks the method part of the request.
# Returns an error code.
def Check_Method(method):
    request_methods = {"GET", "DELETE", "PUT", "PATCH", "POST", "HEAD"}
    if method == "GET":
        return None, "GET"
    if request_methods.__contains__(method):
        logging.debug(f"Error in validating method: {method}")
        return "HTTP/1.0 501 Not Implemented", method
    else:
        logging.debug(f"Error in validating method: {method}")
        return "HTTP/1.0 400 Bad Request", method

# Checks the URL of the request.
# Param: <URL> is the entire URL part of the request.
# example: http://www.flux.utah.edu/somepath
def Check_URL(URL):
    host, port, path = None, None, ""

    # First check scheme
    if (URL[0:7] == "http://"):
        split_URL = URL.split("//")
    else:
        logging.debug(f"Error in validating URL: {URL}")
        return "HTTP/1.0 400 Bad Request", None, None, None

    # Check the remaining part of the URL that comes after the http:
    if ("/" not in split_URL[1]):
        logging.debug(f"Error in validating URL: {URL}")
        return "HTTP/1.0 400 Bad Request", None, None, None
    parsed_after_http = split_URL[1].split("/")

    address = parsed_after_http[0]
    # If there is no port, default the port to 80.
    if (":" in address):
        host = address.split(":")[0]
        port = address.split(":")[1]
    else:
        host = address
        port = 80
    # Extract the path (the remaining part that comes after the address.)
    for index in range(1, len(parsed_after_http)):
        word = "/" + parsed_after_http[index]
        path += word

    return None, host, port, path

# Checks the version of the request.
def Check_Version(version):
    if version == "HTTP/1.0":
        return None, version
    else:
        logging.debug(f"Error in validating version: {version}")
        return "HTTP/1.0 400 Bad Request", version

# Checks the headers of the request.
def Check_Headers(parsed_request, header_dict):
    list_of_headers = ["Authorization", "From",
                       "If-Modified-Since", "Referer", "Host", "Referer", "Header", "User-Agent", "Connection", "Last-Modified"]
    for index in range(1, len(parsed_request) - 2):
        header = parsed_request[index]
        header_kv_pair = header.split(": ")
        if (header_kv_pair[0] in list_of_headers and header_kv_pair[0] not in header_dict.keys()):
            header_dict[header_kv_pair[0]] = header_kv_pair[1]
        else:
            logging.debug(f"Failed to validate header: {header_kv_pair[0]}")
            return "HTTP/1.0 400 Bad Request", header_kv_pair[0]
    return None, header_dict

# Prepares the headers to put into request to origin server. If there are no headers,
# then an empty string is returned.
def Prepare_Headers_For_Request(headers):
    if ("Connection" in headers.keys()):
        del headers["Connection"]
    headers_to_put_in_request = ""
    for key in headers.keys():
        headers_to_put_in_request += f'{key}: {headers[key]}\r\n'
    return headers_to_put_in_request

# This function checks the validity of a HTTP request from a client. If the method
# of the request is not a "GET" but a different acceptable method then it returns a
# 500. If the method of the request is "GET" but the format of the HTTP request is
# wrong, it will return 400.
def Validate_Request(request):
    error, method, host, path, port, version, headers = None, None, None, None, None, None, {}

    logging.debug(f"Request from client is: {request}")

    parsed_request = request.split("\r\n")
    # Splitting returns a list split by the \r\n. So the first element of that list 
    # is the first line of the request.
    first_line = parsed_request[0].split()

    # Validate the method.
    error, method = Check_Method(first_line[0])
    if error is not None:
        return error, method, host, path, port, version, headers

    # Validate the URL.
    error, host, port, path = Check_URL(first_line[1])
    if error is not None:
        return error, method, host, path, port, version, headers

    # Validate the version.
    if (len(first_line) == 2):
        return "HTTP/1.0 400 Bad Request", None, None, None, None, "Header wasn't found.", None
    error, version = Check_Version(first_line[2])
    if error is not None:
        return error, method, host, path, port, version, headers

    # If there are headers, validate the headers.
    error, headers = Check_Headers(parsed_request, headers)
    if error is not None:
        return error, method, host, path, port, version, headers

    # If the request is successfully validated, return the info.
    return error, method, host, path, port, version, headers

def Store_In_Cache(first_line, response_from_origin):
    # Parse the response from the origin.
    response = response_from_origin.split("\r\n\r\n")
    # The item at index 0 is the response line and all headers.
    parsed = response[0]
    parsed += "\r\n"
    # Get the date.
    time_formatted = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    # Add the date of when the object is stored in the cache.
    parsed += f"If-Modified-Since: {time_formatted} \r\n\r\n"
    # The item at index 1 is the data of the response.
    parsed += response[1]
    cache[first_line] = parsed
    return parsed

# Gets the If-Modified-Since header from the object stored in the cache.
def Get_IFMS_Header(object):
    header = "If-Modified-Since:"
    index = object.find(header)
    print(index)
    string = object[index : index + 48]
    return string
# Checks if the host portion of the URL in the response contains a domain 
# that is in the blocked domain list.
def Is_URL_Blocked(host):
    for blocked_domain in blocklist:
        if (host in blocked_domain):
            return True
    return False

# Controls te enabling, disabling and flushing of the cache. Returns true if the
# cache was modified and closes connection with client.
def Cache_Control(path):
    global cache_status
    if ("/proxy" in path and "/cache" in path):
        logging.debug("Enabling caching.")
        if ("/enable" in path):
            cache_status = True

        logging.debug("Disabling caching.")
        if ("/disable" in path):
            cache_status = False

        logging.debug("Flushing cache.")
        if ("/flush" in path):
            cache.clear()            
        return True
    else:
        return False
# Controls te enabling, disabling, adding, removal and flushing of the blocklist. 
# Returns true if the blocklist was modified and closes connection with client.
def Blocklist_Control(path):
    global blocklist_status
    if ("/proxy" in path and "/blocklist" in path):
        if ("/enable" in path):
            logging.debug("Enabling blocklist.")
            blocklist_status = True
        
        if ("/disable" in path):
            logging.debug("Disabling blocklist.")
            blocklist_status = False
        
        if ("/flush" in path):
            logging.debug("Flushing blocklist.")
            blocklist.clear()
        
        if ("/add/" in path):
            path_split = path.split("/")
            domain = path_split[len(path_split) - 1]
            blocklist.append(domain)
            logging.debug(f"Adding {domain} blocklist.")

        if ("/remove/" in path):
            path_split = path.split("/")
            domain = path_split[len(path_split) - 1]
            blocklist.remove(domain) 
            logging.debug(f"Removing {domain} blocklist.")

        return True
    else:
        return False

# This function is called when a client has been accepted on a socket. It takes in a client socket
# and handles the connections that follow.
def HandleConnections(client_skt, client_number):
    global cache_status
    global cache
    global blocklist_status
    global blocklist
    with socket(AF_INET, SOCK_STREAM) as origin_skt:
        try:
            # Recieve request from client.
            request_from_client = client_skt.recv(10000000)

            logging.debug(f"Request received from client {client_number}.")
            logging.debug("Validating request.")

            # Validate request.
            error_message, method, host, path, port, version, headers = Validate_Request(
                request_from_client.decode())
            logging.debug(f"Request validated for client {client_number}: {error_message}, {method}, {host}, {path}, {port}, {version}, {headers}")
            if (isinstance(port, int) == False and port is not None):
                port = int(port)

            # If there is an error while validating request, send an error message to the client.
            if (error_message is not None):
                logging.debug(f"Error code response sent to client {client_number}.")
                client_skt.send(error_message.encode())
                client_skt.close()
                return

            # Check if the request enables or disables caching.
            logging.debug(f"Checking if client {client_number} modifies the cache.")
            state = Cache_Control(path)
            if (state):
                # If cache was modified in anyway, send message to client and close connection.
                logging.debug(f"Request of client {client_number} modified the cache. Sending response and closing Connection.")
                client_skt.send(b'HTTP/1.0 200 OK\r\nConnection: close\r\n\r\n')
                client_skt.close()
                return
            logging.debug(f"Request of client {client_number} did not modify the cache.")

            logging.debug(f"Checking if client {client_number} modifies the blocklist.")
            state = Blocklist_Control(path)
            if (state):
                # If blocklist was modified in anyway, send message to client and close connection.
                logging.debug(f"Request of client {client_number} modified the blocklist. Sending response and closing Connection.")
                client_skt.send(b'HTTP/1.0 200 OK\r\nConnection: close\r\n\r\n')
                client_skt.close()
                return
            logging.debug(f"Request of client {client_number} did not modify the blocklist.")
            
            # Check if the requested domain is in the blocklist.
            if (blocklist_status == True and Is_URL_Blocked(host)):
                logging.debug(f"Blocked domain found. Sending appropriate response code to client {client_number}")
                client_skt.send(b'HTTP/1.0 403 Forbidden')
            
            # Prepare the headers that will be used to assemble the request message that is to be sent to the server.
            prepared_headers = Prepare_Headers_For_Request(headers)

            # Check if the requested object is in the cache.
            
            # Get the first line of the request because that is they key in the cache.
            parsed_request = request_from_client.decode().split("\r\n")
            first_line = parsed_request[0]

            # If cache is enabled, check if the object is in the cache.
            
            if (cache_status and first_line in cache.keys()):
                logging.debug("Checking if requested object is in cache.")

                logging.debug("Requested object found in cache.")
                cached_object = cache[first_line]

                # Get the IFM header from the stored object.
                IFM_header = Get_IFMS_Header(cached_object)

                # Add the IFM Header to the get request that is to be sent to the server.
                request_to_origin = f"{method} http://{host}{path} {version}\r\nConnection: close\r\n{prepared_headers}{IFM_header}\r\n\r\n"
                logging.debug(f"The request to send to client {client_number}'s origin is:\r\n{request_to_origin}")
                request_to_origin = request_to_origin.encode()

                # Check if the object has been modified by sending the request to the server.  
                logging.debug(f"The port specified in client {client_number}'s request is: {port}")
                origin_skt.connect((host, port))
                logging.debug(f"Proxy connected to client {client_number}'s origin server.")
                origin_skt.send(request_to_origin)
                logging.debug(f"Request to client {client_number}'s origin server sent.")

                # Receiving the message in seperate sections.
                full_response_from_origin = b''
                message = None
                while message != b'':
                    message = origin_skt.recv(10000000)
                    full_response_from_origin += message
                response_from_origin = full_response_from_origin
                logging.debug(f"Received response from client {client_number}'s origin server:\r\n{response_from_origin}")

                # If not modified, send the cached object to server.
                response_from_origin = response_from_origin.decode()
                if ("304" in response_from_origin):
                    logging.debug(f"Object in {client_number}'s request has not been modified since last caching.")
                    client_skt.sendall(cached_object.encode())
                    logging.debug(f"Cached object sent to client {client_number}.")
                    print(cache[first_line])

                # If the object was modified, store the object in the cache and forward it to the client.
                elif ("200" in response_from_origin):
                    logging.debug(f"Object in {client_number}'s request has been modified since last caching.")
                    logging.debug(f"Storing object from {client_number}'s request in caching.")

                    # Generate a If-Modified-Since header and insert it into the object before caching.
                    # Put the modified response into the variable.
                    response_from_origin = Store_In_Cache(first_line, response_from_origin)                       

                    logging.debug(f"Sending cached object to client {client_number}.")
                    client_skt.sendall(response_from_origin.encode())
                    return
            
            # If the object is not in the cache, send the request to the server and put the response in the cache.
            else:
                logging.debug(f"Either cache is disabled orrRequested object for client {client_number} is not in cache. Sending request to server")
                request_to_origin = ""

                request_to_origin = f"{method} http://{host}{path} {version}\r\nConnection: close\r\n{prepared_headers}\r\n"
                logging.debug(f"The request to send to client {client_number}'s origin is:\r\n{request_to_origin}")
                    
                request_to_origin = request_to_origin.encode()
                # Attempt to establish connection origin server.
                logging.debug(f"The port specified in client {client_number}'s request is: {port}")
                origin_skt.connect((host, port))
                logging.debug(f"Proxy connected to client {client_number}'s origin server.")

                origin_skt.send(request_to_origin)
                logging.debug(f"Request to client {client_number}'s origin server sent.")

                # Receiving the message in seperate sections.
                full_response_from_origin = b''
                message = None
                while message != b'':
                    message = origin_skt.recv(10000000)
                    full_response_from_origin += message
                response_from_origin = full_response_from_origin
                logging.debug(f"Received response from client {client_number}'s origin server:\r\n{response_from_origin}")

                # If cache is enabled, store the object inside the cache.
                if (cache_status and "200 OK" in response_from_origin.decode()):
                    logging.debug(f"Storing object from client {client_number}'s request in caching.")
                    modified_response = ""
                    modified_response = Store_In_Cache(first_line, response_from_origin.decode())
                    response_from_origin = modified_response.encode()

                # Send the response to the client.
                client_skt.sendall(response_from_origin)
                logging.debug(f"Origin server response sent to client {client_number}.")

                client_skt.close()
        except Exception as e:
                logging.debug(f"Error in handling connection. Error: {e}")
                client_skt.send(b"HTTP/1.0 400 Bad Request")

                client_skt.close()
                logging.debug(f"Closing client {client_number}'s socket.")

# Start of program execution
# Parse out the command line server address and port number to listen to
parser = OptionParser()
parser.add_option("-p", type="int", dest="serverPort")
parser.add_option("-a", type="string", dest="serverAddress")
(options, args) = parser.parse_args()

port = options.serverPort
address = options.serverAddress
if address is None:
    address = "localhost"
if port is None:
    port = 2100

# Set up signal handling (ctrl-c)
signal.signal(signal.SIGINT, ctrl_c_pressed)

# Listof clients, used for debugging.
list_of_clients = {}
lock = threading.Lock()
number_of_client = 0

# New socket for listening for clients.
with socket(AF_INET, SOCK_STREAM) as listen_for_clients:
    listen_for_clients.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listen_for_clients.bind((address, port))
    listen_for_clients.listen()

    # Initializing the pool of threads with a max number of threads as 100.
    with ThreadPoolExecutor(max_workers = 100) as threadPool:

    # Handling connections.
        while True:

            logging.debug("Listening for clients.")

            # Accepting a new client
            client_skt, client_address = listen_for_clients.accept()

            number_of_client += 1   
            logging.debug(f"New client accepted. Client number: {number_of_client}")
            threadPool.submit(HandleConnections, client_skt, number_of_client)

            
            
            


        

        
            

  
