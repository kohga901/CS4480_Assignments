from socket import *

with socket(AF_INET, SOCK_STREAM) as skt:
  skt.connect(('localhost', 2100))
  print("connected.")
  # skt.send(b'GET http://www.flux.utah.edu HTTP/1.0 \r\n\r\n')
  # buffer = input()
  # skt.send(b'GET http://www.flux.utah.edu HTTP/1.0 \r\n\r\n')
  skt.send(b'a')
  skt.send(b'b')
  skt.send(b'c')
  buffer = input()
  skt.send(b'd')



  # print(final_message.decode())
  # message_from_server = skt.recv(10000000)


  # buffer = input()
  # skt.send(b'POST http://localhost:8080/simple.html HTTP/1.0\r\n\r\n')
  # buffer = input()
  # skt.send(b'Wrongmethod http://localhost:8080/simple.html HTTP/1.0\r\n\r\n')


