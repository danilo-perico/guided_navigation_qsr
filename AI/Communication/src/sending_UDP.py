#! /usr/bin/env python

import socket
import time
import sys

sys.path.append('../../Blackboard/src/')
from SharedMemory import SharedMemory

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

## instantiate configparser:
config = ConfigParser()

sys.path.append('../../..')
from config import *

## instantiate config:
prob_starvars_config = Config()

# looking for the file config.ini:
config.read('../../Control/Data/config.ini')

mem_key = int(config.get('Communication', 'no_player_robofei')) * 100

UDP_IP = "255.255.255.255"

number_active_entities = prob_starvars_config.number_of_oriented_points

# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

### UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
### broadcast
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

m = prob_starvars_config.m



while (True):

    time.sleep(0.2)
    region = bkb.read_int(mem, 'COM_POS_ORIENT_QUALIT_ROBOT_A')

    if config.get('Communication', 'kind') == 'human':
        imu = -1
        ### for m = 8:
    #        if region % 2 == 0:
    #            region = region - 1

    else:
        imu = bkb.read_float(mem, 'IMU_EULER_Z')
        imu = round(imu)
        imu = imu % 360
        print imu
        for i in range(0, m):
            if i == 0:
                if imu < 180:
                    if abs(imu - (i * 360 / m)) <= 22.5:
                        imu = i * 360 / m
                else:
                    if abs((imu - 360) - (i * 360 / m)) <= 22.5:
                        imu = i * 360 / m
            else:
                if abs(imu - (i * 360 / m)) <= 22.5:
                    imu = i * 360 / m
                    # if imu >= (((i * (360/m)) - (360/m/2)) % 360) and imu < ((((i)*(360/m)) + (360/m/2)) % 360):

    if bkb.read_int(mem, 'CONTROL_MESSAGES') == 4:
        message = "search"
        print "message:", message
        for i in range(1, number_active_entities + 1):
            sock.sendto(message, (UDP_IP, 3800 + i))
            #        with open("../../prob_starvars/src/relations.dat","r") as f:
            #            data_matrix = f.read()
            #        print data_matrix
            #        message = 'whole_model' + '\n' + data_matrix
            #        print "message:", message
            #        for i in range(1, number_active_entities + 1):
            #            if i != bkb.read_int(mem, 'ROBOT_NUMBER'):
            #                sock.sendto(message, (UDP_IP, 3800 + i))

    elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 2:
        if region != -1 and config.get('Communication', 'kind') == 'human':
            message = str(bkb.read_int(mem, 'ROBOT_NUMBER') - 1) + ' ' + str(imu) + ' ' + str(region) + ' ' + str(
                (region) % m) + ' ' + str(bkb.read_int(mem, 'LOCALIZATION_FIND_ROBOT') - 1)
        else:
            message = str(bkb.read_int(mem, 'ROBOT_NUMBER') - 1) + ' ' + str(imu) + ' ' + str(region) + ' ' + str(
                region) + ' ' + str(bkb.read_int(mem, 'LOCALIZATION_FIND_ROBOT') - 1)
        print "message:", message
        for i in range(1, number_active_entities + 1):
            sock.sendto(message, (UDP_IP, 3800 + i))
        bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
        time.sleep(1)

    elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 6 or bkb.read_int(mem, 'CONTROL_MESSAGES') == 3 or bkb.read_int(mem,
                                                                                                                  'CONTROL_MESSAGES') == 5:
        if bkb.read_int(mem, 'ROBOT_NUMBER') == 1:
            message = "stop"
            print "message:", message
            for i in range(1, number_active_entities + 1):
                sock.sendto(message, (UDP_IP, 3800 + i))
                # bkb.write_int(mem,'CONTROL_MESSAGES', 0)

    elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 1:
        if bkb.read_int(mem, 'ROBOT_NUMBER') == 1:
            message = "move" + ' ' + str(bkb.read_int(mem, 'COM_ACTION_ROBOT1'))
            print "message:", message
            for i in range(1, number_active_entities + 1):
                sock.sendto(message, (UDP_IP, 3800 + i))

    elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 7:
        message = "starvars"
        print "message:", message
        for i in range(1, number_active_entities + 1):
            sock.sendto(message, (UDP_IP, 3800 + i))




