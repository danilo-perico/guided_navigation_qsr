#!/usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

import sys
from ProbStarVarsReasoning import *
#import matplotlib.pyplot as plt

class Interface():
    def __init__(self):
        ## instantiate config
        config = Config()
        self.rotate_control = 0
        self.index = -1
        self.robots = []
        self.mx = 0
        self.my = 0
        self.theta = 0
        self.goal = config.goal
        self.driven = config.driven

        self.entity = None

        self.screen_width = 800
        self.screen_height = self.screen_width
        self.dimension = self.screen_width, self.screen_height
        self.background = pygame.display.set_mode(self.dimension)
        self.background.fill((240,240,240))
        pygame.display.flip()
        self.points = []
        self.probability = 0.
        self.number_of_possible_answers = 0
        self.prob_starvars = ProbStarVarsReasoning(self.background)
        bkb.write_int(mem, 'RELATION_CTRL', 0)
        self.relation_ctrl = bkb.read_int(mem, 'RELATION_CTRL')

    def perform_events(self):
        for event in pygame.event.get():
            #try:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                self.prob_starvars.sense(0)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.prob_starvars.release_particles(False)
                self.prob_starvars.answers_probability()
                self.prob_starvars.qualitative_command(True)
                self.prob_starvars.draw_particles()
                self.prob_starvars.mean()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
                self.entity = self.driven
                self.prob_starvars.measurement_prob(self.entity, "complete")
                self.prob_starvars.measurement_prob(self.goal, "complete")

                #self.prob_starvars.answers_probability()
                #action = self.prob_starvars.qualitative_command(True)
                self.prob_starvars.draw_particles()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                action = 'go_forward'
                self.entity = self.driven  # int(raw_input('Point: '))
                self.prob_starvars.move(self.entity, action)
                self.prob_starvars.draw_particles()
                self.prob_starvars.mean()
                self.relation_ctrl = not self.relation_ctrl
                bkb.write_int(mem, 'RELATION_CTRL', self.relation_ctrl)


            if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                action = 'turn_left'
                self.entity = self.driven  # int(raw_input('Point: '))
                self.prob_starvars.move(self.entity, action)
                self.prob_starvars.draw_particles()
                self.prob_starvars.mean()


            if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                action = 'turn_right'
                self.entity = self.driven  # int(raw_input('Point: '))
                self.prob_starvars.move(self.entity, action)
                self.prob_starvars.draw_particles()
                self.prob_starvars.mean()


            if event.type == pygame.KEYDOWN and event.key == pygame.K_u:
                self.prob_starvars.measurement_prob(self.entity,self.relation_ctrl )

            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                self.prob_starvars.answers_probability()
                self.prob_starvars.qualitative_command()
                self.prob_starvars.draw_particles()
                self.prob_starvars.mean()
                #self.prob_starvars.spatial_relations_by_mean()


            if event.type == pygame.QUIT:
                sys.exit()
