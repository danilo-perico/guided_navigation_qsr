# !/usr/bin/env python
# coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

import random

class WorldModel():
    def __init__(self, points):
        self.points = points

    def __repr__(self):
        xy = []
        for i in range(0, len(self.points)):
            xy.append((self.points[i].x, self.points[i].y, self.points[i].orientation))
        return 'points [x,y,orientation]: %s' % (xy)

