#! /usr/bin/env python
import time

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

### looking for the library SharedMemory
import sys

import socket
import sys

sys.path.append('../../Blackboard/src/')
sys.path.append('../../Decision/src/')

from SharedMemory import SharedMemory

# instantiate configparser:
config = ConfigParser()

# looking for the file config.ini:
config.read('../../Control/Data/config.ini')

mem_key = int(config.get('Communication', 'no_player_robofei')) * 100

UDP_IP = "255.255.255.255"
UDP_PORT = 3800 + int(config.get('Communication', 'no_player_robofei'))

# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

sock.bind((UDP_IP, UDP_PORT))

bkb.write_int(mem, 'CONTROL_MESSAGES', 0)

with open("../../prob_starvars/src/relations.dat", "w") as f:
    pass

while True:
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    print "received message:", data
    #time.sleep(0.1)

    data1 = data.split()

    # if data1[0] == 'begin_starvars':
    #    bkb.write_int(mem,'CONTROL_MESSAGES', 1)
    if data1[0] == 'start':
        bkb.write_int(mem, 'CONTROL_MESSAGES', 3)
        with open("../../prob_starvars/src/relations.dat", "w") as f:
            pass
    elif data1[0] == 'search':
        bkb.write_int(mem, 'CONTROL_MESSAGES', 5)
        print 'search and stop'
        bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
        with open("../../prob_starvars/src/relations.dat", "w") as f:
            pass
    elif data1[0] == 'starvars':
        bkb.write_int(mem, 'CONTROL_MESSAGES', 6)
        bkb.write_int(mem, 'LOST_DRIVEN_ROBOT', 1)
        print 'starvars'
    elif data1[0] == "nothing":
        bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
    elif data1[0] == "stop":
        print 'stop'
        bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
    elif data1[0] == "move":
        if data1[1] == '1':
            print 'move forward'
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 1)
        elif data1[1] == '2':
            print 'move turn_left_and_go_forward'
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 2)
        elif data1[1] == '3':
            print 'move turn_right_and_go_forward'
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 3)
        elif data1[1] == '4':
            print 'move turn_back_and_go_forward'
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 4)

    else:
        with open("../../prob_starvars/src/relations.dat", "a") as f:
            f.write(data1[0] + " " + data1[1] + " " + data1[2] + " " + data1[3] + " " + data1[4] + "\n")

            
