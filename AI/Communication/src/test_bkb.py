import sys
import time


sys.path.append('../../Blackboard/src/')
from SharedMemory import SharedMemory

mem_key = 4*100

#Instantiate the BlackBoard's class:
bkb = SharedMemory()
mem = bkb.shd_constructor(mem_key)


while(True):
    time.sleep(0.5)
    bkb.write_int(mem, 'SERVER_BEGIN', raw_input('enter CONTROL MESSAGES: '))
    print bkb.read_int(mem, 'CONTROL_MESSAGES')
