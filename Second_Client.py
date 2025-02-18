from socket import *

with socket(AF_INET, SOCK_STREAM) as skt:
    skt.connect(('localhost', 2100))
    print("connected.")
    skt.send(b'GET http://www.flux.utah.edu/proxy/blocklist/enable HTTP/1.0 \r\n\r\n')
    message_from_server = skt.recv(10000000)
    print(message_from_server.decode())