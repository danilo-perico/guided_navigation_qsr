#! /usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__project__ = "Probabilistic StarVars"
__file__ = "starvars_discretization.py"

###discretization of the orientation following StarVars
def starvars_discretization(vision_delta_orient, m, relation_ctrl = 2):
    angle = 360.0 / m
    vision_delta_orient = vision_delta_orient % 360
    vision_delta_orient = round(vision_delta_orient, 4)
    for i in range(0, m):
        if vision_delta_orient >= (i * angle) and vision_delta_orient < ((i+1)*angle):
            qualitative_region = i

    if relation_ctrl != 2:
        if relation_ctrl == 0: ### even regions:
            if qualitative_region % 2 == 1:
                qualitative_region = (qualitative_region - 1) % m
        else: ### odd regions
            if qualitative_region % 2 == 0:
                qualitative_region = (qualitative_region - 1) % m
    return qualitative_region
#
# def starvars_discretization_region_middle(vision_delta_orient, m):
#     angle = 360.0 / m
#     angle_middle = angle / 2
#     vision_delta_orient = vision_delta_orient % 360
#     qualitative_region = 0
#     for i in range(1, m):
#         if vision_delta_orient >= (i * angle - angle_middle) and vision_delta_orient < ((i+1)*angle - angle_middle):
#             qualitative_region = i
#     return qualitative_region
