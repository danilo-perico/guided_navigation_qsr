# !/usr/bin/env python
# coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

from math import exp
from math import pi
from math import degrees
from math import atan2
from particles import *
from starvars import *
from world_model import *
from oriented_point import *
import time

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

### necessary to show all numpy data during a print
np.set_printoptions(threshold='nan')
sys.path.append('../../..')
from Blackboard.src.SharedMemory import SharedMemory
from config import *

# instantiate configparser:
config = ConfigParser()
config.read('../../Control/Data/config.ini')
mem_key = int(config.get('Communication', 'no_player_robofei')) * 100
# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

class StarVarsReasoning:
    def __init__(self, background=None):
        self.model = None
        self.background = background
        self.particles_number_per_point = 1
        self.relations_by_mean = []
        self.x_bounds = [0., 0.]
        self.y_bounds = [0., 0.]
        self.screen_by_model_side_size = 0.
        self.windows_qty = 0
        self.relations = []
        self.starvars = None
        self.probability = []

        prob_starvars_config = Config()
        self.goal = prob_starvars_config.goal
        self.driven = prob_starvars_config.driven
        self.m = prob_starvars_config.m
        self.active_entities = prob_starvars_config.number_of_oriented_points - 1
        self.number_of_entities = prob_starvars_config.number_of_entities
        self.number_oriented_points = prob_starvars_config.number_of_oriented_points
        self.action = ''
        self.data_matrix = []
        self.orientation_driven_agent = 0
        print "StarVarsReasoning"

    def display_update(self):
        pygame.display.flip()

    def release_particles(self, reset = [False]):
        print 'release particles'
        for j in range(0, len(self.model.points)):
            if j == self.driven or j == self.goal:
                mean = [self.model.points[j].x, self.model.points[j].y]
                cov = [[0, 0.], [0., 0]]
                for k in range(0, self.particles_number_per_point):
                    particle = Particles()
                    relations = []
                    for l in range(0, len(self.model.points)):
                        if l != j and self.model.points[l].has_orientation != False and l != self.driven:
                            relations.append(int(self.relations[l][j]))
                        else:
                            relations.append('x')
                    relation_from_particle = []
                    new_relations = copy.copy(relations)

                    while cmp(relation_from_particle, new_relations) != 0:
                        new_relations = copy.copy(relations)
                        relation_from_particle = []
                        particle.x, particle.y = np.random.multivariate_normal(mean, cov).T
                        if self.model.points[j].has_orientation == False:
                            particle.orientation = []
                        else:
                            print "orientation_release", j, self.model.points[j].orientation
                            if self.model.points[j].orientation == -1 and reset[0] == False:
                                particle.orientation = random.gauss(random.randrange(0, 315, 45),
                                                                    particle.turn_noise)
                            elif self.model.points[j].orientation != -1 and reset[0] == False:
                                particle.orientation = random.gauss(self.model.points[j].orientation, particle.turn_noise)
                                print "particle.orientation", j, particle.orientation
                            else:
                                pass
                        for l in range(0, len(self.model.points)):
                            if l != j and self.model.points[l].has_orientation != False and l != self.driven:
                                relation_from_particle.append(self.get_qualitative_relation(
                                                                self.model.points[l].x,
                                                                self.model.points[l].y,
                                                                particle.x,
                                                                particle.y,
                                                                self.model.points[l].orientation))
                            else:
                                relation_from_particle.append('x')
                        original_indices = []
                        try:
                            original_indices.append(relations.index(-1))
                            for l in range(0, len(original_indices)):
                                relation_from_particle.pop(original_indices[l])
                                new_relations.pop(original_indices[l])
                        except:
                            pass
                    self.model.points[j].particles.append(particle)
            else:
                particle = Particles()
                mean = [self.model.points[j].x, self.model.points[j].y]
                cov = [[0., 0.], [0., 0.]]
                particle.x, particle.y = np.random.multivariate_normal(mean, cov).T
                if self.model.points[j].has_orientation != False:
                    particle.orientation = self.model.points[j].orientation
                else:
                    particle.orientation = []
                self.model.points[j].particles.append(particle)

    def min_max_particles(self):
        self.x_bounds = [0.,0.]
        self.y_bounds = [0., 0.]
        for j in range(0,len(self.model.points)):
            for k in range(0, len(self.model.points[j].particles)):
                if  self.x_bounds[1] < self.model.points[j].particles[k].x:
                    self.x_bounds[1] = self.model.points[j].particles[k].x
                if self.x_bounds[0] > self.model.points[j].particles[k].x:
                    self.x_bounds[0] = self.model.points[j].particles[k].x
                if self.y_bounds[1] < self.model.points[j].particles[k].y:
                    self.y_bounds[1] = self.model.points[j].particles[k].y
                if self.y_bounds[0] > self.model.points[j].particles[k].y:
                    self.y_bounds[0] = self.model.points[j].particles[k].y
        if self.x_bounds[1] > self.y_bounds[1]:
            self.y_bounds[1] = self.x_bounds[1]
        else:
            self.x_bounds[1] = self.y_bounds[1]
        if self.x_bounds[0] < self.y_bounds[0]:
            self.y_bounds[0] = self.x_bounds[0]
        else:
            self.x_bounds[0] = self.y_bounds[0]

    def scale(self, x, y):
        width, height = self.background.get_size()
        scaled_x = ((x + abs(self.x_bounds[0])) * (width)) / (self.x_bounds[1] - self.x_bounds[0])
        scaled_y = height - (((y + abs(self.y_bounds[0])) * (height-10)) / (self.y_bounds[1] - self.y_bounds[0]))
        return scaled_x, scaled_y

    def draw_particles(self):
        self.min_max_particles()
        # text
        font = pygame.font.SysFont("Arial", 15)
        textpos = self.scale(self.x_bounds[0], self.y_bounds[1])
        textpos = list(textpos)
        #for i in range(self.m):
        #    self.background.blit(font.render(str(i) + ' bel: {0:.2%}'.format(self.probability[i]), 1, (10, 10, 10)), textpos)
        #    textpos[1] = textpos[1] + 17

        textpos = self.scale(self.x_bounds[0], self.y_bounds[1])
        textpos = list(textpos)
        textpos[0] = textpos[0] + 200
        self.background.blit(font.render('Action:' + self.action, 1, (10, 10, 10)), textpos)

        for j in range(0, len(self.model.points)):
            for k in range(0, len(self.model.points[j].particles)):
                scaled_x, scaled_y = self.scale(self.model.points[j].particles[k].x, self.model.points[j].particles[k].y)
                if not self.model.points[j].particles[k].orientation == []:
                    if j == self.driven:
                        self.model.points[j].particles[k].draw_orientation(self.model.points[j].color, scaled_x, scaled_y,
                                                                 self.background)
                    else:
                        self.model.points[j].particles[k].draw_orientation_star(self.model.points[j].color,
                                                                               scaled_x, scaled_y,
                                                                               self.background, 1, self.x_bounds, self.y_bounds)
                else:
                    self.model.points[j].particles[k].draw_without_orientation(self.model.points[j].color, scaled_x, scaled_y,
                                                                         self.background)
        self.display_update()

    def mean(self):
        for j in range(0,len(self.model.points)):
            sumx = 0.
            sumy = 0.
            sumy_sin = 0.
            sumx_cos = 0.
            for k in range(0, len(self.model.points[j].particles)):
                sumx = self.model.points[j].particles[k].x + sumx
                sumy = self.model.points[j].particles[k].y + sumy
                if not self.model.points[j].particles[k].orientation == []:
                    sumy_sin = sumy_sin + sin(rd(self.model.points[j].particles[k].orientation))
                    sumx_cos = sumx_cos + cos(rd(self.model.points[j].particles[k].orientation))

            if len(self.model.points[j].particles) != 0:
                self.model.points[j].mean_orientation = degrees(atan2(sumy_sin, sumx_cos))
                self.model.points[j].mean_x = (sumx /  len(self.model.points[j].particles))
                self.model.points[j].mean_y = (sumy / len(self.model.points[j].particles))
                self.min_max_particles()
                scaled_mean_x, scaled_mean_y = self.scale(self.model.points[j].mean_x,self.model.points[j].mean_y)
                ## draw mean
                mean_color = list(self.model.points[j].color)
                mean_color = [l * 0.75 for l in mean_color]
                mean_color = map(int, mean_color)
                mean_color = tuple(mean_color)
                #pygame.draw.circle(self.background, mean_color, (int(scaled_mean_x), int(scaled_mean_y)), 5, 0)
                #if self.model.points[j].has_orientation == True:
                #    px = 10. * cos(rd(360 - self.model.points[j].mean_orientation)) + scaled_mean_x
                #    py = 10. * sin(rd(360 - self.model.points[j].mean_orientation)) + scaled_mean_y
                #    pygame.draw.line(self.background, mean_color, (int(scaled_mean_x), int(scaled_mean_y)),
                #                     (int(px), int(py)), 3)
        self.display_update()

    def get_qualitative_relation(self, x1, y1, x2, y2, orientation1):
        alpha = degrees(atan2((y2 - y1),(x2 - x1)))
        rotate = orientation1
        rotate = rotate % 360
        if rotate > 180 and rotate < 360:
            rotate = rotate - 360
        alpha = alpha - rotate
        if alpha > 180:
            alpha = alpha - 360
        elif alpha < -180:
            alpha = alpha + 360
        alpha = round(alpha, 4)
        alpha = alpha % 360
        if alpha >= 0.0 and alpha < 45.0:
            relation = 0
        elif alpha >= 45.0 and alpha < 90.0:
            relation = 1
        elif alpha >= 90.0 and alpha < 135.0:
            relation = 2
        elif alpha >= 135.0 and alpha < 180.0:
            relation = 3
        elif alpha >= 180.0 and alpha < 225.0:
            relation = 4
        elif alpha >= 225.0 and alpha < 270.0:
            relation = 5
        elif alpha >= 270.0 and alpha < 315.0:
            relation = 6
        else:
            relation = 7
        return relation

    def qualitative_command(self, probabilistic = True):
        correct_answers = 0
        print "qualitative_command - self.relations", self.relations
        for i in range(0, len(self.relations)):
            if i != self.driven:
                if self.relations[i][self.driven] == self.relations[i][self.goal]:
                    correct_answers += 1

        if correct_answers == (len(self.relations)) - 1:
            print 'class Particle_Filter says: '
            self.action = 'goal_region_achieved'
            return 'goal_region_achieved'

        if probabilistic == True:
            driven_to_goal = np.argmax(np.array(self.probability))

            print driven_to_goal
        else:
            driven_to_goal = int(self.relations[self.driven][self.goal])

        if driven_to_goal == 0 or driven_to_goal == 7:
            print 'class Particle_Filter says: '
            self.action = 'go_forward'
            print 'go_forward'
            return 'go_forward'
        elif driven_to_goal == 1 or driven_to_goal == 2:
            print 'class Particle_Filter says: '
            self.action = 'turn_left_and_walk_forward'
            print 'turn_left_and_walk_forward'
            return 'turn_left_and_walk_forward'
        elif driven_to_goal == 3 or driven_to_goal == 4:
            print 'class Particle_Filter says: '
            self.action = 'turn_back_and_walk_forward'
            print 'turn_back_and_walk_forward'
            return 'turn_back_and_walk_forward'
        elif driven_to_goal == 5 or driven_to_goal == 6:
            print 'class Particle_Filter says: '
            self.action = 'turn_right_and_walk_forward'
            print 'turn_right_and_walk_forward'
            return 'turn_right_and_walk_forward'

    def sense(self, reset = [False]):
        try:
            relations = [line.strip() for line in open("relations.dat", 'r')]
        except:
            relations = [line.strip() for line in open("../../prob_starvars/src/relations.dat", 'r')]

        split_data = []

        if reset[0] is True:
            self.model = None

        ###spliting received string
        for i in range(0, len(relations)):
            split_data.append(relations[i].split())
        for i in range(0, len(split_data)):
            split_data[i] = map(float, split_data[i])
            split_data[i] = map(int, split_data[i])

        self.data_matrix = np.array(split_data)

        print 'class ParticleFilter says:'
        print 'self.data_matrix'
        print self.data_matrix

        ### get initial orientation from driven agent ###
        orientation_driven_agent_filter = []
        driven_agent_data = self.data_matrix[np.where(self.data_matrix[:, 0] == self.driven)]
        for i in range(len(driven_agent_data)):
           orientation_driven_agent_filter.append(driven_agent_data[i][1])
           self.orientation_driven_agent = max(set(orientation_driven_agent_filter), key= orientation_driven_agent_filter.count)

        print "self.model", self.model

        if self.model is None:
            #if self.model is None:
            h = -1.
        else:
            ### remove driven agent from main matrix ###
            data_matrix_out_driven = self.data_matrix[np.where(self.data_matrix[:, 0] != self.driven)]
            print
            print 'without the driven agent'
            print data_matrix_out_driven
            self.data_matrix = data_matrix_out_driven
            ############################################

            print self.data_matrix
            for i in range(0, len(self.model.points)):
                for j in range(0, len(self.model.points)):
                    if i != j and j != self.driven and i != self.goal and i != self.driven:
                        retrieved_relation = self.get_qualitative_relation(
                                                        self.model.points[i].mean_x,
                                                        self.model.points[i].mean_y,
                                                        self.model.points[j].mean_x,
                                                        self.model.points[j].mean_y,
                                                        self.model.points[i].mean_orientation)
                        retrieved_data = [i, self.model.points[i].particles[0].orientation, retrieved_relation, retrieved_relation, j]
                        retrieved_data = np.array([retrieved_data])
                        self.data_matrix = np.concatenate((self.data_matrix, retrieved_data))
                    elif i == self.driven and i != j and j != self.driven and i != self.goal:
                        retrieved_data = [i, self.orientation_driven_agent, -1, -1, j]
                        retrieved_data = np.array([retrieved_data])
                        self.data_matrix = np.concatenate((self.data_matrix, retrieved_data))

            self.data_matrix = np.asarray(self.data_matrix, dtype=int)

            print "new data matrix"
            print self.data_matrix

            h = -1.
            self.starvars.h_ctrl = 0

        #self.model = None
        self.starvars = StarVars()

        loopnum = self.starvars.data_pre_processing(self.data_matrix)
        print 'loopnum', loopnum

        self.relations = self.starvars.overall_relations
        print "h", h
        self.starvars.Recursive_For([], loopnum, h)
        orientations, xy, self.relations = self.starvars.getAnswer()
        # print hex(id(self.relations))
        print 'class Particle_Filter says: '
        print '====== StarVars ======'
        print 'self.relations:'
        print self.relations
        print 'xy:'
        print xy
        print 'orientations:'
        print orientations
        print '======================'
        try:
            number_entities = len(xy[0]) / 2
            print "number entities", number_entities
            points = []
            for i in range(0, number_entities):
                points.append(OrientedPoint(i))
                points[i].x = xy[0][i][0]
                points[i].y = xy[0][i + number_entities][0]
                if i < self.number_oriented_points:
                    if i == self.driven and self.orientation_driven_agent != -1:
                        print "self.orientation_driven_agent", self.orientation_driven_agent
                        points[i].orientation = self.orientation_driven_agent
                    else:
                        points[i].orientation = orientations[0][i]
                else:
                    points[i].has_orientation = False
                    points[i].orientation = []

            print 'class Particle_Filter says: '
            print '== Success! ==========================================='
            print 'StarVars has found a feasible answer for the problem'
            print '======================================================='

            #if self.model is None:
            self.model = WorldModel(points)
            print 'class ParticleFilter says: '
            print self.model
            return True
            #else:
            #    self.updated_model = WorldModel(points)
            #    print 'class ParticleFilter says: '
            #    print self.updated_model

        except:
            return False
            print 'class Particle_Filter says: '
            print '== Error! ============================================='
            print 'A feasible StarVars answer was NOT found!'
            print '======================================================='


    def reasoning(self, reset, ctrl = 0):
        if self.sense(reset):
            self.release_particles([False])
            self.mean()
            action = self.qualitative_command(False)
            self.draw_particles()
            reset[0] = False
        else:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 11)

        self.background.fill((240, 240, 240))
        time.sleep(1)

        if action == 'go_forward':
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 1)
            bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'turn_left_and_walk_forward':
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 2)
            bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'turn_right_and_walk_forward':
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 3)
            bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'turn_back_and_walk_forward':
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 4)
            bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'goal_region_achieved':
            print 'automatic_prob_starvars says: '
            print 'goal achieved!'
            print 'FINISH'
            bkb.write_int(mem, 'REASONING_COMPLETED', 1)
            bkb.write_int(mem, 'ENVIRONMENT_SETUP', 1)
            return True

        else:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 11)
            print 'Fail'
            print 'Resetting StarVars'
            reset[0] = True
            ctrl = 0
            return False
