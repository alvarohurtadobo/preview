import os
import cv2
import json
import time
import logging
from imutils.video import FPS
from imutils.video import VideoStream

class MultiStream():
    """
    This class combines file, usbcamera and picamera inputs
    """

    def __init__(self,  input_video = None,
                        resolution = (320,240),
                        gray_scale = False,
                        brightness = 50):
        """
        The class is started with a "input_video" in case of a file and a USB camera or None with picamera
        The default resolution is 320x240 and can be changed as resolution = (w,h)
        """
        # General settings
        self.input_video = input_video
        self.resolution = resolution
        self.width = self.resolution[0]
        self.height = self.resolution[1]
        self.gray_scale = gray_scale
        self.brightness = brightness

        # Main variables
        self._capture = None

        self._video_souce = ""                      # Can be "pi_camera", "usbcamera" or "IP_camera"

        # We first define the nature of the input
        ## If not stated otherwise we use the pi camera:
        if not self.input_video:
            self._video_souce = "pi_camera"
        else:
            if self.input_video.isdigit():
                self._video_souce = "usbcamera"
            elif "://" in self.input_video:
                # IP camera is like: rtsp://admin:DeMS2018@192.168.1.2:554/Streaming/channels/1
                self._video_souce = "IP_camera"
            else:
                raise Exception('Camera input set incorrectly')

        logging.info('[INFO STREAM]: '+self._video_souce +' source selected')

        if self._video_souce == "pi_camera":
            #we introduce the picamera libraries
            try:
                if resolution:
                    self._capture  = VideoStream(usePiCamera=True, resolution=self.resolution).start()
                else:
                    self._capture  = VideoStream(usePiCamera=True).start()
            except Exception as e:
                logging.info('Could not access any picamera, error: '+str(e))
            try:
                self._capture.camera.brightness = self.brightness
            except:
                logging.info('Could not set brightness to {}'.format(self.brightness))
        elif self._video_souce == "IP_camera":
            self._capture = cv2.VideoCapture(self.full_ip_address())
        elif self._video_souce == "image_file":
            # In case of a file we try all possible locations for the file
            if os.path.isfile(input_video):
                self._capture = ImageCapture(input_video)

        elif self._video_souce == "image_folder":
            # In case of a file we try all possible locations for the file
            if os.path.isdir(self.input_video):
                self._capture = FolderCapture(self.input_video)
            else:
                logging.info('The path provided does not match any existing folder')
        else:
            # In case of a usb camera we try to access it
            try:
                self._capture = cv2.VideoCapture(int(desiredUsbInput))
                ret,frame = self._capture.read()
                auxiliarShape = frame.shape
            except Exception as e:
                logging.info('Could not load the USB camera trying other ports')
                for sourceTrial in range(3):
                    logging.info('Trying {}'.format(sourceTrial))
                    try:
                        self._capture = cv2.VideoCapture(sourceTrial)
                        ret,frame = self._capture.read()
                        if ret:
                            break
                        logging.info('Success reading usb camera at {}'.format(sourceTrial))
                    except:
                        pass
        
            if self._capture:
                # In case of a usb camera we set the parameters
                self._capture.set(cv2.CAP_PROP_FPS, 30)
                if self.resolution:
                    self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        time.sleep(1.0)

    def set_brightness(self,new_brightness):
        # Set the brightness only for the pi camera
        self.brightness = new_brightness
        if self._video_souce == "pi_camera":
            self._capture.camera.brightness = self.brightness

    def set_grayscale(self):
        # Set grayscale to true, by now only averaging the channels
        self.gray_scale = True

    def set_color(self):
        # Set color to RBG
        self.gray_scale = False

    def addVideoRoutes(self,new_path_to_video):
        # In case a custom route to the videos is added for the search job
        self._video_paths.append(new_path_to_video)
        return len(self._video_paths)

    def read(self):
        """
        The most importan class tha unifies both ways of accessing the picamera and usb camera
        """
        # We look for changes every 3 seconds:
        if os.path.isfile(expected_configs_file_name):
            with open(expected_configs_file_name) as json_file:
                new_configs = json.load(json_file)
                if new_configs['changed'] == True:
                    self.set_brightness(int(new_configs['brightness']))
                    if new_configs['gray']:
                        self.set_grayscale()
                    else:
                        self.set_color()
            new_configs['changed'] = False
            new_configs_file_name = expected_configs_file_name.split('.')[0]
            with open(expected_configs_file_name, 'w') as json_file:  
                json.dump(new_configs, json_file)
            os.rename(expected_configs_file_name,new_configs_file_name)
                
        if self._video_souce == "pi_camera":
            frame = self._capture.read()
            if len(frame.shape)>=1:
                ret = True
            else:
                ret = False

        elif self._video_souce == "usbcamera":
            ret, frame = self._capture.read()
        elif self._video_souce == "IP_camera":
            ret, frame = self._capture.read()
        else:
            pass

        # If we are set to grayscale  we set the property
        if self.gray_scale:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        frame.setflags(write=True)
        return ret, frame

    def release(self):
        if not self._video_souce == "pi_camera":
            self._capture.release()
