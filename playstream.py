"""
Simple class for using multiple inputs and multiple sources of videos with opencv and picamera
"""

import os
import cv2
import json
import time
from imutils.video import FPS
from imutils.video import VideoStream

from filestream import FileStream

class PlayStream():
    """
    This class combines all video and file inputs for camera
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
        #return self.ip_format[0] + self.input_video + self.ip_format[1]
        return self.input_video

    def set_address_format(self, beforeIP,afterIP):
        # Change IP Address
        self.ip_format = [beforeIP,afterIP]

    def addVideoRoutes(self,new_path_to_video):
        # In case a custom route to the videos is added for the search job
        self._video_paths.append(new_path_to_video)
        return len(self._video_paths)

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
        elif self._video_souce == "image_folder":
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