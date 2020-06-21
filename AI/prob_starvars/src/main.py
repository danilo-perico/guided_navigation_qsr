#!/usr/bin/env python
#coding: utf-8

__author__ = "Danilo H. Perico"
__license__= "GNU General Public License v3.0"
__project__ = "Probabilistic StarVars"

from graphical_interface import *


def main():
    pygame.init()
    pygame.display.set_caption('Probabilistic StarVars')
    graphical_interface = Interface()

    while(True):
        # Process events
        graphical_interface.perform_events()


        # graphical_interface.display_update()
        graphical_interface.background.fill((240, 240, 240))


        # frame rate
        pygame.time.Clock().tick(300)

##Call the main function, start up
if __name__ == "__main__":
    main()


