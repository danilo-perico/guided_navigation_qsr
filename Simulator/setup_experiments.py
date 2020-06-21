#! /usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__project__ = "Probabilistic StarVars"
__file__ = "setup_experiments.py"

import random
import subprocess
import time
from robot import *
from ball import *

import sys
sys.path.append(('../../../'))
sys.path.append('../../')
sys.path.append('../')

from config import Config



prob_starvars_config = Config()
coordinator = prob_starvars_config.coordinator - 1
dist_limit_vision = 900

robots_position = [line.strip() for line in open("robots.dat", 'r')]
robots_pos = []
for i in range(0, len(robots_position)):
    robots_pos.append(robots_position[i].split())
for i in range(0, len(robots_pos)):
    robots_pos[i] = map(int, robots_pos[i])

target_position = [line.strip() for line in open("target.dat", 'r')]
target = []
for i in range(0, len(target_position)):
    target.append(target_position[i].split())
for i in range(0, len(target)):
    target[i] = map(int, target[i])

episode = 0
euclidean_distance = 0
final_distance = 0


def check(x, y):
    print 'check'
    radius = 9
    x1 = 70 
    y1 = 70 
    x2 = 970 
    y2 = 670
    if (x - radius > x2):
        x = 870
        if y > 570:
            y = 570
        elif y < 170:
            y = 170
    elif (x + radius < x1):
        x = 170
        if y > 570:
            y = 570
        elif y < 170:
            y = 170

    if (y - radius > y2):
        y = 570
        if x > 870:
            x = 870
        elif x < 170:
            x = 170
    elif (y + radius < y1):
        y = 170
        if x > 870:
            x = 870
        elif x < 170:
            x = 170
    return x,y


def setup_experiments(screen, robots, ball, count, count_ctrl):

    global episode
    global euclidean_distance
    global final_distance
    
    if count == 0:
        with open("euclid_and_end_dist.dat", "w") as f_inst:
            pass
                    
    episode = count

    if count_ctrl == 0:
        x,y = check(target[count][0], target[count][1])
        ball.x = x
        ball.y = y

        ### 1 robot
        x = robots_pos[count*prob_starvars_config.number_of_oriented_points][0]
        y = robots_pos[count*prob_starvars_config.number_of_oriented_points][1]
        theta = 0
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.RED, dist_limit_vision, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0.2, 0, 0.1, 0, 0.2, 0, 0, 0, 0, 0, 0.2)
        #robot.set_errors(0, 0., 0, 0., 0, 0., 0, 0, 0, 0, 0, 0.2)
        robots.append(robot)

        ### 2 robot
        x = robots_pos[count*prob_starvars_config.number_of_oriented_points+1][0]
        y = robots_pos[count*prob_starvars_config.number_of_oriented_points+1][1]
        theta = robots_pos[count*prob_starvars_config.number_of_oriented_points+1][2]
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.CYAN, dist_limit_vision, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0.2, 0, 0.1, 0, 0.2, 0, 0, 0, 0, 0, 0.2)
        #robot.set_errors(0, 0., 0, 0., 0, 0., 0, 0, 0, 0, 0, 0.2)
        robots.append(robot)

        ### 3 robot
        x = robots_pos[count*prob_starvars_config.number_of_oriented_points+2][0]
        y = robots_pos[count*prob_starvars_config.number_of_oriented_points+2][1]
        theta = robots_pos[count*prob_starvars_config.number_of_oriented_points+2][2]
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.PURPLE, dist_limit_vision, radians(70))
        robot.imu_initial_value = theta
        #robot.set_errors(0, 0., 0, 0., 0, 0., 0, 0, 0, 0, 0, 0.2)
        robot.set_errors(0, 0.2, 0, 0.1, 0, 0.2, 0, 0, 0, 0, 0, 0.2)
        robots.append(robot)

        ### 4 robot
        x = robots_pos[count*prob_starvars_config.number_of_oriented_points+3][0]
        y = robots_pos[count*prob_starvars_config.number_of_oriented_points+3][1]
        theta = robots_pos[count*prob_starvars_config.number_of_oriented_points+3][2]
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.YELLOW, 5, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0.2, 0, 0.1, 0, 0.2, 0, 0, 0, 0, 0, 0.2)
        #robot.set_errors(0, 0., 0, 0., 0, 0., 0, 0, 0, 0, 0, 0.2)
        robots.append(robot)

        ### goal (ball)
        #x = random.randint(0+50, screen.screen_width-50)
        #y = random.randint(0+50, screen.screen_height-50)
        #ball.x, ball.y = x, y

        for i in range(0, len(robots)):
            robots[i].bkb.write_int(robots[i].Mem, 'DECISION_ACTION_A', 0)
            robots[i].ball = ball
            if i == coordinator:
                robots[i].rotate = 0

        subprocess.call(['./start_automatic_experiment.sh', str(count)])
        time.sleep(5)
        execfile('start.py')
        print 'before euclidean'
        print 'ball.x, ball.y', ball.x, ball.y
        print 'robot3.x, robot3.y', robots[3].x, robots[3].y
        euclidean_distance = sqrt(((ball.x - robots[3].x)**2) + ((ball.y - robots[3].y)**2))
        print 'euclidean dist, episode', euclidean_distance, episode
    else:
        print 'before final'
        print 'ball.x, ball.y', ball.x, ball.y
        print 'robot3.x, robot3.y', robots[3].x, robots[3].y
        final_distance = sqrt(((ball.x - robots[3].x)**2) + ((ball.y - robots[3].y)**2))
        print 'final', final_distance

        with open("euclid_and_end_dist.dat", "a") as f_inst:
            f_inst.write(str(episode-1) + ' ' + str(euclidean_distance) + ' ' + str(final_distance) + '\n')
        
        
        subprocess.call(['./kill_sakura.sh'])
       
        x,y = check(target[count][0], target[count][1])
        ball.x = x
        ball.y = y
        for i in range(0, len(robots)):
            robots[i].x = robots_pos[count*len(robots)+i][0]
            robots[i].y = robots_pos[count*len(robots)+i][1]
            robots[i].ball = ball
            if i == coordinator:
                robots[i].rotate = 0
            else:
                robots[i].rotate = robots_pos[count*len(robots)+i][2]
        euclidean_distance = sqrt(((ball.x - robots[3].x)**2) + ((ball.y - robots[3].y)**2))
        subprocess.call(['./start_automatic_experiment.sh',  str(count)])
        time.sleep(5)
        execfile('start.py')
    episode += 1
    return 'set'
