def calculus_update():
    start = time.time()

    starvars = StarVars()

    loopnum = starvars.Data_Pre_Processing()

    starvars.Recursive_For([], loopnum)

    orientations, xy, relations = starvars.getAnswer()

    number_entities = len(xy[0]) / 2
    number_possible_answers = len(xy)
    number_active_points = len(relations[0])

    points = []
    for i in range(0, number_entities):
        points.append(OrientedPoint())
        for j in range(0,number_possible_answers):
            points[i].x.append(xy[j][i][0])
            points[i].y.append(xy[j][i + number_entities][0])
            if i < number_active_points:
                points[i].orientation.append(orientations[j][i])
            else:
                points[i].orientation.append([])

    probability = Particle_Filter(points)

    probability.Release_Particles()

    probability.Visual_Interface()

    probability.Mean()

    probability.Spatial_Relations_by_Mean()

    while(True):
        ## Motion_Model(oriented_point that should move)
        action = str(raw_input('Action [turn_left, turn_right, go_forward]: '))
        point = int(raw_input('Point: '))
        probability.Motion_Model(point, action)

        probability.Visual_Interface()
        plt.pause(0.1)
        plt.show()
    #print xy
    #print orientations
    #print relations
    end = time.time()
    print 'iteration time: ', (end-start)