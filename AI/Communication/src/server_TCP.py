#! /usr/bin/env python

import socket
import time

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

### looking for the library SharedMemory
import sys
sys.path.append('../../Blackboard/src/')
sys.path.append('../../Decision/src/')
from SharedMemory import SharedMemory

# instantiate configparser:
config = ConfigParser()

# looking for the file config.ini:
config.read('../../Control/Data/config.ini')

mem_key = int(config.get('Communication', 'no_player_robofei')) * 100
# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

sys.path.append('../../..')
from config import *
## instantiate config:
prob_starvars_config = Config()


IP = '127.0.0.' + config.get('Communication', 'no_player_robofei')     # Endereco IP do Servidor
PORT = 5000 + int(config.get('Communication', 'no_player_robofei')) # Porta que o Servidor esta

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
orig = (IP, PORT)
tcp.bind(orig)
tcp.listen(1)

print 'Server running...\n'
bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
sync = 0
sync_ctrl = prob_starvars_config.number_of_oriented_points
robot_flag = []
start = True

goal_found = (prob_starvars_config.number_of_oriented_points-1)*[0]
update_time_ctrl = time.time()
update_time_ctrl_begin = time.time()


while True:
    con, cliente = tcp.accept()
    #print 'goal_found', goal_found
    finish = 0
    if bkb.read_int(mem, 'FINISH') == 0:
        if goal_found.count(1) == len(goal_found):
            finish = 1
            bkb.write_int(mem, 'FINISH', 1)
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
            bkb.write_int(mem, 'DECISION_ACTION_A', 0)
            bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
            time.sleep(3)
            print "=== FINISH === "
            goal_found = (prob_starvars_config.number_of_oriented_points-1)*[0]
            
    if bkb.read_int(mem, 'CONTROL_MESSAGES') == 25: 
        update_time_ctrl = time.time()
        if (update_time_ctrl - update_time_ctrl_begin) >= 60:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 4)
            time.sleep(1)

    while True:
        data = con.recv(1024)
        if not data:
            break
        else:
            #print "received message:", data
            data1 = data.split()
            
            if data1[0] != 'goal_found':
                print "received message:", data

            if data1[0] == 'start':
                bkb.write_int(mem, 'SERVER_BEGIN', 3)
                start = True
                with open("../../prob_starvars/src/relations.dat", "w") as f:
                    pass
            elif data1[0] == 'restart':
                bkb.write_int(mem, 'SERVER_BEGIN', 4)
                start = True
                with open("../../prob_starvars/src/relations.dat", "w") as f:
                    pass
            elif data1[0] == 'update':
                if start == True:
                    continue
                else:
                    bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
                    bkb.write_int(mem, 'DECISION_ACTION_A', 0)
                    bkb.write_int(mem, 'CONTROL_MESSAGES', 5)
                    sync = 0
                    update_time_ctrl_begin = time.time()
                    with open("../../prob_starvars/src/relations.dat", "w") as f:
                        pass
            elif data1[0] == 'synchronization':
                sync += 1
                with open("../../prob_starvars/src/relations.dat", "a") as f:
                    f.write(data1[1] + " " + data1[2] + " " + data1[3] + " " + data1[4] + " " + data1[5] + " " + data1[6] + "\n")
                print 'sync', sync
                #if sync >= prob_starvars_config.number_of_oriented_points:
                if sync >= prob_starvars_config.number_of_oriented_points:
                    bkb.write_int(mem, 'CONTROL_MESSAGES', 10)
                
            elif data1[0] == 'continue':
                bkb.write_int(mem, 'CONTROL_MESSAGES', 12)
            elif data1[0] == 'starvars':
                bkb.write_int(mem, 'CONTROL_MESSAGES', 6)
                print 'starvars'
            elif data1[0] == "stop":
                bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
            elif data1[0] == "hit":
                bkb.write_int(mem, 'LOST_DRIVEN_ROBOT', 1)
                print "HIT"
            elif data1[0] == 'goal_found':
                if bkb.read_int(mem, 'FINISH') == 1 or bkb.read_int(mem, 'FINISH') == 2 or bkb.read_int(mem, 'FINISH') == 3:
                    pass
                else:
                    if int(data1[1]) != prob_starvars_config.driven:
                        goal_found[int(data1[1])] = int(data1[2])
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
                    bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)

            else:
                start = False
                with open("../../prob_starvars/src/relations.dat", "a") as f:
                    f.write(data1[0] + " " + data1[1] + " " + data1[2] + " " + data1[3] + " " + data1[4] + " " + data1[5] + "\n")

    #print 'Finalizando conexao do cliente', cliente
    con.close()
