#! /usr/bin/env python
# coding: utf-8

__author__ = "Danilo H. Perico"
__project__ = "Probabilistic StarVars"
__file__ = "qsr.py"

from threading import Thread

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

import time
import sys
from math import degrees
from math import atan2
from math import sin
from math import cos
from math import radians as rd

from starvars_discretization import *

sys.path.append('../../Blackboard/src/')
from SharedMemory import SharedMemory

sys.path.append('../../..')
from config import *

# instantiate configparser and config:
config = ConfigParser()
prob_starvars_config = Config()

# looking for the file config.ini:
config.read('../../Control/Data/config.ini')

mem_key = int(config.get('Communication', 'no_player_robofei')) * 100

# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

bkb.write_int(mem, 'DECISION_ACTION_VISION', 0)
bkb.write_int(mem, 'LOCALIZATION_FIND_ROBOT', 1)
bkb.write_int(mem, 'GOAL_FOUND', 0)


###function to set the number of the robot that will be found for the vision system
def set_find_robot(other_robot_number, goal):
    if other_robot_number != goal:
        bkb.write_int(mem, 'DECISION_ACTION_VISION', 2)
        bkb.write_int(mem, 'LOCALIZATION_FIND_ROBOT', other_robot_number)
    else:
        bkb.write_int(mem, 'DECISION_ACTION_VISION', 0)
        bkb.write_int(mem, 'LOCALIZATION_FIND_ROBOT', other_robot_number)


### begin ###
print
print '========== Qualitative Spatial Reasoning for Guided Navigation ==========='
print
### set robot number
bkb.write_int(mem, 'ROBOT_NUMBER', int(config.get('Communication', 'no_player_robofei')))

### set variables
number_entities = prob_starvars_config.number_of_entities
goal = prob_starvars_config.goal + 1
driven = prob_starvars_config.driven + 1
m = prob_starvars_config.m

###enforce the robot to not take any action
bkb.write_int(mem, 'DECISION_ACTION_A', 0)

###not send any message
bkb.write_int(mem, 'CONTROL_MESSAGES', 0)

#### CONTROL MESSAGES:
### 0: do nothing
### 1: Look at entity that has been driven
### 2: send found relations
### 3: start
### 4: search when an own region is changed
### 5: search when another entity say to do so
### 6: start prob starvars
### 7: start prob starvars when another entity say to do so
### 9: driven agent hit
### 10: synchronization
### 11: restart
### 12: FINISH

print 'bkb.read_int(mem,ROBOT_NUMBER)', bkb.read_int(mem, 'ROBOT_NUMBER')
bkb.write_int(mem, 'LOST_DRIVEN_ROBOT', 0)
relation_ctrl = 2
vision_orient_old = 0

relation_goal = -1
reasoning = prob_starvars_config.approach


