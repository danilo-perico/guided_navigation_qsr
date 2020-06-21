#!/usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

import numpy as np
from math import radians as rd
from math import degrees
from math import sin
from math import cos
from cvxopt import matrix, solvers
import copy
import sys

sys.path.append('../../..')
from config import *


class StarVars():
    ''' StarVars class '''
    def __init__(self, model = None):
        print
        print 'class StarVars says:'

        print 'StarVars initiated'
        print
        ## instantiate config
        config = Config()
        ## data matrix
        self.data_matrix = []
        ## granularity
        self.m = config.m
        ## regions in degrees
        self.eta = 360.0 / self.m
        self.active_entities = config.number_of_oriented_points - 1
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
        self.xy_answer = []
        self.overall_orientation_answer = []
        self.overall_relations_answer = []
        self.model = model
        self.h_ctrl = 0
        self.force_recursive_break = 0
        self.driven = config.driven
        self.orientation_driven_agent = 0


    def Decide_StarVars(self, variable_list, h_element):
        G = []
        for i in range(0, 2 * len(self.data_matrix)):
            G.append(2 * self.total_entities * [0.])
        G = np.array(G)

        k = 0
        self.overall_orientation = list(self.overall_orientation)
        number_missing_orientations = self.overall_orientation.count(-1)

        ctrl_orient = 0
        ctrl_relations = number_missing_orientations

        for i in range(0, len(self.oriented_points)):
            aux = self.data_matrix[np.where(self.data_matrix[:, 0] == i)]
            angle = rd(aux[0][1])
            if self.overall_orientation[i] == -1:
                angle = rd(variable_list[ctrl_orient] * self.eta)
                ctrl_orient += 1

            for j in range(0, self.total_entities):
                if (i != j):
                    aux2 = aux[np.where(aux[:, 5] == j)]
                    relation1 = rd(aux2[0][2] * self.eta)
                    relation2 = rd(((aux2[0][3] + 1) % self.m) * self.eta)

                    if self.overall_relations[i][j] == -1:
                        relation1 = rd(variable_list[ctrl_relations]  * self.eta)
                        relation2 = rd(((variable_list[ctrl_relations] + 1) % self.m)  * self.eta)
                        ctrl_relations+=1

                    G[k][i] = -sin(angle + relation1)
                    G[k][j] = sin(angle + relation1)

                    G[k + 1][i] = sin(angle + relation2)
                    G[k + 1][j] = -sin(angle + relation2)

                    G[k][i + self.total_entities] = cos(angle + relation1)
                    G[k][j + self.total_entities] = -cos(angle + relation1)

                    G[k + 1][i + self.total_entities] = -cos(angle + relation2)
                    G[k + 1][j + self.total_entities] = cos(angle + relation2)

                    k += 2

        h = []
        for i in range(0, len(G)):
            if i % 2 == 0:
                if self.h_ctrl == 0:
                    h.append(-0.3) #-0.3
                else:
                    h.append(0.)
            else:
                h.append(h_element)
        h = matrix(h)

        Aeq = None
        beq = None

        ### to keep standing points at the same place:
        if self.model != None:
            b = []
            A = np.identity(self.total_entities * 2)
            A = np.delete(A, self.driven, 0)
            A = np.delete(A, self.driven + self.total_entities-1, 0)
            A_array = np.array(A)
            A_t = [list(i) for i in zip(*A_array)]
            Aeq = matrix(A_t)
            Aeq2 = np.array(Aeq)

            for i in range(0, len(self.model.points)):
                if i != self.driven:
                    b.append(self.model.points[i].x)

            for i in range(0, len(self.model.points)):
                if i != self.driven:
                    b.append(self.model.points[i].y)

            beq = matrix(b)

        #print '===== original constraints matrix ====='
        #print G
        #print '======================='

        G = [list(i) for i in zip(*G)]
        G = matrix(G)

        c = 2 * self.total_entities * [0.]
        c = matrix(c)
        solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF', 'meth': 'GLP_PRIMAL', 'tol_bnd': 1e-4}
        sol = solvers.lp(c, G, h, Aeq, beq, solver='glpk')

        #print 'variable_list', variable_list
        #print(sol['x'])

        if sol['status'] == 'optimal':
            self.xy_answer.append(np.array(sol['x']))
            #print 'StarVars answer:'
            #print(sol['x'])
            #print 'variable_list', variable_list

            temp = list(self.overall_orientation)
            for i in range(0, number_missing_orientations):
                for j in range(0, len(temp)):
                    if temp[j] == -1: # or temp[j] == -2:
                        temp[j] = variable_list[i] * self.eta
                        break
            self.overall_orientation_answer.append(temp)

            #print 'self.overall_relations', self.overall_relations
            temp_r = copy.deepcopy(self.overall_relations)

            print "variable_list", variable_list
            print "temp_r", temp_r

            h = number_missing_orientations
            for i in range(0, len(temp_r)):
                for j in range(0, len(temp_r[0])):
                    if temp_r[i][j] == -1: # or temp_r[i][j] == -2:
                        temp_r[i][j] = variable_list[h]
                        h += 1
                        #break
            self.overall_relations_answer = copy.deepcopy(temp_r)
            print "self.overall_relations_answer_teste", self.overall_relations_answer
            #if self.model != None:
            self.force_recursive_break = 1


    def Recursive_For(self, variable_list, n, h):
        if n <= 0:
            if self.force_recursive_break != 1:
                self.Decide_StarVars(variable_list, h) == 0
            else:
                return 0
        else:
            m = np.arange(0, self.m)
            for i in m:
                self.Recursive_For(variable_list + [i], n - 1, h)


    def data_pre_processing(self, data_matrix):
        self.data_matrix = data_matrix
        print "data_matrix_starvars"
        print self.data_matrix

        ### get oriented points ###
        for i in range(len(self.data_matrix)):
            self.oriented_points = list(self.oriented_points)
            self.oriented_points.append(self.data_matrix[i][0])
        self.oriented_points = np.unique(self.oriented_points)

        ### get landmarks ###
        for i in range(len(self.data_matrix)):
            if self.data_matrix[i][5] not in self.oriented_points:
                self.landmarks = list(self.landmarks)
                self.landmarks.append(self.data_matrix[i][5])
        self.landmarks = np.unique(self.landmarks)

        #total number of entities
        self.total_entities = len(self.oriented_points) + len(self.landmarks)


        ### get missing orientations ###
        orientation_filter = self.data_matrix[np.where(self.data_matrix[:, 1] == -1)]

        self.missing_orientation = np.unique(orientation_filter[:, 0])
        #print self.missing_orientation
        ################################

        self.overall_orientation = [0] * self.oriented_points
        for i in range(0, len(self.overall_orientation)):
            orientation_filter = self.data_matrix[np.where(self.data_matrix[:, 0] == i)]
            #self.overall_orientation[i] = np.unique(orientation_filter[:,1])
            self.overall_orientation[i] = max(set(list(orientation_filter[:, 1])), key=list(orientation_filter[:, 1]).count)

        self.overall_relations = []
        for i in range(0, len(self.oriented_points)):
            self.overall_relations.append((len(self.oriented_points) + len(self.landmarks))* [0])

        for i in range(0, len(self.oriented_points)):
            for j in range(0, (len(self.oriented_points) + len(self.landmarks))):
                if i != j:
                    relations_filter_from = self.data_matrix[np.where(self.data_matrix[:, 0] == i)]
                    relations_filter_to = relations_filter_from[np.where(relations_filter_from[:, 5] == j)]
                    self.overall_relations[i][j] = relations_filter_to[:, 2][0]
                else:
                    self.overall_relations[i][j] = 'x'

        ### get missing relations ###
        relations_filter = self.data_matrix[np.where(self.data_matrix[:, 2] == -1)]
        self.missing_relations_from = relations_filter[:, 0]
        print "missing relations", self.missing_relations_from
        ################################

        self.loopnum = len(self.missing_orientation) + len(self.missing_relations_from)

        for i in range(0, len(self.overall_orientation)):
            if self.overall_orientation[i] == -1: # or self.overall_orientation[i] == -2:
                self.orient_index.append(i)
        #print self.orient_index

        for i in range(0, len(self.overall_relations)):
            for j in range(0, len(self.overall_relations[0])):
                if self.overall_relations[i][j] == -1: # or self.overall_relations[i][j] == -2:
                    self.relations_index.append([i, j])
        #print self.relations_index

        return self.loopnum


    def getAnswer(self):
        for i in range(0, len(self.overall_orientation_answer)):
            self.overall_orientation_answer[i].insert(self.driven, self.orientation_driven_agent)
        return np.array(self.overall_orientation_answer), np.array(self.xy_answer), np.array(self.overall_relations_answer)
