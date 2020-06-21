#!/bin/bash

echo "world number $1"

cd ../AI/Blackboard/src
sakura --title "clean Shared Memory" -e "python CleanSharedMemory.py" &
cd ../../Communication/src
sakura --title "receiving" -e "python server_TCP.py" &
sakura --title "sending"  -e "python client_TCP.py" &
cd ../../Decision/src
sakura --title "qsr" -e "python qsr.py" &
sakura --title "automatic prob starvars" -e "python automatic_prob_starvars.py $1" &
cd ../../..

ROBOTS=4

if [ $ROBOTS -gt 1 ]; then
    for ((i = 2; i <= $ROBOTS; i++)); do
	cd AI$i/Blackboard/src
	sakura --title "clean Shared Memory $i" -e "python CleanSharedMemory.py" &        
	cd ../../Communication/src
        sakura --title "receiving $i"  -e "python server_TCP.py" &
        sakura --title "sending $i"  -e "python client_TCP.py" &
        cd ../../Decision/src
        sakura --title "qsr $i"  -e "python qsr.py" &
        sakura --title "automatic prob starvars $i"  -e "python automatic_prob_starvars.py $1" &
        cd ../../..
        done
fi

cd ../../..

