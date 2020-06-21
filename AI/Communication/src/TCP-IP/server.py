#! /usr/bin/env python

import socket

IP = '127.0.0.1'     # Endereco IP do Servidor
PORT = 5001            # Porta que o Servidor esta

print 'Server running...\n'

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
orig = (IP, PORT)
tcp.bind(orig)
tcp.listen(1)

while True:
    con, cliente = tcp.accept()
    print 'Conectado por', cliente
    while True:
        data = con.recv(1024)
        if not data:
            break
        else:
            print "received message:", data

    print 'Finalizando conexao do cliente', cliente
    con.close()
