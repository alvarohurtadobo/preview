"""
This is a simple preview program and use example for the PlayStream Class
"""

import os
import cv2
import sys
import time
import argparse

sys.path.append(os.getenv('HOME')+'/trafficFlow/flaskwebcontroller/')
from servercontroller import ServerController
from playstream import PlayStream

parser = argparse.ArgumentParser(description='Perform next options')
parser.add_argument("-k", "--autokill", type=int, help="Auto kill parameter", default=0)
parser.add_argument("-s", "--showImage", type=bool, help="Show image in screen rather than server", default=False)
parser.add_argument("-i", "--video_file", type=str, help="Specify optional video file", default=None)
parser.add_argument("-W", "--width", type=int, help="Specify optional video width", default=320)
parser.add_argument("-H", "--height", type=int, help="Specify optional video height", default=240)
parser.add_argument("-p", "--ip_camera", type=str, help="Specify optional ip camera file", default=None)
#parser.add_argument('video_file', metavar='video_file', type=str, nargs='?', help='specify optional video file')
args = parser.parse_args()

frame_number = 0

if __name__ == '__main__':
    autokill = 0
    if args.autokill > 0:
        autokill = args.autokill
        print('Set autokill to {} seconds'.format(autokill))
    if args.ip_camera:
        miCamara = PlayStream(ip_address_with_port = args.ip_camera)
    else:
        miCamara = PlayStream(input_video = args.video_file,resolution=(args.width,args.height))
    server = ServerController()

    initialTime = time.time()
    while True:
        ret,frame = miCamara.read() 
        print(frame.shape)
        if args.showImage:
            cv2.imshow('Window',frame)
        else:
            server.sendImageIfAllowed(frame)
        ch = cv2.waitKey(1) & 0xFF
        frame_number+=1
        if frame_number % 100:
            print(miCamara.getFPS())
        if autokill > 0:
            if time.time() - initialTime > autokill:
                print('Automatic program exit')
                break
        if ch == ord('q'):
            break
