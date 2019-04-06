"""
This is a simple preview program and use example for the PlayStream Class
"""

"""
Examples:
1. pi_camera.- To run with a picamera do not add any input:
    python3 main.py -s True
2. usb_camera.- To run with a web cam just add the index of the camera to be used
    python3 main.py -s True -i 0
3. IP_camera.- To run with a IP camera just add the complete rtsp path to the images:
    python3 main.py -s True -i "rtsp://admin:DeMS@192.168.1.14:554/live/0/MAIN"
    python3 main.py -s True -i "rtsp://admin:DeMS2018@192.168.1.2:554/Streaming/channels/1"
    * To enter in IP mode the name must have the string '://' in its name
4. file_stream.- To run with a folder of images just provide the source to the images:
    python3 main.py -s True -i "/home/pi/WORKDIR"
5. image_stream / video_stream.- To run with a single file just add the path to the image or video: avi, mp4, jpg, png are accepted
    python3 main.py -s True -i "/home/pi/trafficFlow/trialVideos/sar2.mp4"
# For videos in the '/home/pi/trafficFlow/trialVideos/' directory, you can only state the name of the file
    python3 main.py -s True -i "sar2.mp4"

The outputs of the file are sent to the preview.txt file, to store in debug mode
    -d True

Parameters to setup the width and height, for Picamera/webcam only only
    -W 2464
    -H 1080

Set PERIOD [sec] for reporting fps and standar deviation:
    -p <PERIOD> [sec]

To capture a number videos <VIDEO_NUMBER> or captures <CAPTURE_NUMBER> of every period <PERIOD> with lenght <LENGTH> we set:
    -v 10 [10 videos will be geretated every <PERIOD> time]
    -c 10 [10 frame capture shots will be geretated every <PERIOD> time]
    -l 10 [sec, duration of the recorded videos and frames]

Set the program to self kill in a certain time:
    -k 10 [sec, time of duration of the program]

Set the frames per second intended for the application (depending on the camera we could get less):
    -f 10 [frames per second]

Other parameter for file stream are grayscale:
    -g [True/False]
For picamera the brigthness can be adjusted:
    -b [0-100]
"""

import os
import cv2
import sys
import time
import logging
import argparse
from datetime import datetime

sys.path.append(os.getenv('HOME')+'/trafficFlow/flaskwebcontroller/')
from servercontroller import ServerController
from playstream import PlayStream

parser = argparse.ArgumentParser(description='Perform next options')
parser.add_argument("-i", "--video_file",   type = str,  default = None,   help = "Specify optional video file")
parser.add_argument("-s", "--show",         type = bool, default = False,  help = "Show image in screen rather than server")
parser.add_argument("-k", "--autokill",     type = int,  default = 0,      help = "Self kill parameter")
parser.add_argument("-p", "--period",       type = int,  default = 20,     help = "Period for reporting")
parser.add_argument("-v", "--next_video",   type = int,  default = 0,      help = "Periods to store video")
parser.add_argument("-c", "--next_captures",type = int,  default = 0,      help = "Periods to store single frames")
parser.add_argument("-f", "--fps",          type = int,  default = 12,     help = "Optional FPS")
parser.add_argument("-W", "--width",        type = int,  default = 320,    help = "Specify optional video width")
parser.add_argument("-H", "--height",       type = int,  default = 240,    help = "Specify optional video height")
parser.add_argument("-g", "--grayscale",    type = bool, default = False,  help = "Set grayscale mode")
parser.add_argument("-d", "--debug",        type = bool, default = False,  help = "Set logging to debug")
parser.add_argument("-b", "--brightness",   type = int,  default = 50,     help = "Specify optional brightness for the camera")
parser.add_argument("-t", "--threaded",     type = bool, default = False,  help = "Optional enable threaded module")
parser.add_argument("-l", "--length",       type = int,  default = 10,     help = "Lenght for historial in seconds, it is adviced not to be greater than period")
#parser.add_argument("-r", "--real",         type = bool, default = False, help = "Emulate real time, for saved video only")
args = parser.parse_args()

frame_number = 0

if __name__ == '__main__':
    # Logging settings
    my_level = logging.INFO
    if args.debug:
        my_level = logging.DEBUG
        logging.debug('Generando DEBUG')
    logging.basicConfig(filename='preview.txt', filemode='w', format='%(name)s - %(asctime)s : %(message)s',level=my_level)

    # Self Kill settings
    autokill = 0
    if args.autokill > 0:
        autokill = args.autokill
        logging.info('Set autokill to {} seconds'.format(autokill))

    miCamara = PlayStream(  input_video = args.video_file,
                            resolution = (args.width,args.height),
                            historial_len = args.length,
                            brightness = args.brightness,
                            fake_gray_scale = args.grayscale,
                            fps = args.fps)

    server = ServerController()

    initialTime = time.time()

    exportOutput = os.getenv('HOME')+'/output'

    if not os.path.exists(exportOutput):
        os.makedirs(exportOutput)

    time_now = time.time()

    counter_for_videos = args.next_video
    counter_for_captures = args.next_captures

    logging.info('Started program at {} with required FPS: {}'.format(datetime.now().strftime('%Y%m%d_%H%M%S'),args.fps))
    if args.show:
        cv2.namedWindow('Preview', cv2.WND_PROP_FULLSCREEN)

    while True:
        try:
            ret, frame = miCamara.read() 

            if not ret:
                logging.info('Ret False, could not get any frame at: {}'.format(datetime.now().strftime('%Y%m%d_%H%M%S')))

            if args.show:
                cv2.imshow('Preview',frame)
            else:
                server.sendImageIfAllowed(frame)
            
            frame_number += 1

            if (time.time() - time_now > args.period):
                logging.info('Last FPS: {0:.2f}, Last Period: {1:.3f}, Last Standar Deviation: {2:.5f}'.format(miCamara.getFPS(),miCamara.getPeriod(),miCamara.getStandarDeviation()/miCamara.getPeriod()))
                exportOutputName = exportOutput + '/' +datetime.now().strftime('%Y%m%d_%H%M%S')
                if counter_for_videos > 0:
                    #logging.info('Saving video at frame {}, with shape {}'.format(frame_number,frame.shape))
                    miCamara.generateVideo(exportOutputName)
                    counter_for_videos -= 1
                if counter_for_captures > 0:
                    #logging.info('Saving images at frame {}, with shape {}'.format(frame_number,frame.shape))
                    miCamara.exportHistorialAsImages(exportOutputName)
                    counter_for_captures -= 1
                time_now = time.time()

            if autokill > 0:
                if time.time() - initialTime > autokill:
                    logging.info('Automatic program exit')
                    break

            ch = cv2.waitKey(1) & 0xFF
            if ch == ord('q'):
                break
            if ch == ord('s'):
                cv2.imwrite(exportOutput + '/' +datetime.now().strftime('%Y%m%d_%H%M%S')+'.png',frame)
                
        except Exception as e:
            logging.info('Exception "{}" at: {}. Leaving'.format(str(e),datetime.now().strftime('%Y%m%d_%H%M%S')))
            break
