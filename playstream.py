"""
Simple class for using multiple inputs and multiple sources of videos with opencv and picamera
"""

import os
import cv2
import time
from datetime import datetime
from imutils.video import FPS
from imutils.video import VideoStream

#from ipcamera import IPCamera

class PlayStream():
    """
    This class combines file, usbcamera and picamera inputs
    """
    historial = {}
    frame_number = 0
    list_period = []
    
    def __init__(self,  input_video = None, 
                        ip_address_with_port = None,
                        resolution = (320,240),
                        fake_gray_scale = False,
                        brightness = 50,
                        real_time = False,
                        historial_len = None):
        """
        The class is started with a "input_video" in case of a file and a USB camera or None with picamera
        The default resolution is 320x240 and can be changed as resolution = (w,h)
        """
        # General settings
        self.fps = 30
        self._init_time = time.time()
        homeRoute = os.getenv('HOME')
        self.new_time = time.time()
        self.old_time = self.new_time
        self.fake_gray_scale = fake_gray_scale
        self.brightness = brightness

        self.historial_len = None
        try:
            if historial_len > 0:
                self.historial_len = historial_len
        except:
            print('Not integer returned')

        self._capture = None
        self.width = None
        self.height = None
        if resolution:
            self.resolution = resolution
            self.width = resolution[0]
            self.height = resolution[1]
        
        self._video_souce = "picamera"                      # Can be "picamera", "usbcamera" or "file"

        # File settings:
        self._video_paths = [homeRoute+'/trafficFlow/trialVideos/']
        
        self.emulate_real_time = real_time

        # IP camera settings
        self.ip_format = ['rtsp://admin:DeMS2018@','/Streaming/channels/1/preview']    # rtsp://admin:DeMS2018@192.168.1.2:554/Streaming/channels/1
        self.ip_address_with_port = ip_address_with_port                        # 192.168.1.20:554

        if ip_address_with_port:
            self._video_souce = "IPcamera"
        elif input_video:
            input_video = input_video.replace(' ','')       # Remove when updated validators
            try:
                desiredUsbInput = int(input_video)
                self._video_souce = "usbcamera"
            except:
                self._video_souce = "file"
        
        print('[INFO STREAM]:',self._video_souce,'source selected')

        if self._video_souce == "picamera":
            #we introduce the picamera libraries
            try:
                if resolution:
                    self._capture  = VideoStream(usePiCamera=True, resolution=self.resolution).start()
                else:
                    self._capture  = VideoStream(usePiCamera=True).start()
            except Exception as e:
                print('Could not access any picamera, error: '+str(e))
            try:
                self._capture.stream.camera.brightness = self.brightness
            except:
                print('<<< COULD NOT SET BRIGHTNESS, CHECK THE PATH >>>')
        elif self._video_souce == "IPcamera":
            self._capture = cv2.VideoCapture(self.full_ip_address())
            #self._capture = IPCamera(self.full_ip_address())
        elif self._video_souce == "file":
            # In case of a file we try all possible locations for the file
            if os.path.isfile(input_video):
                self._capture = cv2.VideoCapture(input_video)
            else:
                for path in self._video_paths:
                    if os.path.isfile(path + input_video):
                        self._capture = cv2.VideoCapture(path + input_video)
                        break
        else:
            # In case of a usb camera we try to access it
            try:
                self._capture = cv2.VideoCapture(int(desiredUsbInput))
                ret,frame = self._capture.read()
                auxiliarShape = frame.shape
            except Exception as e:
                print('Could not load the USB camera trying other ports')
                for sourceTrial in range(3):
                    print('Trying {}'.format(sourceTrial))
                    try:
                        self._capture = cv2.VideoCapture(sourceTrial)
                        ret,frame = self._capture.read()
                        if ret:
                            break
                        print('Success reading usb camera at {}'.format(sourceTrial))
                    except:
                        pass
        
            if self._capture:
                # In case of a usb camera we set the parameters
                self._capture.set(cv2.CAP_PROP_FPS, 30)
                if self.resolution:
                    self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        time.sleep(1.0)
            
    def full_ip_address(self):
        return self.ip_format[0] + self.ip_address_with_port + self.ip_format[1]


    def set_address_format(self, beforeIP,afterIP):
        self.ip_format = [beforeIP,afterIP]

    def addVideoRoutes(self,new_path_to_video):
        """
        In case a custom route to the videos is added for the search job
        """
        self._video_paths.append(new_path_to_video)
        return len(self._video_paths)

    @staticmethod
    def exportHistorialAsImages(pathToSave):
        contador = 0
        inicio = min(PlayStream.historial)
        final = max(PlayStream.historial)
        for indice in range(inicio,final):
            imagen = PlayStream.historial[indice]
            file_name = '/{date}_{counter}.jpg'.format( date = datetime.now().strftime('%Y%m%d_%H%M%S'),
                                                        counter = contador)
            print('saving: '+pathToSave+file_name)
            cv2.imwrite(pathToSave+file_name,imagen)
            contador += 1

    def read(self):
        """
        The most importan class tha unifies both ways of accessing the picamera and usb camera
        """
        if self._video_souce == "picamera":
            frame = self._capture.read()
            if len(frame.shape)>=1:
                ret = True
            else:
                ret = False
        elif self._video_souce == "usbcamera":
            ret, frame = self._capture.read()
        elif self._video_souce == "IPcamera":
            ret, frame = self._capture.read()
        else:
            frames_retraso = int((time.time() - self._init_time)*self.fps)
            if frames_retraso == 0:
                frames_retraso = 1
            
            for index in range(frames_retraso):
                ret, frame = self._capture.read()
                if not self.emulate_real_time:
                    # If I wish to analice all frames I skip from the first capture
                    break
            if self.resolution:
                frame = cv2.resize(frame,(self.width,self.height))
        
        if ret and self.historial_len:
            PlayStream.historial[PlayStream.frame_number] = frame.copy()
            PlayStream.frame_number += 1
            if len(PlayStream.historial) > self.historial_len:
                del PlayStream.historial[min(PlayStream.historial)]
        if not ret:
            print('Could not get any frame')
        
        # We calculate the fps:
        self.new_time = time.time()
        PlayStream.list_period.append(self.new_time-self.old_time)
        self.old_time = self.new_time
        if len(PlayStream.list_period)>10:
            PlayStream.list_period.pop(0)

        # If we are set to grayscale  we set the property
        if self.fake_gray_scale:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        return ret, frame

    def getPeriod(self):
        return sum(PlayStream.list_period)/len(PlayStream.list_period)

    def getFPS(self):
        return 1/self.getPeriod()

    def release(self):
        if not self._video_souce == "picamera":
            self._capture.release()
