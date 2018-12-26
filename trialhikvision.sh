#!/bin/bash

cd $HOME/trafficFlow/preview
python3 main.py -p 192.168.1.11:554 -t 60 -n 5 -l 30
cd