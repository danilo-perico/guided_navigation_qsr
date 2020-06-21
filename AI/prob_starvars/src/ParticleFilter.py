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
from CreateModel import *
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


class ParticleFilter:
    def __init__(self, background=None):
        self.model = None
        self.updated_model = None
        self.background = background
        self.particles_number_per_point = 100
        self.sigma_xy_spread = 1.0
        self.sigma_xy_update = 0.05
        self.sigma_orient = 7.5
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

    def release_particles(self, reset = [False]):
        print 'release particles'
        for j in range(0, len(self.model.points)):
            if j == self.driven:
                mean = [self.model.points[j].x, self.model.points[j].y]
                #cov = [[self.sigma_xy_spread, 0.], [0., self.sigma_xy_spread]]
                cov = [[0, 0.], [0., 0]]
                for k in range(0, self.particles_number_per_point):
                    particle = Particles()

                    particle.x, particle.y = np.random.multivariate_normal(mean, cov).T
                    if self.model.points[j].orientation == -1 and reset[0] == False:
                        particle.orientation = random.gauss(random.randrange(0, 360, 60/self.m),
                                                            particle.turn_noise)
                    elif self.model.points[j].orientation != -1:
                        particle.orientation = random.gauss(self.model.points[j].orientation, particle.turn_noise)
                    else:
                        pass
                    self.model.points[j].particles.append(particle)
                    print particle.x, particle.y, particle.orientation
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

    def scale(self, x, y):
        width, height = self.background.get_size()
        xmin = self.x_bounds[0] - ((self.x_bounds[1] - self.x_bounds[0]) * 0.1)
        xmax = self.x_bounds[1] + ((self.x_bounds[1] - self.x_bounds[0]) * 0.1)

        ymin = self.y_bounds[0] - ((self.y_bounds[1] - self.y_bounds[0]) * 0.1)
        ymax = self.y_bounds[1] + ((self.y_bounds[1] - self.y_bounds[0]) * 0.1)

        scaled_x = ((x + abs(xmin)) * (width)) / (xmax - xmin)
        scaled_y = height - ((y + abs(ymin)) * (height) / (ymax - ymin))
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

        textpos = (300,0)
        textpos = list(textpos)
        self.background.blit(font.render('Action:' + self.action, 1, (10, 10, 10)), textpos)

        for j in range(0, len(self.model.points)):
            for k in range(0, len(self.model.points[j].particles)):
                scaled_x, scaled_y = self.scale(self.model.points[j].particles[k].x, self.model.points[j].particles[k].y)
                if not self.model.points[j].particles[k].orientation == []:
                    if j == self.driven:
                        #self.model.points[j].particles[k].draw_orientation_star(self.model.points[j].color,
                        #                                                       scaled_x, scaled_y,
                        #                                                       self.background, 1, self.x_bounds, self.y_bounds)
                        self.model.points[j].particles[k].draw_orientation(self.model.points[j].color, scaled_x, scaled_y,
                                                                 self.background)
                    else:
                        self.model.points[j].particles[k].draw_orientation(self.model.points[j].color, scaled_x, scaled_y,
                                                                 self.background)
                        #self.model.points[j].particles[k].draw_orientation_star(self.model.points[j].color,
                        #                                                       scaled_x, scaled_y,
                        #                                                       self.background, 1, self.x_bounds, self.y_bounds)
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

    def get_angle(self, x1, y1, x2, y2, orientation1):
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
        #alpha = round(alpha)
        if alpha > 180:
            alpha = 360 - alpha
        return alpha

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
        alpha = alpha % 360
        alpha = round(alpha, 4)
        angle = 360.0 / self.m

        for i in range(0, self.m):
            if alpha >= (i * angle) and alpha < ((i+1)*angle):
                qualitative_region = i
        return qualitative_region

    def answers_probability(self):
        answers_probability = [0] * self.m
        ### using mean ###
        # self.mean()
        # relation_to_goal = self.get_qualitative_relation(
        #          self.model.points[self.driven].mean_x,
        #          self.model.points[self.driven].mean_y,
        #          self.model.points[self.goal].mean_x,
        #          self.model.points[self.goal].mean_y,
        #          self.model.points[self.driven].mean_orientation)
        ### ###
        ### using each particle ###
        for j in range(0, len(self.model.points[self.driven].particles)):
            relation_to_goal = self.get_qualitative_relation(
                self.model.points[self.driven].particles[j].x,
                self.model.points[self.driven].particles[j].y,
                self.model.points[self.goal].mean_x,
                self.model.points[self.goal].mean_y,
                self.model.points[self.driven].particles[j].orientation)

            answers_probability[relation_to_goal] += 1

        self.probability = map(lambda x: float(x)/self.particles_number_per_point, answers_probability)
        print 'probability', self.probability

        ### using mean ###
        #self.probability = relation_to_goal
        ### ####

    def qualitative_command(self, probabilistic = True):
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


    def sense(self, reset = [False]):
        self.create_model = CreateModel(self.model)
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

        self.data_matrix = np.array(split_data)

        print 'class ParticleFilter says:'
        print 'self.data_matrix'
        print self.data_matrix

        if len(self.data_matrix) != self.number_oriented_points and  len(self.data_matrix) != (self.number_oriented_points * (self.number_of_entities-1)):
            bkb.write_int(mem, 'CONTROL_MESSAGES', 4)
            time.sleep(2)
            return False

        ### get orientation from driven agent ###
        orientation_driven_agent_filter = []
        driven_agent_data = self.data_matrix[np.where(self.data_matrix[:, 0] == self.driven)]
        for i in range(len(driven_agent_data)):
           orientation_driven_agent_filter.append(driven_agent_data[i][1])
           self.orientation_driven_agent = max(set(orientation_driven_agent_filter), key= orientation_driven_agent_filter.count)

        if self.model is None:
            pass
        else:
            print "data_matrix_else"
            print self.data_matrix

            for i in range(0, len(self.model.points)):
                for j in range(0, len(self.model.points)):
                    if i != j and j != self.driven and i != self.driven and i != self.goal:
                        retrieved_relation = self.get_angle(
                                                        self.model.points[i].x,
                                                        self.model.points[i].y,
                                                        self.model.points[j].x,
                                                        self.model.points[j].y,
                                                        self.model.points[i].orientation)
                        retrieved_data = [i, self.model.points[i].particles[0].orientation, retrieved_relation, retrieved_relation, retrieved_relation, j]
                        retrieved_data = np.array([retrieved_data])
                        self.data_matrix = np.concatenate((self.data_matrix, retrieved_data))
            print "new data matrix"
            print self.data_matrix

        self.create_model.modeling(self.data_matrix)
        orientations, xy = self.create_model.getAnswer()
        # print hex(id(self.relations))
        print 'class Particle_Filter says: '
        print '====== Particles ======'
        print xy
        print orientations
        print '======================'
        #try:
        number_entities = len(xy[0]) / 2
        print "number entities", number_entities
        points = []
        for i in range(0, number_entities):
            points.append(OrientedPoint(i))
            points[i].x = xy[0][i][0]
            points[i].y = xy[0][i + number_entities][0]
            if i < self.number_oriented_points:
                if i == self.driven:
                    points[i].orientation = self.orientation_driven_agent
                else:
                    points[i].orientation = orientations[i]
            else:
                points[i].has_orientation = False
                points[i].orientation = []

        print 'class Particle_Filter says: '
        print '== Success! ==========================================='


        if self.model is None:
            self.model = WorldModel(points)
            print 'class ParticleFilter says: New Model '
            print self.model
        else:
            self.updated_model = WorldModel(points)
            print 'class ParticleFilter says: Updated Model'
            print self.updated_model

        #except:
        #    print 'class Particle_Filter says: '
        #    print '== Error! ============================================='


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
                dist = float(self.forward) + abs(random.gauss(0.0, self.model.points[entity].particles[j].forward_noise))
                print "antes", self.model.points[entity].particles[j].x
                self.model.points[entity].particles[j].x = self.model.points[entity].particles[j].x + (
                cos(rd(self.model.points[entity].particles[j].orientation)) * dist)
                print "depois", self.model.points[entity].particles[j].x
                self.model.points[entity].particles[j].y = self.model.points[entity].particles[j].y + (
                sin(rd(self.model.points[entity].particles[j].orientation)) * dist)



    def measurement_prob(self, entity, driven_robot_is_lost = 0):
        ## compare the new models with particles from the old models and give weights for all particles
        for k in range(0, len(self.model.points[entity].particles)):
            self.model.points[entity].particles[k].w = 0.

        for k in range(0, len(self.model.points[entity].particles)):
            particle_posture = [self.model.points[entity].particles[k].x, self.model.points[entity].particles[k].y]
            updated_model_posture = [self.updated_model.points[entity].x, self.updated_model.points[entity].y]

            prob = self.gaussian(0, self.sigma_xy_update, self.euclidean_distance(particle_posture, updated_model_posture))
            max_prob = max(prob, 1e-300)

            self.model.points[entity].particles[k].w = max_prob

            #print 'x,y, sense:'
            #print self.updated_model.points[entity].x, self.updated_model.points[entity].y
            print 'x,y, particle k:'
            #print self.model.points[entity].particles[k].x, self.model.points[entity].particles[k].y
            print 'k, particle.w', k, self.model.points[entity].particles[k].w

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

        ### sensor resetting
        for k in range(self.m):
            self.model.points[entity].particles[k].x = self.updated_model.points[entity].x
            self.model.points[entity].particles[k].y = self.updated_model.points[entity].y
            self.model.points[entity].particles[k].orientation = k*360/self.m


    def reasoning(self, reset, finish = 0, ctrl = 0):
        if self.sense(reset) == False:
            return False
        if ctrl == 0:
            self.release_particles()
        else:
            self.measurement_prob(prob_starvars_config.driven)

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
            #bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'turn_left_and_walk_forward':
            self.move(prob_starvars_config.driven, 'turn_left')
            self.move(prob_starvars_config.driven, 'go_forward')
            self.draw_particles()
            self.mean()
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 2)
            #bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'turn_right_and_walk_forward':
            self.move(prob_starvars_config.driven, 'turn_right')
            self.move(prob_starvars_config.driven, 'go_forward')
            self.draw_particles()
            self.mean()
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 3)
            #bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        elif action == 'turn_back_and_walk_forward':
            self.move(prob_starvars_config.driven, 'turn_left')
            self.move(prob_starvars_config.driven, 'turn_left')
            self.move(prob_starvars_config.driven, 'go_forward')
            self.draw_particles()
            self.mean()
            bkb.write_int(mem, 'COM_ACTION_ROBOT1', 4)
            #bkb.write_int(mem, 'CONTROL_MESSAGES', 1)
            return False

        else:
            bkb.write_int(mem, 'CONTROL_MESSAGES', 11)
            print 'Fail'
            print 'Resetting StarVars'
            reset[0] = True
            ctrl = 0
            return False
