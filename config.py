#! /usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__project__ = "Probabilistic StarVars"
__file__ = "config.py"

### indices starting from 0
class Config():
    def __init__(self):
        self.m = 16
        self.number_of_entities = 5
        self.number_of_oriented_points = 4
        self.number_of_landmarks = 1
        self.driven = 3
        self.goal = 4
        self.coordinator = 1
	# approaches = 'starvars', 'prob_starvars', 'particle_filter'
	self.approach = 'prob_starvars'
	# tau for particle filter approach	
	self.tau = 3
