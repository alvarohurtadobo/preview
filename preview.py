import os
import cv2
import sys
import time
import json
import argparse
import datetime
import numpy as np
from imutils.video import FPS
from imutils.video import VideoStream
from servercontroller import ServerController

parser = argparse.ArgumentParser(description='Perform next options')
parser.add_argument("-k", "--autokill", type=int, help="Introduce the autokill parameter", default=0)
parser.add_argument("-s", "--showImage", type=bool, help="Mostrar", default=False)
parser.add_argument('video_file', metavar='video_file', type=str, nargs='?', help='specify optional video file')
args = parser.parse_args()

if __name__ == '__main__':
    videoAddress = os.getenv('HOME') +'/trafficFlow/trialVideos/'
    picam = False
    if args.video_file:
        source = videoAddress + args.video_file
        miCamara = cv2.VideoCapture(source)
    else:
        try:
            miCamara  = VideoStream(usePiCamera=True, resolution=(320,240)).start()
            time.sleep(2.0)
            picam = True
            print('Success accessing picamera')
        except Exception as e:
            print('Could not access any picamera, error: '+str(e))
            for sourceTrial in range(2):
                try:
                    miCamara = cv2.VideoCapture(sourceTrial)
                    print('Success reading usb camera at {}'.format(sourceTrial))
                except:
                    pass
            picam = False

    server = ServerController()
    if args.autokill > 0:
        autokill = args.autokill
        print('Set autokill to {} seconds'.format(autokill))
    initialTime = time.time()
    while True:
        
        if picam:
            frame = miCamara.read() 
        else:
            ret,frame = miCamara.read() 
        frameToSend = cv2.resize(frame,(320,240))
        if args.showImage:
            cv2.imshow('Window',frameToSend)
        server.sendImageIfAllowed(frameToSend)
        ch = cv2.waitKey(1) & 0xFF
        if autokill > 0:
            if time.time() - initialTime > autokill:
                break
        if ch == ord('q'):
            break
