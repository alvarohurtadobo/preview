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
parser.add_argument("-k", "--autokill",     type = int, default = 0,      help = "Self kill parameter")
parser.add_argument("-s", "--show_image",   type = bool, default = False, help = "Show image in screen rather than server")
parser.add_argument("-i", "--video_file",   type = str, default = None,   help = "Specify optional video file")
parser.add_argument("-W", "--width",        type = int, default = 320,    help = "Specify optional video width")
parser.add_argument("-H", "--height",       type = int, default = 240,    help = "Specify optional video height")
parser.add_argument("-p", "--ip_camera",    type = str, default = None,   help = "Specify optional ip camera file")
parser.add_argument("-g", "--grayscale",    type = bool, default = False, help = "Set grayscale mode")
parser.add_argument("-b", "--brightness",   type = int, default = 50,     help = "Specify optional brightness for the camera")
parser.add_argument("-t", "--threaded",     type = bool, default = False,  help = "Optional enable threaded module")
args = parser.parse_args()

frame_number = 0

if __name__ == '__main__':
    autokill = 0
    if args.autokill > 0:
        autokill = args.autokill
        print('Set autokill to {} seconds'.format(autokill))
    if args.ip_camera:
        miCamara = PlayStream(  ip_address_with_port = args.ip_camera,
                                resolution = (args.width,args.height),
                                historial_len = 30,
                                brightness = args.brightness,
                                fake_gray_scale = args.grayscale)
    else:
        miCamara = PlayStream(  input_video = args.video_file,
                                resolution = (args.width,args.height),
                                historial_len = 30,
                                brightness = args.brightness,
                                fake_gray_scale = args.grayscale)
                                
    server = ServerController()

    initialTime = time.time()
    while True:
        ret,frame = miCamara.read() 
        if args.show_image:
            cv2.imshow('Window',frame)
        else:
            server.sendImageIfAllowed(frame)
        ch = cv2.waitKey(1) & 0xFF
        frame_number+=1
        if frame_number % 300 == 60:
            print(frame.shape)
            print(miCamara.getFPS())
            #PlayStream.exportHistorialAsImages('/home/alvaro/images')
        if autokill > 0:
            if time.time() - initialTime > autokill:
                print('Automatic program exit')
                break
        if ch == ord('q'):
            break