while True:
    time.sleep(0.05)
    #print "inicio loop", bkb.read_int(mem, 'CONTROL_MESSAGES')

    if bkb.read_int(mem, 'SERVER_BEGIN') == 3 or bkb.read_int(mem, 'SERVER_BEGIN') == 4:
        relation_ctrl = 2
        if bkb.read_int(mem, 'SERVER_BEGIN') == 4:
            bkb.write_int(mem, 'SERVER_BEGIN', 0)
        else:
            bkb.write_int(mem, 'SERVER_BEGIN', 2)
        bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
        ### set vision to look for robots
        bkb.write_int(mem, 'DECISION_ACTION_VISION', 2)
        ###do for all robots
        for j in range(1, number_entities + 1):
            if j == bkb.read_int(mem, 'ROBOT_NUMBER'):
                continue
            ###find robot by its number:
            set_find_robot(j, goal)
            # bkb.write_int(mem, 'DECISION_ACTION_VISION', 2)
            bkb.write_int(mem, 'DECISION_SEARCH_ON', 1)
            i = 0
            ###loop for allowing that a robot can be found
            while i < 25:
                i = i + 1
                time.sleep(1)
            if bkb.read_int(mem, 'VISION_LOST') == 1:
                bkb.write_int(mem, 'DECISION_SEARCH_ON', 1)
                vision_orient = "NF"
            else:
                bkb.write_int(mem, 'DECISION_SEARCH_ON', 0)
                if j == goal:
                    sumx_cos = 0
                    sumy_sin = 0
                    for k in range(30):
                        time.sleep(0.05)
                        print 'VISION DEG', bkb.read_float(mem, 'VISION_PAN_DEG')
                        sumy_sin = sumy_sin + sin(rd(bkb.read_float(mem, 'VISION_PAN_DEG')))
                        sumx_cos = sumx_cos + cos(rd(bkb.read_float(mem, 'VISION_PAN_DEG')))
                    vision_orient  = degrees(atan2(sumy_sin, sumx_cos))
                    relation_goal = starvars_discretization(vision_orient, m, 2)
                else:
                    sumx_cos = 0
                    sumy_sin = 0
                    for k in range(30):
                        time.sleep(0.05)
                        print 'VISION_RBT01_ANGLE', bkb.read_float(mem, 'VISION_RBT01_ANGLE')
                        sumy_sin = sumy_sin + sin(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                        sumx_cos = sumx_cos + cos(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                    vision_orient  = degrees(atan2(sumy_sin, sumx_cos))
                print vision_orient

            ###StarVars discretization
            # print vision_orient
            if vision_orient == "NF":
                bkb.write_float(mem, 'COM_POS_ANGLE', -1)
            else:
                if reasoning == 'particle_filter':
                    bkb.write_float(mem, 'COM_POS_ANGLE', vision_orient)
                else:
                    bkb.write_float(mem, 'COM_POS_ANGLE', starvars_discretization(vision_orient, m))

            ###send relations found
            bkb.write_int(mem, 'CONTROL_MESSAGES', 2)
            time.sleep(1)

        print 'look at the driven agent'
        if bkb.read_int(mem, 'ROBOT_NUMBER') != driven:
            set_find_robot(driven, goal)
            bkb.write_int(mem, 'DECISION_SEARCH_ON', 1)
            time.sleep(15)

        if bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.coordinator:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 6)
            #print(bkb.read_int(mem, 'CONTROL_MESSAGES'))
        #else:
        #    bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            #print(bkb.read_int(mem, 'CONTROL_MESSAGES'))


    else:
        vision_lost_ctrl = 0
        #print 'control message:', bkb.read_int(mem, 'CONTROL_MESSAGES')
        #if bkb.read_int(mem, 'CONTROL_MESSAGES') == 0:
        #    bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            #print 'control message1:', bkb.read_int(mem, 'CONTROL_MESSAGES')
        if bkb.read_int(mem, 'CONTROL_MESSAGES') == 6 or bkb.read_int(mem, 'CONTROL_MESSAGES') == 4:
            pass
        if bkb.read_int(mem, 'CONTROL_MESSAGES') == 12:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
        if bkb.read_int(mem, 'CONTROL_MESSAGES') == 10:
            if bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.coordinator:
                time.sleep(0.5)
                bkb.write_int(mem, 'CONTROL_MESSAGES', 6)
            #else:
            #    bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
        if bkb.read_int(mem, 'CONTROL_MESSAGES') == 1:
            if bkb.read_int(mem, 'ROBOT_NUMBER') != driven:
                set_find_robot(driven, goal)
                bkb.write_int(mem, 'DECISION_SEARCH_ON', 1)
                time.sleep(1)
                sumx_cos = 0
                sumy_sin = 0
                #for k in range(10):
                #    time.sleep(0.05)
                #    sumy_sin = sumy_sin + sin(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                #    sumx_cos = sumx_cos + cos(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                #vision_orient  = degrees(atan2(sumy_sin, sumx_cos))
                if reasoning == 'particle_filter':
                    count = 0
		    # tick = tau/0.3 (0.3 = sleep time inside loop)
                    tick = prob_starvars_config/0.3 
                    angle_update_region = 5
                    angle_update_value = 0
                    # for k in range(10):
                    #     time.sleep(0.05)
                    #     sumy_sin = sumy_sin + sin(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                    #     sumx_cos = sumx_cos + cos(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                    # vision_orient_old  = degrees(atan2(sumy_sin, sumx_cos))
                    while count < tick or angle_update_value <= angle_update_region:
                        sumx_cos = 0
                        sumy_sin = 0
                        for k in range(4):
                            time.sleep(0.05)
                            sumy_sin = sumy_sin + sin(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                            sumx_cos = sumx_cos + cos(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                        vision_orient  = degrees(atan2(sumy_sin, sumx_cos))

                        current_relation = starvars_discretization(vision_orient, m, 2)
                        #print 'bkb.read_int(mem, GOAL_FOUND)', bkb.read_int(mem, 'GOAL_FOUND')

                        if bkb.read_int(mem, 'FINISH') == 2:
                            bkb.write_int(mem, 'FINISH', 3)
                            bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
                            break

                        if relation_goal == current_relation:
                            #if bkb.read_int(mem, 'GOAL_FOUND') != 1:
                            bkb.write_int(mem, 'GOAL_FOUND', 1)
                        else:
                            #if bkb.read_int(mem, 'GOAL_FOUND') == 1:
                            bkb.write_int(mem, 'GOAL_FOUND', 0)


                        bkb.write_float(mem, 'COM_POS_ANGLE3', current_relation)

                        if count == 0:
                            vision_orient_old = vision_orient
                        #print 'vision_orient_old', vision_orient_old
                        #print 'vision_orient',  vision_orient
                        angle_update_value = abs((vision_orient_old % 360) - (vision_orient % 360))
                        #print '### count, angle_update_value ###', count, angle_update_value
                        bkb.write_float(mem, 'COM_POS_ANGLE', vision_orient)

                        if bkb.read_int(mem, 'SERVER_BEGIN') == 3 or bkb.read_int(mem, 'SERVER_BEGIN') == 4 \
                        or bkb.read_int(mem, 'CONTROL_MESSAGES') == 10:
                            break
                        else:
                            count += 1
                        time.sleep(0.1)
                    else:
                        print 'STOP!'
                        if bkb.read_int(mem, 'CONTROL_MESSAGES') != 1 and bkb.read_int(mem, 'CONTROL_MESSAGES') != 0 and \
                         bkb.read_int(mem, 'CONTROL_MESSAGES') != 10:
                            print 'control message - entrou:', bkb.read_int(mem, 'CONTROL_MESSAGES')
                            #pass
                        else:
                            bkb.write_int(mem, 'CONTROL_MESSAGES', 4)
                            print 'control message4:', bkb.read_int(mem, 'CONTROL_MESSAGES')
                            time.sleep(2)
                    print 'control message - fim:', bkb.read_int(mem, 'CONTROL_MESSAGES')
                else:
                    relation = starvars_discretization(vision_orient, m, relation_ctrl)
                    print 'RELATION, relation_ctrl', relation, relation_ctrl
                    new_relation = relation
                    while relation == new_relation:
                        if bkb.read_int(mem, 'SERVER_BEGIN') == 3 or bkb.read_int(mem, 'SERVER_BEGIN') == 4 or bkb.read_int(mem, 'CONTROL_MESSAGES') == 10 or bkb.read_int(mem, 'CONTROL_MESSAGES') == 12:
                            break
                        else:
                            sumx_cos = 0
                            sumy_sin = 0
                            for k in range(10):
                                time.sleep(0.05)
                                sumy_sin = sumy_sin + sin(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                                sumx_cos = sumx_cos + cos(rd(bkb.read_float(mem, 'VISION_RBT01_ANGLE')))
                            vision_orient  = degrees(atan2(sumy_sin, sumx_cos))
                            new_relation = starvars_discretization(vision_orient, m, relation_ctrl)

                            current_relation = starvars_discretization(vision_orient, m, 2)
                            if relation_goal == current_relation:
                                if bkb.read_int(mem, 'GOAL_FOUND') != 1:
                                    bkb.write_int(mem, 'GOAL_FOUND', 1)
                                    #bkb.write_int(mem, 'CONTROL_MESSAGES', 15)
                            else:
                                if bkb.read_int(mem, 'GOAL_FOUND') == 1:
                                    bkb.write_int(mem, 'GOAL_FOUND', 0)
                                    #bkb.write_int(mem, 'CONTROL_MESSAGES', 15)

                            bkb.write_float(mem, 'COM_POS_ANGLE3', current_relation)

                            print 'NEW_RELATION, relation_ctrl', new_relation, relation_ctrl
                            if new_relation != relation:
                                if (new_relation == 0 and relation == 15) or (new_relation == 15 and relation == 0):
                                    line = 0
                                else:
                                    line = max(new_relation, relation)
                                if line % 2 == 0: #even
                                    relation_ctrl = 1 #odd

                                else: #odd
                                    relation_ctrl = 0 #even
                                sense_relation = starvars_discretization(vision_orient, m, relation_ctrl)

                            if relation_ctrl != 2:
                                bkb.write_float(mem, 'COM_POS_ANGLE', sense_relation)
                                bkb.write_float(mem, 'COM_POS_ANGLE2', sense_relation + 1)
                            else:
                                bkb.write_float(mem, 'COM_POS_ANGLE', new_relation)
                                bkb.write_float(mem, 'COM_POS_ANGLE2', new_relation)
                            time.sleep(0.05)
                    else:
                        print 'STOP!'
                        bkb.write_int(mem, 'CONTROL_MESSAGES', 4)
                        print bkb.read_int(mem, 'CONTROL_MESSAGES')
                        time.sleep(2)
            else:
                bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
    ### end ###
