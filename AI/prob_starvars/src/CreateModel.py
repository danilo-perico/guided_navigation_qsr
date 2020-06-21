#!/usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

import numpy as np
from math import radians as rd
from math import sin
from math import cos
from cvxopt import matrix, solvers
import copy
import sys

sys.path.append('../../..')
from config import *

# debug flag:
Debug = True

class CreateModel:
    '''CreateModel class '''
    def __init__(self, model = None):
        print
        ## instantiate config
        config = Config()
        ## data matrix
        self.data_matrix = []
        ## granularity
        self.m = config.m
        ## regions in degrees
        self.eta = 360 / self.m
        self.active_entities = config.number_of_oriented_points - 1
        self.number_of_entities = config.number_of_entities
        self.oriented_points = []
        self.landmarks = []
        self.missing_orientation = []
        self.missing_relations_from = []
        self.overall_orientation = []
        self.overall_relations = []
        self.total_entities = 0
        self.loopnum = 0
        self.variable_list = []
        self.orient_index = []
        self.relations_index = []
        self.xy = []
        self.overall_orientation_answer = []
        self.overall_relations_answer = []
        self.model = model
        self.h_ctrl = 0
        self.force_recursive_break = 0
        self.driven = config.driven
        self.orientation_driven_agent = 0


    def modeling(self, data_matrix):
        xy = [[]]
        #print xy
        for i in range(2*self.number_of_entities):
            xy[0].append([0])

        ref_dist = 1

        triangles_angles = []
        distances = []

        for i in range(0, self.number_of_entities - 2):
            a = 0
            b = 1
            c = 2 + i
            triangles_angles.append([])
            distances.append([])
            for j in range(0, 2): #2 angles
                filtering = data_matrix[np.where(data_matrix[:, 0] == a)]
                print 'filtering\n', filtering
                filtering2 = filtering[np.where(filtering[:, 5] == b)]
                print 'filtering2\n', filtering2
                alpha = filtering2[0][2]
                filtering2 = filtering[np.where(filtering[:, 5] == c)]
                print 'filtering2\n', filtering2
                beta = filtering2[0][2]
                angle = abs(alpha - beta)

                if angle >= 180:
                    angle = abs(angle - 360)

                triangles_angles[i].append(angle)

                aux = a
                a = b
                b = c
                c = aux


            triangles_angles[i].append(180 - (triangles_angles[i][0] + triangles_angles[i][1]))

            #distances
            for j in range(0,len(triangles_angles[i])):
                if j == len(triangles_angles[i])-1:
                    distances[i].append(ref_dist)
                else:
                    try:
                        distances[i].append(ref_dist*sin(rd(triangles_angles[i][j])) / sin(rd(triangles_angles[i][len(triangles_angles[i])-1])))
                    except:
                        distances[i].append(ref_dist*sin(rd(triangles_angles[i][j])) / sin(rd(1)))


        filtering = data_matrix[np.where(data_matrix[:, 0] == 0)]
        for i in range(self.number_of_entities):
            if i != 0:
                filtering2 = filtering[np.where(filtering[:, 5] == i)]
                alpha = filtering2[0][2]
                if i == 1:
                    #x:
                    xy[0][i] = [cos(rd(alpha)) * ref_dist]
                    #y:
                    xy[0][(i+self.number_of_entities)] = [sin(rd(alpha)) * ref_dist]
                else:
                    #x:
                    xy[0][i] = [cos(rd(alpha)) * distances[i-2][1]]
                    #y:
                    xy[0][(i+self.number_of_entities)] = [sin(rd(alpha)) * distances[i-2][1]]
        #print "============="
        #print 'triangles_angles', triangles_angles
        #print 'distances', distances
        #print xy
        #print "============="
        self.xy = xy

        for i in range(self.active_entities):
            filtering = data_matrix[np.where(data_matrix[:, 0] == i)]
            #if Debug: print 'filtering\n', filtering
            self.overall_orientation_answer.append(filtering[0][1])

    def getAnswer(self):
        return np.array(self.overall_orientation_answer), np.array(self.xy)
