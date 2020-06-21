#! /usr/bin/env python

import socket
import time
import sys


IP = '127.0.0.1'     # Endereco IP do Servidor
PORT = 5001          # Porta que o Servidor esta

print 'Client running 2...\n'


while(True):
    time.sleep(0.2)
    input1 = raw_input()
    if input1 == "1":
        message = "update"
        print "message:", message
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.connect((IP, PORT))
        tcp.send(message)
        tcp.close()
