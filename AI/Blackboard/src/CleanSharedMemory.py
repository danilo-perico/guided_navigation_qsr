import sys

from SharedMemory import SharedMemory
sys.path.append('../../..')
from config import *

print "resetting Shared Memory ..."

prob_starvars_config = Config()

### config parser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

config = ConfigParser()
config.read('../../Control/Data/config.ini')
mem_key = int(config.get('Communication', 'no_player_robofei')) * 100

bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)

bkb.write_int(mem, 'DECISION_ACTION_A', 0)
bkb.write_int(mem, 'DECISION_ACTION_B', 0)
bkb.write_int(mem, 'COM_ACTION_ROBOT1', 0)
bkb.write_int(mem, 'CONTROL_MESSAGES', 0)
bkb.write_int(mem, 'SERVER_BEGIN', 0)
bkb.write_int(mem, 'HIT', 0)
bkb.write_int(mem, 'REASONING_COMPLETED', 0)
bkb.write_int(mem, 'ENVIRONMENT_SETUP', 0)
bkb.write_int(mem, 'LOST_DRIVEN_ROBOT', 0)
bkb.write_float(mem, 'COM_POS_ANGLE', 0)
bkb.write_int(mem, 'VISION_LOST', 0) 
bkb.write_int(mem, 'FINISH', 0) 
bkb.write_int(mem, 'GOAL_FOUND', 0) 

print "Shared Memory clean..."
