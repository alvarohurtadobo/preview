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
#parser.add_argument("-t", "--threaded",     type = bool, default = False,  help = "Optional enable threaded module")
parser.add_argument("-t", "--period",       type = int, default = 0,      help = "Optional period for saving images")
parser.add_argument("-f", "--fps",          type = int, default = 6,      help = "Optional FPS")
parser.add_argument("-n", "--next",         type = int, default = 1,      help = "Next images backup on video")
parser.add_argument("-l", "--lenght",       type = int, default = 10,     help = "Lenght for historial in seconds")
#parser.add_argument("-r", "--real",         type = bool, default = False, help = "Emulate real time, for saved video only")
args = parser.parse_args()

frame_number = 0

if __name__ == '__main__':
    autokill = 0
    if args.autokill > 0:
        autokill = args.autokill
        print('Set autokill to {} seconds'.format(autokill))
    if args.ip_camera:
        miCamara = PlayStream(  ip_address_with_port = args.ip_camera,
                                resolution = (1920,1080),
                                historial_len = args.lenght,
                                brightness = args.brightness,
                                fake_gray_scale = args.grayscale,
                                fps = args.fps)
    else:
        miCamara = PlayStream(  input_video = args.video_file,
                                resolution = (args.width,args.height),
                                historial_len = args.lenght,
                                brightness = args.brightness,
                                fake_gray_scale = args.grayscale,
                                fps = args.fps)
                                
    server = ServerController()

    initialTime = time.time()

    exportOutput = os.getenv('HOME')+'/output'

    if not os.path.exists(exportOutput):
        os.makedirs(exportOutput)

    time_now = time.time()

    counter_for_images = args.next

    while True:
        ret,frame = miCamara.read() 
        if args.show_image:
            cv2.imshow('Window',frame)
        else:
            server.sendImageIfAllowed(frame)
        ch = cv2.waitKey(1) & 0xFF
        frame_number += 1

        if  (time.time() - time_now > args.period) and (args.period > 0):
            print('Saving files at frame {}, with shape {}, and at real FPS {} from requested FPS {}'.format(frame_number,frame.shape,miCamara.getFPS(),miCamara.fps))
            miCamara.generateVideo(exportOutput)
            if counter_for_images > 0:
                PlayStream.exportHistorialAsImages(exportOutput)
                counter_for_images -= 1
            time_now = time.time()
        if autokill > 0:
            if time.time() - initialTime > autokill:
                print('Automatic program exit')
                break
        if ch == ord('q'):
            break
