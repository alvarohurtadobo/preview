import os
import cv2
import json
import time
import logging
from imutils.video import FPS
from imutils.video import VideoStream
from highpicamera import HighPiCamera

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
        if self.resolution:
            self.width = self.resolution[0]
            self.height = self.resolution[1]
        else:
            self.width = 0
            self.height = 0
        self.gray_scale = gray_scale
        self.brightness = brightness

        # Main variables
        self._capture = None

        self._video_souce = ""                      # Can be "pi_camera", "usbcamera" or "IP_camera"

        # We first define the nature of the input
        ## If not stated otherwise we use the pi camera:
        #print(self.input_video)
        if not self.input_video:
            self._video_souce = "pi_camera"
        else:
            if self.input_video.isdigit():
                self._video_souce = "usbcamera"
            elif "://" in self.input_video:
                # IP camera is like: rtsp://admin:DeMS2018@192.168.1.2:554/Streaming/channels/1
                self._video_souce = "IP_camera"
                
            else:
                raise Exception('Camera input: {}. set incorrectly'.format(self._video_souce ))

        if self._video_souce == "pi_camera":
            #we introduce the picamera libraries
            self._capture = HighPiCamera(   width = self.width,
                                            height = self.height,
                                            framerate = 2,
                                            emulate = None)
        elif self._video_souce == "IP_camera":
            self._capture = cv2.VideoCapture(self.input_video)
        else:
            self._capture = cv2.VideoCapture(int(self.input_video))
            self._capture.set(cv2.CAP_PROP_FPS, 30)
            if self.resolution:
                self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        time.sleep(1.0)

        self.ret, self.frame = self.read()
        if not self.ret:
            raise Exception('Did not receive any frame')
        self.shape = self.frame.shape
        self.received_resolution = (self.shape[1],self.shape[0])

        logging.info('[CREATED MULTI STREAM] type: {} and size: {}'.format(self._video_souce,self.shape))

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

    def release(self):
        if not self._video_souce == "pi_camera":
            self._capture.release()

    def read(self):
        """
        The most importan class tha unifies both ways of accessing the picamera, IP camera and usb camera
        """
        # We look for changes every 3 seconds:
        
        ret, frame = self._capture.read()

        # If we are set to grayscale  we set the property
        if self.gray_scale:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        if ret:
            frame.setflags(write=True)
        else:
            logging.error('No frame received')
        return ret, frame
