#! /usr/bin/env python

import socket
import time
import sys

sys.path.append('..')

from config import *
## instantiate config:
prob_starvars_config = Config()
number_active_entities = prob_starvars_config.number_of_oriented_points

IP = '127.0.0.'
PORT = 5000

print '===== Start ====='
message = 'start'
print message

for i in range(1, number_active_entities + 1):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcp.connect((IP + str(i), PORT + i))
    tcp.send (message)
    tcp.close()
print




