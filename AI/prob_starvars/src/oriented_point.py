# !/usr/bin/env python
# coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

import random

class OrientedPoint():
    def __init__(self, entity):
        self.x = 0.
        self.y = 0.
        self.orientation = 0.
        self.particles = []
        self.w = []
        self.mean_x = 0.
        self.mean_y = 0.
        self.mean_orientation = 0.
        self.has_orientation = True
        self.w_sum = 0.
        if entity == 0:
            self.color = (255, 0, 0)
        elif entity == 1:
            self.color = (0, 0, 200)
        elif entity == 2:
            self.color = (153, 51, 153)
        elif entity == 3:
            self.color = (190, 190, 0)

        else:
            self.color = (211, 211, 211)

