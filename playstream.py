"""
Simple class for using multiple inputs and multiple sources of videos with opencv and picamera
"""

import os
import cv2
import json
import time
import logging
import statistics

from filestream import FileStream
from multistream import MultiStream

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

        self.input_video = input_video
        self.resolution = resolution
        self.gray_scale = fake_gray_scale
        self.brightness = brightness
        self.real_time = real_time
        self.historial_len = historial_len
        self.fps = fps

        # Auxiliar Variables:
        self.last_time = time.time()
        self.old_time = self.last_time

        if self.input_video:
            if not self.input_video.isdigit() and os.path.exists(self.input_video):
                self.camera = FileStream(path_to_file = self.input_video, fps = self.fps)
            else:
                self.camera = MultiStream(  input_video = self.input_video,
                                            resolution = self.resolution,
                                            gray_scale = self.gray_scale,
                                            brightness = self.brightness)

        self.received_resolution = self.camera.received_resolution

    def read(self):
        """
        The most importan class tha unifies both ways of accessing the picamera and usb camera
        """
        # We look for changes every 3 seconds:
        if os.getenv('changed') == 'True':
            self.set_brightness(int(os.getenv('brightness')))
            if os.getenv('gray') == True:
                self.set_grayscale()
            else:
                self.set_color()
            os.system('export changed=False')

        ret, frame = self.camera.read()

        # We generate the new historial:
        if ret and self.historial_len:
            PlayStream.historial[PlayStream.frame_number] = frame.copy()
            PlayStream.frame_number += 1
            if len(PlayStream.historial) > self.historial_len:
                del PlayStream.historial[min(PlayStream.historial)]
        if not ret:
            raise Exception('Could no longer get any frame')
        
        # We calculate the fps:
        self.new_time_for_fps = time.time()
        PlayStream.list_period.append(self.new_time_for_fps-self.old_time)
        self.old_time = self.new_time_for_fps

        # We make use of the las 10 periods only
        if len(PlayStream.list_period)>30:
            PlayStream.list_period.pop(0)

        return ret, frame

    def set_brightness(self,new_brightness):
        # Set the brightness only for the pi camera
        self.camera.set_brightness(new_brightness)

    def set_grayscale(self):
        # Set grayscale to true, by now only averaging the channels
        self.camera.set_grayscale()

    def set_color(self):
        # Set color to RBG
        self.camera.set_color()

    def release(self):
        self.camera.release()

    # Calculations
    def getPeriod(self):
        return sum(PlayStream.list_period)/len(PlayStream.list_period)

    def getStandarDeviation(self):
        return statistics.stdev(PlayStream.list_period)

    def getFPS(self):
        return 1/self.getPeriod()

    def generateVideo(self,directory):
        current_video = directory + '.avi'
        logging.info('Saving video: {} with len: {}, fps:{} and resolution: {}'.format(current_video,len(PlayStream.historial),self.fps,self.received_resolution))
        aEntregar = cv2.VideoWriter(current_video,PlayStream.fourcc, self.fps, self.received_resolution)

        for index,frame in PlayStream.historial.items():
            try:
                aEntregar.write(frame)
            except Exception as e:
                logging.info('Problem with frame {} because of {}'.format(index,e))
        aEntregar.release()

        #os.system('ffmpeg -i {} {}.mp4'.format(nombreVideo,nombreVideo[:-4]))
        #os.system('rm {}'.format(nombreVideo))

    def exportHistorialAsImages(self,pathToSave):
        contador = 0
        inicio = min(PlayStream.historial)
        final = max(PlayStream.historial)
        logging.info('Saving images in: ' + pathToSave)
        if not os.path.exists(pathToSave):
            os.makedirs(pathToSave)
        for indice in range(inicio,final):
            imagen = PlayStream.historial[indice]
            file_name = '/{counter}.jpg'.format(counter = contador)
            cv2.imwrite(pathToSave+file_name,imagen)
            contador += 1