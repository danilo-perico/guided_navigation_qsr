#! /usr/bin/env python
# coding: utf-8

import time
import pygame
from math import *
import sys

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

### looking for the library SharedMemory

import socket
sys.path.append('../../')
from Blackboard.src.SharedMemory import SharedMemory
from prob_starvars.src.StarVarsReasoning import *
from prob_starvars.src.ProbStarVarsReasoning import *
from prob_starvars.src.ParticleFilter import *

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
prob_starvars_config = Config()

mem_key_coord = prob_starvars_config.coordinator * 100
mem_coord = bkb.shd_constructor(mem_key_coord)

mem_key_driven = (prob_starvars_config.driven+1) * 100
mem_driven = bkb.shd_constructor(mem_key_driven)

### set robot number
bkb.write_int(mem, 'ROBOT_NUMBER', int(config.get('Communication', 'no_player_robofei')))

if bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.coordinator:
    pygame.init()
    pygame.display.set_caption('Reasoning Display')
    screen_width = 800
    screen_height = screen_width
    dimension = screen_width, screen_height
    background = pygame.display.set_mode(dimension)
    background.fill((240, 240, 240))
    pygame.display.flip()
else:
    background = None

bkb.write_int(mem, 'REASONING_COMPLETED', 1)
ctrl = 0
count_starvars_failure = 0
turn_ctrl = 0
bkb.write_int(mem, 'DECISION_ACTION_A', 0)
bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
bkb.write_int(mem, 'FINISH', 0)
bkb.write_int(mem_coord, 'FINISH', 0)
bkb.write_int(mem_driven, 'FINISH', 0)

reset = [False]

try:
    print 'WORLD NUMBER', sys.argv[1]
    episode = int(sys.argv[1])
except:
    episode = 0


if episode == 0:

    with open("../../prob_starvars/src/answer_instructions_number.dat", "w") as f_inst:
        pass

    with open("../../prob_starvars/src/answer_time_each_decision.dat", "w") as f_time:
        pass

    with open("../../prob_starvars/src/path_total_time_per_episode.dat", "w") as f_path:
        pass

number_of_iterations = 0
bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
bkb.write_int(mem, 'DECISION_ACTION_A', 0)
hit_ctrl = 0
x_old = -1
y_old = -1
complete_path = 0
total_time = 0
start_time_total_episode = 0
end_time_total_episode = 0
episode_ctrl_guided = -1
finish_check = 0


