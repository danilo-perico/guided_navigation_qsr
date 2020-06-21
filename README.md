# Guided Navigation from Multiple Viewpoints using QualitativeSpatial Reasoning


The simulated experiments are made using an adaptation of the RoboFEI-HT Simulator \[[1]] \[[2]].

[1]: https://doi.org/10.1007/s40313-018-0390-y
[2]: https://github.com/danilo-perico/robofei-ht-framework



### Setup

1. compile the code of the robot running *./setup.sh*. Choose 4 robots.

2. Once the robots codes are compiled, run *main_simulator.py* inside the Simulator folder, for running the simulation environment.

3. Then, press *F9* to start the simulation. A world number will be required in terminal. It is the number of the initial positioning of all entities. It is possible to choose a number between 0 and 99.

4. It is possible to configure the used approach for reasoning, *m* and *tau* in file *config.py*


### OS and dependencies

This program was tested in Ubuntu 16.04 LTS 64 bits

* Main Dependencies:
    * cmake
    * g++
    * python 2.7 
    * pygame
    * numpy
    * cvxopt
    * sakura
    * libhdf5-serial-dev
    * libboost-all-dev 
    * screen
    
### License

GNU GENERAL PUBLIC LICENSE.
Version 3, 29 June 2007
   
