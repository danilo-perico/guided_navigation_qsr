#! /usr/bin/env python

import socket
import time
import sys

sys.path.append('..')

from config import *
## instantiate config:
prob_starvars_config = Config()

UDP_IP = "255.255.255.255"
number_active_entities = prob_starvars_config.number_of_oriented_points

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1) #broadcast

##### starting reasoning ######
print '===== Start ====='
message = 'start'
print message
time.sleep(2)
for i in range(1, number_active_entities + 1):
    sock.sendto(message, (UDP_IP, 3800 + i))
print