while True:
    print "control messages", (bkb.read_int(mem, 'CONTROL_MESSAGES'))
    action = 'empty'

    if bkb.read_int(mem_coord, 'REASONING_COMPLETED') == 1:
        x_old = -1
        y_old = -1
        
    if bkb.read_int(mem, 'SERVER_BEGIN') == 2 and bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.driven+1:
        hit_ctrl = 0
        bkb.write_int(mem, 'HIT', 0)
        time.sleep(2)
        complete_path = 0
        episode_ctrl_guided += 1
        x_old = bkb.read_int(mem, 'ROBOT_X')
        y_old = bkb.read_int(mem, 'ROBOT_Y')
        start_time_total_episode = time.time()
        bkb.write_int(mem, 'SERVER_BEGIN', 0)
        
    
    if bkb.read_int(mem, 'FINISH') == 2:
        if finish_check == 0: 
            finish_check = 1
            end_time_total_episode = time.time()
            with open("../../prob_starvars/src/path_total_time_per_episode.dat", "a") as f_path:
                f_path.write(str(episode) + " " + str(complete_path) + " " + str(end_time_total_episode - start_time_total_episode) + "\n")
            bkb.write_int(mem_coord, 'FINISH', 3)


    if bkb.read_int(mem, 'FINISH') == 1: 
        bkb.write_int(mem_driven, 'FINISH', 2)

    if bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.coordinator:
        if bkb.read_int(mem, 'REASONING_COMPLETED') == 1:
            bkb.write_int(mem, 'REASONING_COMPLETED', 0)
            ctrl = 0
            reset = [False]
            number_of_iterations = 0
       

        if bkb.read_int(mem, 'LOST_DRIVEN_ROBOT') == 1:
            bkb.write_int(mem, 'ENVIRONMENT_SETUP', 1)
            number_of_iterations = 1000
            with open("../../prob_starvars/src/answer_instructions_number.dat", "a") as f_inst:
                f_inst.write(str(episode) + " " + str(number_of_iterations) + "\n")
            bkb.write_int(mem, 'LOST_DRIVEN_ROBOT', 0)
            bkb.write_int(mem, 'REASONING_COMPLETED', 1)
            time.sleep(3)
   

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        if bkb.read_int(mem, 'FINISH') == 3:       
            print '!!! FINISH !!!'
            with open("../../prob_starvars/src/answer_instructions_number.dat", "a") as f_inst:
                f_inst.write(str(episode) + " " + str(number_of_iterations) + "\n")
            bkb.write_int(mem, 'REASONING_COMPLETED', 1)
            bkb.write_int(mem, 'ENVIRONMENT_SETUP', 1)
            bkb.write_int(mem, 'FINISH', 4)
            time.sleep(3)


        # graphical_interface.display_update()
        background.fill((240, 240, 240))

        ###frame rate
        pygame.time.Clock().tick(60)


        if bkb.read_int(mem, 'CONTROL_MESSAGES') == 6 :
            print "############# REASONING #####################"
            if number_of_iterations >= 50:
                bkb.write_int(mem, 'REASONING_COMPLETED', 1)
                bkb.write_int(mem, 'ENVIRONMENT_SETUP', 1)
                with open("../../prob_starvars/src/answer_instructions_number.dat", "a") as f_inst:
                    f_inst.write(str(episode) + " " + str(number_of_iterations) + "\n")
                time.sleep(5)
            else:
                start_time = time.time()
                #if bkb.read_int(mem, 'FINISH') == 1:
                #    finish = 1
                #    bkb.write_int(mem, 'FINISH', 0)
                #else:
                #    finish = 0
                finish = 0
                if ctrl == 0:
                    print 'automatic_prob_starvars says: '
                    print 'start reasoning!!!'
                    if prob_starvars_config.approach == 'particle_filter': 
                    	reasoning_agent = ParticleFilter(background)
                    elif prob_starvars_config.approach == 'prob_starvars': 
                        reasoning_agent = ProbStarVarsReasoning(background)
                    else:
                        reasoning_agent = StarVarsReasoning(background)

                    if isinstance(reasoning_agent, StarVarsReasoning):
                        pygame.display.set_caption('StarVars')
                    elif isinstance(reasoning_agent, ParticleFilter):
                        pygame.display.set_caption('Particle Filter')
                    else:
                        pygame.display.set_caption('Probabilistic StarVars')
                    
                    print(reasoning_agent)

                    if reasoning_agent.reasoning(reset,finish):
                        #with open("../../prob_starvars/src/answer_instructions_number.dat", "a") as f_inst:
                        #    f_inst.write(str(episode) + " " + str(number_of_iterations) + "\n")
                        time.sleep(5)
                        bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
                    if reset[0] == False:
                        ctrl = 1
                    else:
                        reset[0] = False

                else:
                    print 'automatic_prob_starvars says: '
                    print 'call reasoning!!!'
                    if reasoning_agent.reasoning(reset, finish, ctrl):
                        #with open("../../prob_starvars/src/answer_instructions_number.dat", "a") as f_inst:
                        #    f_inst.write(str(episode) + " " + str(number_of_iterations) + "\n")
                        time.sleep(5)
                        bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
                    if reset[0] is True:
                        ctrl = 0
                        reset[0] = False

                end_time = time.time()

                with open("../../prob_starvars/src/answer_time_each_decision.dat", "a") as f_time:
                    f_time.write(str(episode) + " " + str(number_of_iterations) + " " + str(end_time - start_time) + "\n")

                number_of_iterations += 1

                if bkb.read_int(mem, 'CONTROL_MESSAGES') != 11:
                    bkb.write_int(mem, 'CONTROL_MESSAGES', 13)



    elif bkb.read_int(mem, 'ROBOT_NUMBER') == prob_starvars_config.driven + 1:
        ### COM_ACTION_ROBOT1:
        ### 0 = stop
        ### 1 = go_forward
        ### 2 = turn_left_and_go_forward
        ### 3 = turn_right_and_go_forward
        ### 4 = turn_back_and_go_forward

        print "Driven"
        print 'com_action', bkb.read_int(mem, 'COM_ACTION_ROBOT1')

        #if bkb.read_int(mem, 'CONTROL_MESSAGES') == 12:
        speed = 8
        if hit_ctrl != 1:
            print "bkb.read_int", bkb.read_int(mem, 'HIT')
            if bkb.read_int(mem, 'HIT') == 1:
                bkb.write_int(mem, 'CONTROL_MESSAGES', 9)
                bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
                bkb.write_int(mem, 'DECISION_ACTION_A', 0)
                bkb.write_int(mem, 'HIT', 0)
                hit_ctrl = 1
                print 'HIT'

        turn = 90
        if turn_ctrl == 0:
            initial_orientation = bkb.read_float(mem, 'IMU_EULER_Z') % 360

        if bkb.read_int(mem, 'COM_ACTION_ROBOT1') == 0:
            bkb.write_int(mem, 'DECISION_ACTION_A', 0)
            turn_ctrl = 0
            if x_old != -1 and y_old != -1:
                x_new = bkb.read_int(mem, 'ROBOT_X')
                y_new = bkb.read_int(mem, 'ROBOT_Y')
                path = sqrt((x_old - x_new) ** 2 + (y_old - y_new) ** 2)
                complete_path = path + complete_path
            	print 'complete_path', complete_path
            	x_old = bkb.read_int(mem, 'ROBOT_X')
            	y_old = bkb.read_int(mem, 'ROBOT_Y')

        elif bkb.read_int(mem, 'COM_ACTION_ROBOT1') == 1:
            bkb.write_int(mem, 'DECISION_ACTION_A', 8)
            bkb.write_int(mem, 'DECISION_ACTION_B', speed)
            turn_ctrl = 0

        elif bkb.read_int(mem, 'COM_ACTION_ROBOT1') == 2:
            dist = 2
            if turn_ctrl == 0:
                while dist >= 0.001:
                    heading = bkb.read_float(mem, 'IMU_EULER_Z') % 360
                    heading_angle = [cos(radians(heading)), sin(radians(heading))]
                    initial_orientation_angle = [cos(radians(initial_orientation + turn)),
                                                 sin(radians(initial_orientation + turn))]
                    dist = ((heading_angle[0] - initial_orientation_angle[0]) ** 2 +
                            (heading_angle[1] - initial_orientation_angle[1]) ** 2)
                    bkb.write_int(mem, 'DECISION_ACTION_A', 2)
            turn_ctrl = 1
            bkb.write_int(mem, 'DECISION_ACTION_A', 8)
            bkb.write_int(mem, 'DECISION_ACTION_B', speed)

        elif bkb.read_int(mem, 'COM_ACTION_ROBOT1') == 3:
            dist = 2
            if turn_ctrl == 0:
                while dist >= 0.001:
                    dist = []
                    heading = bkb.read_float(mem, 'IMU_EULER_Z') % 360
                    heading_angle = [cos(radians(heading)), sin(radians(heading))]
                    initial_orientation_angle = [cos(radians(initial_orientation - turn)), sin(radians(initial_orientation - turn))]
                    dist = ((heading_angle[0] - initial_orientation_angle[0]) ** 2 + (heading_angle[1] - initial_orientation_angle[1]) ** 2)
                    bkb.write_int(mem, 'DECISION_ACTION_A', 3)
            turn_ctrl = 1
            bkb.write_int(mem, 'DECISION_ACTION_A', 8)
            bkb.write_int(mem, 'DECISION_ACTION_B', speed)


        elif bkb.read_int(mem, 'COM_ACTION_ROBOT1') == 4:
            dist = 2
            if turn_ctrl == 0:
                while dist >= 0.001:
                    heading = bkb.read_float(mem, 'IMU_EULER_Z') % 360
                    heading_angle = [cos(radians(heading)), sin(radians(heading))]
                    initial_orientation_angle = [cos(radians(initial_orientation + 2 * turn)),
                                                 sin(radians(initial_orientation + 2 * turn))]
                    dist = ((heading_angle[0] - initial_orientation_angle[0]) ** 2 +
                            (heading_angle[1] - initial_orientation_angle[1]) ** 2)
                    bkb.write_int(mem, 'DECISION_ACTION_A', 2)
            turn_ctrl = 1
            bkb.write_int(mem, 'DECISION_ACTION_A', 8)
            bkb.write_int(mem, 'DECISION_ACTION_B', speed)

    time.sleep(0.01)
