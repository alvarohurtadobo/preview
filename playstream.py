"""
Simple class for using multiple inputs and multiple sources of videos with opencv and picamera
"""

import os
import cv2
import json
import time
from imutils.video import FPS
from imutils.video import VideoStream

#from ipcamera import IPCamera

class ImageCapture():
    def __init__(self,path_to_image):
        self.path_to_image = path_to_image
        if os.path.isfile(self.path_to_image):
            self.ret = True 
        else:
            self.ret = False
        self.image = cv2.imread(self.path_to_image)
        print('Read image size: ',self.image.shape)
        self.camera = None
        

    def read(self):
        self.image = cv2.imread(self.path_to_image)
        return self.ret, self.image

    def set(self,parameter,variable):
        pass


class PlayStream():
    """
    This class combines file, usbcamera and picamera inputs
    """
    historial = {}
    frame_number = 0
    list_period = []
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    
    def __init__(self,  input_video = None,
                        resolution = (320,240),
                        fake_gray_scale = False,
                        brightness = 50,
                        real_time = False,
                        historial_len = 0,
                        fps = 6):
        """
        The class is started with a "input_video" in case of a file and a USB camera or None with picamera
        The default resolution is 320x240 and can be changed as resolution = (w,h)
        """
        # General settings
        self.fps = fps
        self.home_route = os.getenv('HOME')

        # Timing variables settings
        self._init_time = time.time()
        self.last_time = self._init_time 
        self.new_time_for_fps = time.time()
        self.old_time = self.new_time_for_fps
        self.emulate_real_time = real_time

        # Config settings
        self.fake_gray_scale = fake_gray_scale
        self.brightness = brightness
        self.width = None
        self.height = None

        self.historial_len = historial_len*self.fps
        if self.historial_len < 0:
            self.historial_len = 0

        self.normalPeriod = True

        # Main variables
        self._capture = None
        
        if resolution:
            self.resolution = resolution
            self.width = resolution[0]
            self.height = resolution[1]
        
        self._video_souce = "pi_camera"                      # Can be "pi_camera", "usbcamera" or "video_file"

        # File paths:
        self._video_paths = [self.home_route+'/trafficFlow/trialVideos/']
        self._image_paths = [self.home_route+'/trafficFlow/prototipo/installationFiles/']

        # IP camera settings
        self.ip_format = ['rtsp://admin:DeMS2018@','/Streaming/channels/1/preview']    # rtsp://admin:DeMS2018@192.168.1.2:554/Streaming/channels/1
        #self.ip_format = ['rtsp://pi:dems@','/']    # rtsp://admin:DeMS2018@192.168.1.2:554/Streaming/channels/1

        self.input_video = input_video
        # We first define the nature of the input

        # If not stated otherwise we use the pi camera:
        if not self.input_video:
            self._video_souce = "pi_camera"
        else:
            # Let's remove the undesired characters:
            self.input_video = self.input_video.replace(' ','')       # Remove when updated validators
            if '.mp4' in self.input_video or '.avi' in self.input_video:
                self._video_souce = "video_file"
            elif '.png' in self.input_video or '.jpg' in self.input_video:
                self._video_souce = "image_file"
            else:
                # A IP source must have three points and maybe a colon:
                number_of_dots = len(self.input_video.split('.')) - 1
                if number_of_dots == 3:
                    self._video_souce = "IP_camera"
                else:
                    try:
                        desiredUsbInput = int(input_video)
                        self._video_souce = "usbcamera"
                    except:
                        self._video_souce = "video_file"
        
        print('[INFO STREAM]:',self._video_souce,'source selected')

        if self._video_souce == "pi_camera":
            #we introduce the picamera libraries
            try:
                if resolution:
                    self._capture  = VideoStream(usePiCamera=True, resolution=self.resolution).start()
                else:
                    self._capture  = VideoStream(usePiCamera=True).start()
            except Exception as e:
                print('Could not access any picamera, error: '+str(e))
            try:
                self._capture.camera.brightness = self.brightness
            except:
                print('Could not set brightness to {}'.format(self.brightness))
        elif self._video_souce == "IP_camera":
            self._capture = cv2.VideoCapture(self.full_ip_address())
            #self._capture = IPCamera(self.full_ip_address())
        elif self._video_souce == "video_file":
            # In case of a file we try all possible locations for the file
            if os.path.isfile(input_video):
                self._capture = cv2.VideoCapture(input_video)
            else:
                for path in self._video_paths:
                    if os.path.isfile(path + input_video):
                        self._capture = cv2.VideoCapture(path + input_video)
                        break
        elif self._video_souce == "image_file":
            # In case of a file we try all possible locations for the file
            if os.path.isfile(input_video):
                self._capture = ImageCapture(input_video)
            else:
                for path in self._image_paths:
                    if os.path.isfile(path + input_video):
                        print('Tried ',path + input_video)
                        self._capture = ImageCapture(path + input_video)
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

    def set_brightness(self,new_brightness):
        # Set the brightness only for the pi camera
        self.brightness = new_brightness
        if self._video_souce == "pi_camera":
            self._capture.camera.brightness = self.brightness

    def set_grayscale(self):
        # Set grayscale to true, by now only averaging the channels
        self.fake_gray_scale = True

    def set_color(self):
        # Set color to RBG
        self.fake_gray_scale = False
            
    def full_ip_address(self):
        # Create IP address
        return self.ip_format[0] + self.ip_address_with_port + self.ip_format[1]

    def set_address_format(self, beforeIP,afterIP):
        # Change IP Address
        self.ip_format = [beforeIP,afterIP]

    def addVideoRoutes(self,new_path_to_video):
        # In case a custom route to the videos is added for the search job
        self._video_paths.append(new_path_to_video)
        return len(self._video_paths)

    def addImageRoutes(self,new_path_to_images):
        # In case a custom route to the videos is added for the search job
        self._image_paths.append(new_path_to_images)
        return len(self._image_paths)

    def read(self):
        """
        The most importan class tha unifies both ways of accessing the picamera and usb camera
        """
        # We look for changes every 3 seconds:
        if time.time() - self.last_time > 4:
            self.last_time = time.time()
            new_configs = {}
            expected_configs_file_name = '{home}/configs/configs.json'.format(home = self.home_route)
            
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
        elif self._video_souce == "image_file":
            ret, frame = self._capture.read()
        elif self._video_souce == "usbcamera":
            ret, frame = self._capture.read()
        elif self._video_souce == "IP_camera":
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
        self.new_time_for_fps = time.time()
        if self.normalPeriod:
            # If we did not generate video or images we append the period to compute the fps
            PlayStream.list_period.append(self.new_time_for_fps-self.old_time)
        else:
            self.normalPeriod = True
        self.old_time = self.new_time_for_fps
        if len(PlayStream.list_period)>10:
            PlayStream.list_period.pop(0)

        # If we are set to grayscale  we set the property
        if self.fake_gray_scale:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        frame.setflags(write=True)
        return ret, frame

    def getPeriod(self):
        return sum(PlayStream.list_period)/len(PlayStream.list_period)

    def getFPS(self):
        return 1/self.getPeriod()

    def release(self):
        if not self._video_souce == "pi_camera":
            self._capture.release()

    def generateVideo(self,directory):
        current_video = directory + '.avi'
        print('Saving video: ' + current_video)
        aEntregar = cv2.VideoWriter(current_video,PlayStream.fourcc, self.fps,self.resolution)

        for index,frame in PlayStream.historial.items():
            try:
                aEntregar.write(frame)
            except Exception as e:
                print('Problem with frame {} because of {}'.format(index,e))
        aEntregar.release()
        self.normalPeriod = False
        #os.system('ffmpeg -i {} {}.mp4'.format(nombreVideo,nombreVideo[:-4]))
        #os.system('rm {}'.format(nombreVideo))

    def exportHistorialAsImages(self,pathToSave):
        contador = 0
        inicio = min(PlayStream.historial)
        final = max(PlayStream.historial)
        print('Saving images in: ' + pathToSave)
        if not os.path.exists(pathToSave):
            os.makedirs(pathToSave)
        for indice in range(inicio,final):
            imagen = PlayStream.historial[indice]
            file_name = '/{counter}.jpg'.format(counter = contador)
            cv2.imwrite(pathToSave+file_name,imagen)
            contador += 1
        self.normalPeriod = False