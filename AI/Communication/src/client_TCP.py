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

number_active_entities = prob_starvars_config.number_of_oriented_points

# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

m = prob_starvars_config.m


IP = '127.0.0.'     # Endereco IP do Servidor
PORT = 5000         # Porta que o Servidor esta

print 'Client running...\n'
bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
bkb.write_int(mem, 'LOOK_DRIVEN_CTRL', 0)
sync = 0
sent2 = time.time()

bkb.write_int(mem, 'GOAL_FOUND', 0)
goal_found = bkb.read_int(mem, 'GOAL_FOUND')
ctrl_finish = 0

while(True):
        time.sleep(0.01)
        goal_found = bkb.read_int(mem, 'GOAL_FOUND')

        ctrl_finish += 1
        if ctrl_finish > 30:
            ctrl_finish = 0

        region = bkb.read_float(mem, 'COM_POS_ANGLE')
        region2 = bkb.read_float(mem, 'COM_POS_ANGLE2')
        region3 = bkb.read_float(mem, 'COM_POS_ANGLE3')
        if config.get('Communication', 'imu') == 'off':
            imu = -1
        else:
            imu = bkb.read_float(mem, 'IMU_EULER_Z')
            imu = round(imu)
            imu = imu % 360
            for i in range(0, m):
                if i == 0:
                    if imu < 180:
                        if abs(imu - (i * 360 / m)) <= 360/m/2:
                            imu = i * 360 / m
                    else:
                        if abs((imu - 360) - (i * 360 / m)) <= 360/m/2:
                            imu = i * 360 / m
                else:
                    if abs(imu - (i * 360 / m)) <= 360/m/2:
                        imu = i * 360 / m

        if ctrl_finish >= 30:
            message = "goal_found" + " " + str(bkb.read_int(mem, 'ROBOT_NUMBER')-1) + ' ' + str(bkb.read_int(mem, 'GOAL_FOUND'))
            #print "message:", message
            try:
                for i in range(1, number_active_entities + 1):
                    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tcp.connect((IP + str(i), PORT + i))
                    tcp.send(message)
                    tcp.close()
            except:
                pass


        if bkb.read_int(mem, 'CONTROL_MESSAGES') == 4:
            message = "update"
            print "message:", message
            for i in range(1, number_active_entities + 1):
                tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp.connect((IP + str(i), PORT + i))
                tcp.send(message)
                tcp.close()


        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 5:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 25)
            message = str(bkb.read_int(mem, 'ROBOT_NUMBER') - 1) + ' ' + str(imu) + ' ' + str(region) + ' ' + str(
                     (region2) % m) + ' ' + str(region3) + ' '  + str(prob_starvars_config.driven)
            for i in range(1, number_active_entities + 1):
                tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp.connect((IP + str(i), PORT + i))
                message_final = 'synchronization' + ' ' + message
                tcp.send(message_final)
                tcp.close()


            # for i in range(1, number_active_entities + 1):
            #
            #     tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #     tcp.connect((IP + str(i), PORT + i))
            #     tcp.send(message)
            #     tcp.close()

        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 2:
            if region != -1 and config.get('Communication', 'imu') == 'off':
                message = str(bkb.read_int(mem, 'ROBOT_NUMBER') - 1) + ' ' + str(imu) + ' ' + str(region) + ' ' + str(
                    (region) % m) + ' ' + str(region) + ' ' + str(bkb.read_int(mem, 'LOCALIZATION_FIND_ROBOT') - 1)
            else:
                message = str(bkb.read_int(mem, 'ROBOT_NUMBER') - 1) + ' ' + str(imu) + ' ' + str(region) + ' ' + str(
                    region) + ' ' + str(region) + ' ' + str(bkb.read_int(mem, 'LOCALIZATION_FIND_ROBOT') - 1)
            print "message:", message
            for i in range(1, number_active_entities + 1):
                tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp.connect((IP + str(i), PORT+i))
                tcp.send (message)
                tcp.close()
            bkb.write_int(mem, 'CONTROL_MESSAGES', 0)

        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 6 or bkb.read_int(mem, 'CONTROL_MESSAGES') == 3:
            if bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.coordinator:
                message = "stop"
                for i in range(1, number_active_entities + 1):
                    if i == prob_starvars_config.driven+1:
                        print "message:", message
                        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tcp.connect((IP + str(i), PORT+i))
                        tcp.send (message)
                        tcp.close()


        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 1:
            if bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.coordinator:
                if bkb.read_int(mem, 'COM_ACTION_ROBOT1') != 0:
                    message = "move" + ' ' + str(bkb.read_int(mem, 'COM_ACTION_ROBOT1'))
                    for i in range(1, number_active_entities + 1):
                        if i == prob_starvars_config.driven+1:
                            print "message:", message
                            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            tcp.connect((IP + str(i), PORT+i))
                            tcp.send (message)
                            tcp.close()
                    #bkb.write_int(mem, 'CONTROL_MESSAGES', 0)

        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 7:
            message = "starvars"
            print "message:", message
            for i in range(1, number_active_entities + 1):
                if i == prob_starvars_config.coordinator:
                    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tcp.connect((IP + str(i), PORT+i))
                    tcp.send (message)
                    tcp.close()


        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 9:
            message = "hit"
            print "message:", message
            for i in range(1, number_active_entities + 1):
                tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp.connect((IP + str(i), PORT + i))
                tcp.send(message)
                tcp.close()
            bkb.write_int(mem, 'CONTROL_MESSAGES', 0)

        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 11:
            message = "restart"
            print "message:", message
            for i in range(1, number_active_entities + 1):
                tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp.connect((IP + str(i), PORT + i))
                tcp.send(message)
                tcp.close()

        elif bkb.read_int(mem, 'CONTROL_MESSAGES') == 13:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
            message = "continue"
            print "message:", message
            for i in range(1, number_active_entities + 1):
                tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp.connect((IP + str(i), PORT + i))
                tcp.send(message)
                tcp.close()
