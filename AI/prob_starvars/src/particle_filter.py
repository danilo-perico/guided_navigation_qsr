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

### necessary to show all numpy data during a print
np.set_printoptions(threshold='nan')
sys.path.append('../../..')
from config import *

class StarVarsReasoning:
    def __init__(self, background=None):
        self.model = None
        self.updated_model = None
        self.background = background
        self.particles_number_per_point = 1
        # vision max distance
        self.sigma_xy_spread = 0.0
        self.sigma_xy_update = 0.0
        self.sigma_orient = 0.0
        self.turn = 90
        self.forward = 0.01
        self.relations_by_mean = []
        self.x_bounds = [0., 0.]
        self.y_bounds = [0., 0.]
        self.screen_by_model_side_size = 0.
        self.windows_qty = 0
        self.relations = []
        self.starvars = None
        self.number_of_possible_answers = 0
        self.probability = []

        config = Config()
        self.goal = config.goal
        self.driven = config.driven
        self.m = config.m
        self.active_entities = config.number_of_oriented_points - 1
        self.number_of_entities = config.number_of_entities
        self.number_oriented_points = config.number_of_oriented_points
        self.action = ''
        self.data_matrix = []
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

    def release_particles(self, reset = False):
        print 'release particles'

        for j in range(0, len(self.model.points)):
            if j == self.driven or j == self.goal:
                mean = [self.model.points[j].x, self.model.points[j].y]
                cov = [[self.sigma_xy_spread, 0.], [0., self.sigma_xy_spread]]
                #cov = [[0, 0.], [0., 0]]
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
                            if self.model.points[j].orientation == -1 and reset == False:
                                particle.orientation = random.gauss(random.randrange(0, 315, 45),
                                                                    particle.turn_noise)
                            elif self.model.points[j].orientation != -1 and reset == False:
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

    def answers_probability(self):
        answers_probability = [0] * self.m

        for j in range(0, len(self.model.points[self.driven].particles)):
            relation_to_goal = self.get_qualitative_relation(
                self.model.points[self.driven].particles[j].x,
                self.model.points[self.driven].particles[j].y,
                self.model.points[self.goal].mean_x,
                self.model.points[self.goal].mean_y,
                self.model.points[self.driven].particles[j].orientation)

            answers_probability[relation_to_goal] += 1
        print 'probability', answers_probability

        self.probability = map(lambda x: float(x)/self.particles_number_per_point, answers_probability)
        print 'probability', self.probability


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


    def sense(self, reset = False):

        try:
            relations = [line.strip() for line in open("relations.dat", 'r')]
        except:
            relations = [line.strip() for line in open("../../prob_starvars/src/relations.dat", 'r')]

        split_data = []

        if reset:
            self.model = None

        ###spliting received string
        for i in range(0, len(relations)):
            split_data.append(relations[i].split())
        for i in range(0, len(split_data)):
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

            print "data_matrix_else"
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
            #else:
            #    self.updated_model = WorldModel(points)
            #    print 'class ParticleFilter says: '
            #    print self.updated_model

        except:
            print 'class Particle_Filter says: '
            print '== Error! ============================================='
            print 'A feasible StarVars answer was NOT found!'
            print '======================================================='

    def move(self, entity, action):
        ctrl_total_per_trial = 300
        for j in range(0, len(self.model.points[entity].particles)):
            if action == 'turn_left':
                self.model.points[entity].particles[j].orientation = (self.model.points[entity].particles[
                                                                              j].orientation + self.turn +
                                                                          random.gauss(0.0, self.model.points[
                                                                              entity].particles[j].turn_noise)
                                                                          ) % 360
            elif action == 'turn_right':
                self.model.points[entity].particles[j].orientation = (self.model.points[entity].particles[
                                                                              j].orientation - self.turn +
                                                                          random.gauss(0.0, self.model.points[
                                                                              entity].particles[j].turn_noise)
                                                                          ) % 360
            else:
                relation = []
                for k in range(0, len(self.model.points)):
                    if entity != k and self.model.points[k].has_orientation != False:
                        relation.append(self.get_qualitative_relation(self.model.points[k].x,
                                                                      self.model.points[k].y,
                                                                      self.model.points[entity].particles[j].x,
                                                                      self.model.points[entity].particles[j].y,
                                                                      self.model.points[k].orientation))
                    elif entity == k:
                        relation.append('x')

                print "relation", j, relation

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
                                                                                  k].orientation))
                        elif entity == k:
                            new_relation.append('x')

                print "new_relation", j, new_relation


        ### a % of particles to go to the next region
        relation = []
        changed_particles_index = []
        rate = 0.3 ### 30%
        changed_particles_index_qty = int(len(self.model.points[entity].particles) * rate)
        for k in range(0, changed_particles_index_qty):
            changed_particles_index.append(random.randint(0, (len(self.model.points[entity].particles)-1)))

        for j in range(0, len(changed_particles_index)):
            for k in range(0, len(self.model.points)):
                 if entity != k and self.model.points[k].has_orientation is not False:
                     relation.append(self.get_qualitative_relation(self.model.points[k].mean_x,
                                                                   self.model.points[k].mean_y,
                                                                   self.model.points[entity].particles[changed_particles_index[j]].x,
                                                                   self.model.points[entity].particles[changed_particles_index[j]].y,
                                                                   self.model.points[k].mean_orientation))
                 elif entity == k:
                     relation.append('x')

            new_relation = copy.copy(relation)
            ctrl = 0

            while cmp(new_relation, relation) == 0 and ctrl <= ctrl_total_per_trial:

                 new_relation = []
                 ctrl += 1
                 ## move, and add randomness to the motion command
                 dist = float(self.forward)
                 self.model.points[entity].particles[changed_particles_index[j]].x = self.model.points[entity].particles[changed_particles_index[j]].x + (
                     cos(rd(
                         self.model.points[entity].particles[changed_particles_index[j]].orientation)) * dist)
                 self.model.points[entity].particles[changed_particles_index[j]].y = self.model.points[entity].particles[changed_particles_index[j]].y + (
                     sin(rd(
                         self.model.points[entity].particles[changed_particles_index[j]].orientation)) * dist)

                 for k in range(0, len(self.model.points)):
                     if entity != k and self.model.points[k].has_orientation != False:
                         new_relation.append(self.get_qualitative_relation(self.model.points[k].mean_x,
                                                                           self.model.points[k].mean_y,
                                                                           self.model.points[
                                                                               entity].particles[changed_particles_index[j]].x,
                                                                           self.model.points[
                                                                               entity].particles[changed_particles_index[j]].y,
                                                                           self.model.points[
                                                                               k].mean_orientation))
                     elif entity == k:
                         new_relation.append('x')

        ### add radomness dist and orientation:
        for j in range(0, len(self.model.points[entity].particles)):
            dist = float(self.forward) + random.gauss(0.0, self.model.points[entity].particles[j].forward_noise)
            self.model.points[entity].particles[j].x = self.model.points[entity].particles[j].x + (
                cos(rd(self.model.points[entity].particles[j].orientation)) * dist)
            self.model.points[entity].particles[j].y = self.model.points[entity].particles[j].y + (
                sin(rd(self.model.points[entity].particles[j].orientation)) * dist)

            #dist = float(self.forward) + random.gauss(0.0, self.models[i].points[entity].particles[
            #    changed_particles_index[j]].forward_noise)
            #self.models[i].points[entity].particles[changed_particles_index[j]].x = self.models[i].points[entity].particles[changed_particles_index[j]].x + (
            #    cos(rd(self.models[i].points[entity].particles[changed_particles_index[j]].orientation)) * dist)
            #self.models[i].points[entity].particles[changed_particles_index[j]].y = self.models[i].points[entity].particles[changed_particles_index[j]].y + (
            #    sin(rd(self.models[i].points[entity].particles[changed_particles_index[j]].orientation)) * dist)

    def measurement_prob(self, entity, driven_robot_is_lost = 0):
        ## compare the new models with particles from the old models and gibe weights for all particles

        for k in range(0, len(self.model.points[entity].particles)):
            #print self.models[l].points[entity].particles[k].w
            self.model.points[entity].particles[k].w = 0.


        for k in range(0, len(self.model.points[entity].particles)):
            relation_particle = []
            for j in range(0, len(self.model.points)):
                if entity != j and self.model.points[j].has_orientation != False:
                    relation_particle.append(self.get_qualitative_relation(self.model.points[j].x,
                                                                  self.model.points[j].y,
                                                                  self.model.points[entity].particles[k].x,
                                                                  self.model.points[entity].particles[k].y,
                                                                  self.model.points[j].orientation))


            #print 'model', l
            #print 'relation_particle', relation_particle
            if self.model.points[entity].particles[k].out_of_fov == True:
                out_of_fov = 1
            else:
                out_of_fov = 0
            relation_particle.append(out_of_fov)
            print 'relation_particle', relation_particle

            relation_point_model = []
            for j in range(0, len(self.model.points)):
                if entity != j and self.model.points[j].has_orientation != False:
                    relation_point_model.append(self.get_qualitative_relation(self.model.points[j].x,
                                                                self.model.points[j].y,
                                                                self.updated_model.points[entity].x,
                                                                self.updated_model.points[entity].y,
                                                                self.updated_model.points[j].orientation))

            relation_point_model.append(driven_robot_is_lost)
            print 'relation_point_model', relation_point_model

            self.model.points[entity].particles[k].w = self.gaussian(0., self.sigma_xy_update, self.euclidean_distance(
                relation_particle, relation_point_model))


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
        #print "step", step
        #print "w_total", w_total

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

        #print "particles", self.model.points[entity].particles
