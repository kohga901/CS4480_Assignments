# Place imports here
import signal
from optparse import OptionParser
import sys
from socket import *
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

logging.basicConfig(level=logging.DEBUG)

# The cache that stores the objects in the proxy.
# The key is the path to the object, and the value is the 
# object.
cache = {}

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
                       "If-Modified-Since", "Referer", "Host", "Referer", "Header", "User-Agent", "Connection"]
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

    logging.debug(f"Request form client is: {request}")

    parsed_request = request.split("\r\n")
    # Splitting returns a list so the first element of that list is the first
    # line of the request.
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

# This function is called when a client has been accepted on a socket. It takes in a client socket
# and handles the connections that follow.
def HandleConnections(client_skt, client_number):

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

        # If request is validated successfully, prepare request to send to origin server.

        # Check if the requested object is in the cache.

        # If the object is in the cache, check if the object has been modified by sending the request to the server.  

        # If the object is not in the cache, send the request to the server and put the response in the cache.
        else:
            request_to_origin = ""
            # Preparing the headers to put into request.
            prepared_headers = Prepare_Headers_For_Request(headers)

            request_to_origin = f"{method} http://{host}{path} {version}\r\nConnection: close\r\n{prepared_headers}\r\n"
            logging.debug(f"The request to send to client {client_number}'s origin is:\r\n{request_to_origin}")
                
            request_to_origin = request_to_origin.encode()
            # Attempt to establish connection origin server.
            with socket(AF_INET, SOCK_STREAM) as origin_skt:
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

                # Store the object thats in the response inside the cache.

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

            
            
            


        

        
            

  
