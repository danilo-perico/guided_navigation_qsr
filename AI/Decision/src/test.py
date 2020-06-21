import sys

sys.path.append('../../')

from prob_starvars.src.StarVarsReasoning import *

test = StarVarsReasoning()

if test.reasoning(False):
    print("ola")
