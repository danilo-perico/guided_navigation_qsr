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
from world import *
from simulation import *

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

def setup_experiments(screen, robots, ball, count):
    if count == 0:

        ball.x = target[count][0]
        ball.y = target[count][1]

        ### 1 robot
        x = robots_pos[count][0]
        y = robots_pos[count][1]
        theta = 0
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.RED, dist_limit_vision, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5.)
        robots.append(robot)

        ### 2 robot
        x = robots_pos[count+1][0]
        y = robots_pos[count+1][1]
        theta = robots_pos[count+1][2]
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.CYAN, dist_limit_vision, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5.)
        robots.append(robot)

        ### 3 robot
        x = robots_pos[count+2][0]
        y = robots_pos[count+2][1]
        theta = robots_pos[count+2][2]
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.PURPLE, dist_limit_vision, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5.)
        robots.append(robot)

        ### 4 robot
        x = robots_pos[count+3][0]
        y = robots_pos[count+3][1]
        theta = robots_pos[count+3][2]
        robot = Robot(x, y, theta,(len(robots)+1)* screen.KEY_BKB, screen.YELLOW, 5, radians(70))
        robot.imu_initial_value = theta
        robot.set_errors(0, 0, 0, 0, 0, 0.1, 0, 0, 0, 0, 0, 5.)
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

#        subprocess.call(['./start_automatic_experiment.sh'])
#        time.sleep(5)
#        execfile('start.py')
    else:
        ball.x = target[count][0]
        ball.y = target[count][1]
        for i in range(0, len(robots)):
            robots[i].x = robots_pos[count*len(robots)+i][0]
            robots[i].y = robots_pos[count*len(robots)+i][1]
            if i == coordinator:
                robots[i].rotate = 0
            else:
                robots[i].rotate = robots_pos[count*len(robots)+i][2]

        #x = random.randint(0+50, screen.screen_width-50)
        #y = random.randint(0+50, screen.screen_height-50)
        #ball.x, ball.y = x, y

        #time.sleep(5)
        #execfile('start.py')
        
    #return 'set'
    
screen = Screen()
screen.start_simulation()
simul = Simulation(screen)
field = Nothing(screen)
simul.field = field
ball = Ball(520,370,0.95)
robots = []
field.draw_nothing()
while True:
    pygame.display.flip()
    modelo = int(raw_input())
    field.draw_nothing()
    setup_experiments(screen, robots, ball, modelo)
    for robot in range(0, len(robots)):
        robots[robot].draw_robot(robot, screen)
        robots[robot].draw_starvars(screen)
    ball.draw_ball(screen)
    pygame.display.flip()

screen.clock.tick(100)

