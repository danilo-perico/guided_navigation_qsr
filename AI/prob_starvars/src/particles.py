# !/usr/bin/env python
# coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

import pygame
from math import cos
from math import sin

from math import sqrt
from math import radians as rd
import numpy as np

class Particles():
    def __init__(self):
        ## particle posture (x, y, orientation)
        self.x = 0.
        self.y = 0.
        self.orientation = 0.0
        self.has_orientation = True
        ## noise for going forward
        self.forward_noise = 0.2
        ## noise in degrees for turning
        self.turn_noise = 5.0
        ## particle weight
        self.w = 0.
        self.model = None
        self.out_of_fov = False

    def draw_dashed_line(self, surf, color, start_pos, end_pos, width=1, dash_length=10):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dl = dash_length

        if (x1 == x2):
            ycoords = [y for y in range(y1, y2, dl if y1 < y2 else -dl)]
            xcoords = [x1] * len(ycoords)
        elif (y1 == y2):
            xcoords = [x for x in range(x1, x2, dl if x1 < x2 else -dl)]
            ycoords = [y1] * len(xcoords)
        else:
            a = abs(x2 - x1)
            b = abs(y2 - y1)
            c = round(sqrt(a ** 2 + b ** 2))
            dx = dl * a / c
            dy = dl * b / c

            xcoords = [x for x in np.arange(x1, x2, dx if x1 < x2 else -dx)]
            ycoords = [y for y in np.arange(y1, y2, dy if y1 < y2 else -dy)]

        next_coords = list(zip(xcoords[1::2], ycoords[1::2]))
        last_coords = list(zip(xcoords[0::2], ycoords[0::2]))
        for (x1, y1), (x2, y2) in zip(next_coords, last_coords):
            start = (round(x1), round(y1))
            end = (round(x2), round(y2))
            pygame.draw.line(surf, color, start, end, width)

    def draw_starvars(self, screen, color, point, scaled_x, scaled_y, j, windows_qty, x_bounds, y_bounds, relation_ctrl, m):
        windows_qty = 1
        width, height = screen.get_size()
        resolution = 360.0 / m
        side_size = width / windows_qty

        farthest_boundary = 10
        new_x = cos(rd(self.orientation)) * farthest_boundary + int(scaled_x)
        new_y =  int(scaled_y) - sin(rd(self.orientation)) * farthest_boundary

        #print 'j, windows_qty', j, windows_qty
        while (new_x > (j % windows_qty) * side_size and new_x < ((j % windows_qty)+1) * side_size and
                       new_y > int(j / windows_qty) * side_size and new_y < (int(j / windows_qty) + 1) * side_size):
            new_x = cos(rd(self.orientation)) * farthest_boundary + int(scaled_x)
            #line_ctrl = int(j / windows_qty) + 1
            new_y =  int(scaled_y) - sin(rd(self.orientation)) * farthest_boundary
            farthest_boundary += 2
            #print new_x, new_y, farthest_boundary
        pygame.draw.line(screen, color, (int(scaled_x), int(scaled_y)), (new_x, new_y), 3)
        angles = []
        for i in range(m):
            angles.append(resolution*i)
        for i in range(1, len(angles)):
            farthest_boundary = 10
            new_x = cos(rd(self.orientation + angles[i])) * farthest_boundary + int(scaled_x)
            new_y = int(scaled_y) - sin(rd(self.orientation + angles[i])) * farthest_boundary
            while (new_x > (j % windows_qty) * side_size and new_x < ((j % windows_qty) + 1) * side_size and
                           new_y > int(j / windows_qty) * side_size and new_y < (
                int(j / windows_qty) + 1) * side_size):
                new_x = cos(rd(self.orientation + angles[i])) * farthest_boundary + int(scaled_x)
                new_y = int(scaled_y) - sin(rd(self.orientation + angles[i])) * farthest_boundary
                farthest_boundary += 2
            if relation_ctrl[point] == "even":
                if i % 2 == 0:
                    pygame.draw.line(screen, color, (int(scaled_x), int(scaled_y)), (new_x,new_y), 1)
                else:
                    self.draw_dashed_line(screen, color, (int(scaled_x), int(scaled_y)), (int(new_x), int(new_y)))
            elif relation_ctrl[point] == "odd":
                if i % 2 == 0:
                    self.draw_dashed_line(screen, color, (int(scaled_x), int(scaled_y)), (int(new_x), int(new_y)))
                else:
                    pygame.draw.line(screen, color, (int(scaled_x), int(scaled_y)), (new_x,new_y), 1)
            else:
                pygame.draw.line(screen, color, (int(scaled_x), int(scaled_y)), (new_x,new_y), 1)


    def draw_orientation_star(self, color, point, scaled_x, scaled_y, window, windows_qty, x_bounds, y_bounds, relation_ctrl, m):
        i = 0
        px = 7. * cos(rd(360 - self.orientation)) + scaled_x
        py = 7. * sin(rd(360 - self.orientation)) + scaled_y
        pygame.draw.line(window, color, (int(scaled_x), int(scaled_y)), (int(px), int(py)), 1)
        pygame.draw.circle(window, color, (int(scaled_x), int(scaled_y)), 3, 0)
        self.draw_starvars(window, color, point, scaled_x, scaled_y, i, windows_qty,  x_bounds, y_bounds, relation_ctrl, m)



    def draw_orientation(self, color, scaled_x, scaled_y, window):
        px = 7. * cos(rd(360 - self.orientation)) + scaled_x
        py = 7. * sin(rd(360 - self.orientation)) + scaled_y
        pygame.draw.line(window, color, (int(scaled_x), int(scaled_y)), (int(px), int(py)), 1)
        pygame.draw.circle(window, color, (int(scaled_x), int(scaled_y)), 3, 0)

    def draw_without_orientation(self, color, scaled_x, scaled_y, window):
        pygame.draw.circle(window, color, (int(scaled_x), int(scaled_y)), 3, 0)

    def __repr__(self):
        return '[x= %.10s y= %.10s orient= %.10s weight= %.25s]\n' % (str(self.x), str(self.y), str(self.orientation), str(self.w))
