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
sys.path.append('../..')
from Blackboard.src.SharedMemory import SharedMemory
from config import *
prob_starvars_config = Config()

# instantiate configparser:
config = ConfigParser()
config.read('../../Control/Data/config.ini')
mem_key = int(config.get('Communication', 'no_player_robofei')) * 100
# Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

### necessary to show all numpy data during a print
np.set_printoptions(threshold='nan')
sys.path.append('../../..')


class ProbStarVarsReasoning:
    def __init__(self, background=None):
        self.model = None
        self.updated_model = None
        self.background = background
        #self.particles_number_per_point = 50
        self.max_number_of_particles = 10000
        self.min_number_of_particles = 100
        #self.sigma_xy_spread = 3.0
        self.sigma_xy_update = 0.1
        self.sigma_orient = 7.5
        self.turn = 90
        self.forward = 0.01
        self.relations_by_mean = []
        self.x_bounds = [0., 0.]
        self.y_bounds = [0., 0.]
        self.x_bounds_points = [0., 0.]
        self.y_bounds_points = [0., 0.]
        self.screen_by_model_side_size = 0.
        self.windows_qty = 0
        self.relations = []
        self.starvars = None
        self.number_of_possible_answers = 0
        self.probability = []
        self.relations_to_goal = []
        self.relations_to_driven = []
        self.goal_achieved = False

        config = Config()
        self.goal = config.goal
        self.driven = config.driven
        self.m = config.m
        self.active_entities = config.number_of_oriented_points - 1
        self.number_of_entities = config.number_of_entities
        self.number_oriented_points = config.number_of_oriented_points
        self.action = ''
        self.data_matrix = []
        self.relation_ctrl = self.number_of_entities * ["complete"]
        self.orientation_driven_agent = 0

    def display_update(self):
        pygame.display.flip()

    def gaussian(self, mu, sigma, x):
        ## calculates the probability of x for 1-dim Gaussian with mean mu and var sigma
        return exp(- ((mu - x) ** 2) / (sigma ** 2) / 2.0) / sqrt(2.0 * pi * (sigma ** 2))

    def euclidean_distance(self, u, v):
        ## calculates the euclidean distance between two vectors made of qualitative regions (particle and new measurement)
        square_sum = 0.
        for i in range(0, len(u)):
            square_sum += ((u[i] - v[i]) ** 2)
        return sqrt(square_sum)

    def release_particles(self, reset = [False]):
        print 'release particles'
        self.min_max_points()
        self.x_bounds_points, self.y_bounds_points
        for j in range(0, len(self.model.points)):
            if j == self.driven or j == self.goal:
                for k in range(0, self.max_number_of_particles):
                    particle = Particles()
                    particle.x = random.uniform(self.x_bounds_points[0]-1, self.x_bounds_points[1]+1)
                    particle.y = random.uniform(self.y_bounds_points[0]-1, self.y_bounds_points[1]+1)
                    if self.model.points[j].has_orientation == False:
                        particle.orientation = []
                    else:
                        if self.model.points[j].orientation == -1 and reset[0] == False:
                            particle.orientation = random.gauss(random.randrange(0, 360, 360/self.m),
                                                                 particle.turn_noise)
                        elif self.model.points[j].orientation != -1:
                            particle.orientation = random.gauss(self.model.points[j].orientation, particle.turn_noise)
                        else:
                            pass
                    self.model.points[j].particles.append(particle)
                    self.updated_model = self.model
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
        self.x_bounds = [0., 0.]
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


    def min_max_points(self):
        self.x_bounds_points = [0., 0.]
        self.y_bounds_points = [0., 0.]
        for j in range(0,len(self.model.points)):
            if  self.x_bounds_points[1] < self.model.points[j].x:
                self.x_bounds_points[1] = self.model.points[j].x
            if self.x_bounds_points[0] > self.model.points[j].x:
                self.x_bounds_points[0] = self.model.points[j].x
            if self.y_bounds_points[1] < self.model.points[j].y:
                self.y_bounds_points[1] = self.model.points[j].y
            if self.y_bounds_points[0] > self.model.points[j].y:
                self.y_bounds_points[0] = self.model.points[j].y


    def scale(self, x, y):
        width, height = self.background.get_size()
        scaled_x = 20 + ((x - self.x_bounds[0]) * (width-40) / (self.x_bounds[1] - self.x_bounds[0]))
        scaled_y = height - (20 + (((y + abs(self.y_bounds[0])) * (height-40)) / (self.y_bounds[1] - self.y_bounds[0])))
        return scaled_x, scaled_y


    def draw_particles(self):
        self.min_max_particles()
        for j in range(0, len(self.model.points)):
            for k in range(0, len(self.model.points[j].particles)):
                scaled_x, scaled_y = self.scale(self.model.points[j].particles[k].x, self.model.points[j].particles[k].y)
                if not self.model.points[j].particles[k].orientation == []:
                    if j == self.driven:
                        self.model.points[j].particles[k].draw_orientation(self.model.points[j].color, scaled_x, scaled_y,
                                                                 self.background)
                    else:
                        self.model.points[j].particles[k].draw_orientation_star(self.model.points[j].color, j,
                                                                               scaled_x, scaled_y,
                                                                               self.background, 1, self.x_bounds, self.y_bounds, self.relation_ctrl, self.m)
                else:
                    self.model.points[j].particles[k].draw_without_orientation(self.model.points[j].color, scaled_x, scaled_y,
                                                                         self.background)
        try:
            # font = pygame.font.SysFont("Arial", 15)
            # textpos = self.scale(self.x_bounds[0], self.y_bounds[1])
            # textpos = list(textpos)
            # for i in range(self.m):
            #     self.background.blit(font.render(str(i) + ' bel: {0:.2%}'.format(self.probability[i]), 1, (10, 10, 10)), textpos)
            #     textpos[1] = textpos[1] + 17

            textpos = self.scale(self.x_bounds[0], self.y_bounds[1])
            textpos = list(textpos)
            textpos[0] = textpos[0] + 200
            self.background.blit(font.render('Action:' + self.action, 1, (10, 10, 10)), textpos)
        except:
            pass
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

            if  len(self.model.points[j].particles) != 0:
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
                pygame.draw.circle(self.background, mean_color, (int(scaled_mean_x), int(scaled_mean_y)), 5, 0)
                if self.model.points[j].has_orientation == True:
                    px = 10. * cos(rd(360 - self.model.points[j].mean_orientation)) + scaled_mean_x
                    py = 10. * sin(rd(360 - self.model.points[j].mean_orientation)) + scaled_mean_y
                    pygame.draw.line(self.background, mean_color, (int(scaled_mean_x), int(scaled_mean_y)),
                                     (int(px), int(py)), 3)
        self.display_update()


    def get_qualitative_relation(self, x1, y1, x2, y2, orientation1, relation_ctrl = "complete"):
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
        alpha = alpha % 360
        alpha = round(alpha, 4)
        angle = 360.0 / self.m

        for i in range(0, self.m):
            if alpha >= (i * angle) and alpha < ((i+1)*angle):
                qualitative_region = i

        if relation_ctrl != "complete":
            if relation_ctrl == "even": ### even regions:
                if qualitative_region % 2 == 1:
                    qualitative_region = (qualitative_region - 1) % self.m
            elif relation_ctrl == "odd": ### odd regions
                if qualitative_region % 2 == 0:
                    qualitative_region = (qualitative_region - 1) % self.m
        return qualitative_region


    def answers_probability(self):
        answers_probability = [0] * self.m
        correct_answers = 0
        for j in range(0, len(self.model.points[self.driven].particles)):
            particle_relation_to_goal = self.get_qualitative_relation(
                self.model.points[self.driven].particles[j].x,
                self.model.points[self.driven].particles[j].y,
                self.model.points[self.goal].mean_x,
                self.model.points[self.goal].mean_y,
                self.model.points[self.driven].particles[j].orientation, "complete")

            # particle_relations = []
            # for i in range(0, len(self.model.points)):
            #     particle_relations.append(self.get_qualitative_relation(
            #         self.model.points[i].mean_x,
            #         self.model.points[i].mean_y,
            #         self.model.points[self.driven].particles[j].x,
            #         self.model.points[self.driven].particles[j].y,
            #         self.model.points[i].mean_orientation, "complete"))
            #
            # if self.relations_to_goal == particle_relations:
            #     correct_answers += 1

            answers_probability[particle_relation_to_goal] += 1
        self.probability = map(lambda x: float(x)/len(self.model.points[self.driven].particles), answers_probability)


    def qualitative_command(self, probabilistic = True):
        # if self.goal_achieved == True:
        #     print 'class Particle_Filter says: '
        #     self.action = 'goal_region_achieved'
        #     return 'goal_region_achieved'
        # else:
        var = self.m / 8
        left = 0
        right = 0
        front = 0
        back = 0

        if probabilistic == True:
            for i in range(len(self.probability)):
                if i >= (1 * var) and i < (3 * var):
                    left += self.probability[i]
                elif i >= (3 * var) and i < (5 * var):
                    back += self.probability[i]
                elif i >= (5 * var) and i < (7 * var):
                    right += self.probability[i]
                else:
                    front += self.probability[i]

        qualitative_relation_probability = [front,left,back,right]
        driven_to_goal = np.argmax(np.array(qualitative_relation_probability))

        print '&&&&& qualitative_relation_probability &&&&&&&'
        print qualitative_relation_probability

        if driven_to_goal == 1:
            print 'class Particle_Filter says: '
            self.action = 'turn_left_and_walk_forward'
            print 'turn_left_and_walk_forward'
            return 'turn_left_and_walk_forward'
        elif driven_to_goal == 2:
            print 'class Particle_Filter says: '
            self.action = 'turn_back_and_walk_forward'
            print 'turn_back_and_walk_forward'
            return 'turn_back_and_walk_forward'
        elif driven_to_goal == 3:
            print 'class Particle_Filter says: '
            self.action = 'turn_right_and_walk_forward'
            print 'turn_right_and_walk_forward'
            return 'turn_right_and_walk_forward'
        else:
            print 'class Particle_Filter says: '
            self.action = 'go_forward'
            print 'go_forward'
            return 'go_forward'


    def decide_update_sense(self):
        try:
            relations = [line.strip() for line in open("relations.dat", 'r')]
        except:
            relations = [line.strip() for line in open("../../prob_starvars/src/relations.dat", 'r')]
        split_data = []
        ###spliting received string
        for i in range(0, len(relations)):
            split_data.append(relations[i].split())
        for i in range(0, len(split_data)):
            split_data[i] = map(float, split_data[i])
            split_data[i] = map(int, split_data[i])

        self.data_matrix = np.array(split_data)

        ### get orientation from driven agent ###
        orientation_driven_agent_filter = []
        driven_agent_data = self.data_matrix[np.where(self.data_matrix[:, 0] == self.driven)]
        for i in range(len(driven_agent_data)):
           orientation_driven_agent_filter.append(driven_agent_data[i][1])
           self.orientation_driven_agent = max(set(orientation_driven_agent_filter), key= orientation_driven_agent_filter.count)

        ### remove driven agent from main matrix ###
        data_matrix_out_driven = self.data_matrix[np.where(self.data_matrix[:, 0] != self.driven)]
        self.data_matrix = data_matrix_out_driven

        self.relations_to_driven = []
        driven_data = self.data_matrix[np.where(self.data_matrix[:, 5] == self.driven)]
        driven_data = sorted(driven_data, key=lambda x: x[0])
        for i in range(len(driven_data)):
            self.relations_to_driven.append(driven_data[i][4])

        print "self.data_matrix"
        print self.data_matrix

        if self.model is None:
            self.relations_to_goal = []
            goal_data = self.data_matrix[np.where(self.data_matrix[:, 5] == self.goal)]
            goal_data = sorted(goal_data, key=lambda x: x[0])
            for i in range(len(goal_data)):
                self.relations_to_goal.append(goal_data[i][4])
        else:
            driven_agent_data = self.data_matrix[np.where(self.data_matrix[:, 5] == self.driven)]
            driven_agent_data = sorted(driven_agent_data, key=lambda x: x[0])
            for i in range(self.number_of_entities):
                try:
                    if driven_agent_data[i][2] != driven_agent_data[i][3]:
                        if (driven_agent_data[i][2] == 0 and driven_agent_data[i][3] == 15) or (driven_agent_data[i][2] == 15 and driven_agent_data[i][3] == 0):
                            line = 0
                        else:
                            line = max(driven_agent_data[i][2], driven_agent_data[i][3])
                        print "cruzou na linha ", line
                        print "deve atualizar as regioes ",  driven_agent_data[i][2], driven_agent_data[i][3]
                        if line % 2 == 0: #even
                            self.relation_ctrl[i] = "odd" #odd
                        else:
                            self.relation_ctrl[i] = "even" #even
                    else:
                        self.relation_ctrl[i] = "complete"
                except:
                    self.relation_ctrl[i] = "complete"

            print '==== self.relation_ctrl ====', self.relation_ctrl

            for i in range(0, len(self.model.points)):
                for j in range(0, len(self.model.points)):
                    if i != j and j != self.driven and i != self.driven and i != self.goal:
                        retrieved_relation = self.get_qualitative_relation(
                                                        self.model.points[i].mean_x,
                                                        self.model.points[i].mean_y,
                                                        self.model.points[j].mean_x,
                                                        self.model.points[j].mean_y,
                                                        self.model.points[i].mean_orientation, "complete")
                        retrieved_data = [i, self.model.points[i].particles[0].orientation, retrieved_relation, retrieved_relation, retrieved_relation, j]
                        retrieved_data = np.array([retrieved_data])
                        self.data_matrix = np.concatenate((self.data_matrix, retrieved_data))
            print "new data matrix"
            print self.data_matrix

        print 'GOAL DATA', self.relations_to_goal
        print 'DRIVEN DATA', self.relations_to_driven

        #if self.relations_to_goal == self.relations_to_driven:
        #    self.goal_achieved = True
        #else:
        #    self.goal_achieved = False


    def sense(self, reset = [False]):
        self.starvars = StarVars(self.model)
        if self.model is None:
            h = -1.
        else:
            h = -0.01
            self.starvars.h_ctrl = 1

        loopnum = self.starvars.data_pre_processing(self.data_matrix)
        #print 'loopnum', loopnum
        self.relations = self.starvars.overall_relations
        self.starvars.Recursive_For([], loopnum, h)
        orientations, xy, self.relations = self.starvars.getAnswer()

        #print 'class Particle_Filter says: '
        print '====== StarVars ======'
        print self.relations
        print xy
        print orientations
        print '======================'
        try:
            number_entities = len(xy[0]) / 2
            #print "number entities", number_entities
            points = []
            for i in range(0, number_entities):
                points.append(OrientedPoint(i))
                points[i].x = xy[0][i][0]
                points[i].y = xy[0][i + number_entities][0]
                if i < self.number_oriented_points:
                    if i == self.driven:
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

            if self.model is None:
                self.model = WorldModel(points)
                print self.model
            else:
                self.updated_model = WorldModel(points)
                print self.updated_model
            return True
        except:
            print 'class Particle_Filter says: '
            print '== Error! ============================================='
            print 'A feasible StarVars answer was NOT found!'
            print '======================================================='
            return False


    def move(self, entity, action):
        ctrl_total_per_trial = 1000
        for j in range(0, len(self.model.points[entity].particles)):
            if action == 'turn_left':
                self.model.points[entity].particles[j].orientation = (self.model.points[entity].particles[
                                                                              j].orientation + self.turn +
                                                                          random.gauss(0.0, self.model.points[
                                                                              entity].particles[j].turn_noise)
                                                                          ) % 360
                self.model.points[entity].particles[j].x = self.model.points[entity].particles[j].x + (
                cos(rd(self.model.points[entity].particles[j].orientation)) * self.model.points[entity].particles[j].forward_noise)
                self.model.points[entity].particles[j].y = self.model.points[entity].particles[j].y + (
                sin(rd(self.model.points[entity].particles[j].orientation)) * self.model.points[entity].particles[j].forward_noise)

            elif action == 'turn_right':
                self.model.points[entity].particles[j].orientation = (self.model.points[entity].particles[
                                                                              j].orientation - self.turn +
                                                                          random.gauss(0.0, self.model.points[
                                                                              entity].particles[j].turn_noise)
                                                                          ) % 360
                self.model.points[entity].particles[j].x = self.model.points[entity].particles[j].x + (
                cos(rd(self.model.points[entity].particles[j].orientation)) * self.model.points[entity].particles[j].forward_noise)
                self.model.points[entity].particles[j].y = self.model.points[entity].particles[j].y + (
                sin(rd(self.model.points[entity].particles[j].orientation)) * self.model.points[entity].particles[j].forward_noise)
            else:
                relation_ctrl = copy.deepcopy(self.relation_ctrl)
                epsilon1 = 30 ### rate (%) of particles that are going to be moved at the same place
                rand = random.randint(0, 100)
                if rand < epsilon1:
                    continue

                relation = []
                for k in range(0, len(self.model.points)):
                    if entity != k and self.model.points[k].has_orientation != False:
                        relation.append(self.get_qualitative_relation(self.model.points[k].x,
                                                                      self.model.points[k].y,
                                                                      self.model.points[entity].particles[j].x,
                                                                      self.model.points[entity].particles[j].y,
                                                                      self.model.points[k].orientation, relation_ctrl[k]))
                    elif entity == k:
                        relation.append('x')

                new_relation = copy.copy(relation)
                ctrl = 0
                self.model.points[entity].particles[j].orientation = (self.model.points[entity].particles[
                                                                                 j].orientation +
                                                                          random.gauss(0.0, self.model.points[
                                                                          entity].particles[j].turn_noise)) % 360
                while cmp(new_relation, relation) == 0 and ctrl <= ctrl_total_per_trial:
                    self.model.points[entity].particles[j].out_of_fov = False
                    new_relation = []
                    ctrl += 1
                    if ctrl >= ctrl_total_per_trial:
                        self.model.points[entity].particles[j].out_of_fov = True
                    #print self.models[i].points[entity].particles[j]
                    ## move, and add randomness to the motion command
                    dist = float(self.forward)
                    self.model.points[entity].particles[j].x = self.model.points[entity].particles[j].x + (
                    cos(rd(self.model.points[entity].particles[j].orientation)) * dist)
                    self.model.points[entity].particles[j].y = self.model.points[entity].particles[j].y + (
                    sin(rd(self.model.points[entity].particles[j].orientation)) * dist)

                    for k in range(0, len(self.model.points)):
                        if entity != k and self.model.points[k].has_orientation != False:
                            new_relation.append(self.get_qualitative_relation(self.model.points[k].x,
                                                                              self.model.points[k].y,
                                                                              self.model.points[
                                                                                  entity].particles[j].x,
                                                                               self.model.points[
                                                                                  entity].particles[j].y,
                                                                              self.model.points[
                                                                                  k].orientation, relation_ctrl[k]))
                        elif entity == k:
                            new_relation.append('x')

                ### a % of particles to go to the next region
                relation = []
                changed_particles_index = []
                epsilon = 10 ### rate (%) of particles that are going to be moved to one more region
                if random.randint(0, 100) < epsilon:
                    for k in range(0, len(self.model.points)):
                         if entity != k and self.model.points[k].has_orientation is not False:
                             relation.append(self.get_qualitative_relation(self.model.points[k].x,
                                                                           self.model.points[k].y,
                                                                           self.model.points[entity].particles[j].x,
                                                                           self.model.points[entity].particles[j].y,
                                                                           self.model.points[k].orientation, 2))
                         elif entity == k:
                             relation.append('x')

                    new_relation = copy.deepcopy(relation)

                    ctrl = 0
                    while cmp(new_relation, relation) == 0 and ctrl <= ctrl_total_per_trial:
                        new_relation = []
                        ctrl += 1
                        ## move, and add randomness to the motion command
                        dist = float(self.forward)
                        self.model.points[entity].particles[j].x = self.model.points[entity].particles[j].x + (
                             cos(rd(self.model.points[entity].particles[j].orientation)) * dist)
                        self.model.points[entity].particles[j].y = self.model.points[entity].particles[j].y + (
                             sin(rd(self.model.points[entity].particles[j].orientation)) * dist)

                        for k in range(0, len(self.model.points)):
                            if entity != k and self.model.points[k].has_orientation != False:
                                new_relation.append(self.get_qualitative_relation(self.model.points[k].x,
                                                                                   self.model.points[k].y,
                                                                                   self.model.points[
                                                                                       entity].particles[j].x,
                                                                                   self.model.points[
                                                                                       entity].particles[j].y,
                                                                                   self.model.points[k].orientation, 2))
                            elif entity == k:
                                 new_relation.append('x')


    def measurement_prob(self, entity):
        ## compare the new models with particles from the old models and gibe weights for all particles
        relation_point_model = []
        for j in range(0, len(self.model.points)):
            if entity != j and j != self.driven and self.model.points[j].has_orientation != False:
                relation_point_model.append(self.get_qualitative_relation(self.model.points[j].x,
                                                            self.model.points[j].y,
                                                            self.updated_model.points[entity].x,
                                                            self.updated_model.points[entity].y,
                                                            self.updated_model.points[j].orientation, self.relation_ctrl[j]))

        print "relation_point_model", relation_point_model
        for k in range(0, len(self.model.points[entity].particles)):
            self.model.points[entity].particles[k].w = 0.
            relation_particle = []
            for j in range(0, len(self.model.points)):
                if entity != j and j != self.driven and self.model.points[j].has_orientation != False:
                    relation_particle.append(self.get_qualitative_relation(self.model.points[j].x,
                                                                  self.model.points[j].y,
                                                                  self.model.points[entity].particles[k].x,
                                                                  self.model.points[entity].particles[k].y,
                                                                  self.model.points[j].orientation, self.relation_ctrl[j]))

                    #print "relation_particle", relation_particle
            self.model.points[entity].particles[k].w = self.gaussian(0., self.sigma_xy_update, self.euclidean_distance(relation_particle, relation_point_model))

        self.model.points[entity].particles.sort(key=lambda x: x.w, reverse=True)

        self.model.points[entity].particles =  self.model.points[entity].particles[:self.min_number_of_particles]

        print 'particles', self.model.points[entity].particles
        random.shuffle(self.model.points[entity].particles)

        w_total = len(self.model.points[entity].particles) * [0]
        for k in range(len(w_total)):
            if k == 0:
                w_total[k] = self.model.points[entity].particles[k].w
            else:
                w_total[k] = w_total[k - 1] + self.model.points[entity].particles[k].w
        original_step = w_total[-1] / len(w_total)
        step = original_step
        temp_particles = []
        i = 0
        j = 0
        while i < len(w_total):
            if j < len(w_total):
                if w_total[j] >= step:
                    temp_particles.append(copy.deepcopy(self.model.points[entity].particles[j]))
                    step = step + original_step
                    i += 1
                else:
                    j += 1
            else:
                temp_particles.append(copy.deepcopy(self.model.points[entity].particles[i]))
                i += 1
        self.model.points[entity].particles = temp_particles
        self.model.points[entity].particles.sort(key=lambda x: x.w)

        ### sensor resetting
        for k in range(self.m):
            self.model.points[entity].particles[k].x = self.updated_model.points[entity].x
            self.model.points[entity].particles[k].y = self.updated_model.points[entity].y
            self.model.points[entity].particles[k].orientation = k*360/self.m

    def reasoning(self, reset, finish, ctrl = 0):
        if finish == 0:
            self.decide_update_sense()
            if self.sense(reset):
                pass
            else:
               bkb.write_int(mem, 'CONTROL_MESSAGES', 11)
               print 'reasoning method Fail'
               print 'Resetting StarVars'
               reset[0] = True
               ctrl = 0
               return False

            if ctrl == 0:
                self.release_particles()
                self.measurement_prob(self.driven)
                self.measurement_prob(self.goal)
            else:
                self.measurement_prob(self.driven)

            #raw_input('wait')
            time.sleep(1)
            self.mean()
            self.answers_probability()
            action = self.qualitative_command(True)
            self.draw_particles()

            self.background.fill((240, 240, 240))
            time.sleep(2)

            if action == 'go_forward':
                self.move(prob_starvars_config.driven, action)
                self.draw_particles()
                self.mean()
                bkb.write_int(mem, 'COM_ACTION_ROBOT1', 1)
                bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
                return False

            elif action == 'turn_left_and_walk_forward':
                self.move(prob_starvars_config.driven, 'turn_left')
                self.move(prob_starvars_config.driven, 'go_forward')
                self.draw_particles()
                self.mean()
                bkb.write_int(mem, 'COM_ACTION_ROBOT1', 2)
                bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
                return False

            elif action == 'turn_right_and_walk_forward':
                self.move(prob_starvars_config.driven, 'turn_right')
                self.move(prob_starvars_config.driven, 'go_forward')
                self.draw_particles()
                self.mean()
                bkb.write_int(mem, 'COM_ACTION_ROBOT1', 3)
                bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
                return False

            elif action == 'turn_back_and_walk_forward':
                self.move(prob_starvars_config.driven, 'turn_left')
                self.move(prob_starvars_config.driven, 'turn_left')
                self.move(prob_starvars_config.driven, 'go_forward')
                self.draw_particles()
                self.mean()
                bkb.write_int(mem, 'COM_ACTION_ROBOT1', 4)
                bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
                return False

            else:
                bkb.write_int(mem, 'CONTROL_MESSAGES', 11)
                print 'Fail'
                print 'Resetting StarVars'
                reset[0] = True
                ctrl = 0
                return False
        else:
                print 'goal achieved!'
                print 'FINISH'
                bkb.write_int(mem, 'REASONING_COMPLETED', 1)
                bkb.write_int(mem, 'ENVIRONMENT_SETUP', 1)
                return True
