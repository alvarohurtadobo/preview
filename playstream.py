"""
Simple class for using multiple inputs and multiple sources of videos with opencv and picamera
"""

import os
import cv2
import json
import time
import logging
import statistics
import multiprocessing

from filestream import FileStream
from multistream import MultiStream

class PlayStream(multiprocessing.Process):
    """
    This class combines all video and file inputs for camera
    """
    historial = {}
    frame_number = 0
    list_period = []
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    def __init__(self,  input_video = None,
                        resolution = None,
                        fake_gray_scale = False,
                        brightness = 50,
                        real_time = False,
                        historial_len = 0,
                        fps = 6,
                        in_pipe = None):
        self.in_pipe = in_pipe
        if self.in_pipe:
            super(PlayStream, self).__init__()

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

        self.known_paths = [os.getenv('SOURCE_VIDEO_PATH')+'/']

        if self.input_video:
            complete_file_path = self.verify_file_path(self.input_video)
            if not self.input_video.isdigit() and complete_file_path:
                
                # If resolution set up manually we force the given resolution
                # None means the natural given resolution
                self.camera = FileStream(   path_to_file = complete_file_path,
                                            fps = self.fps,
                                            resolution = self.resolution,
                                            gray_scale = self.gray_scale)
            else:
                # Cleaning input, when launched from server uses to add a space, leading to errors:
                self.input_video = self.input_video.replace(" ","")
                self.camera = MultiStream(  input_video = self.input_video,
                                            resolution = self.resolution,
                                            gray_scale = self.gray_scale,
                                            brightness = self.brightness)
        else:
            # if no source is selected by default we set the Pi camera:
            self.camera = MultiStream(  input_video = self.input_video,
                                        resolution = self.resolution,
                                        gray_scale = self.gray_scale,
                                        brightness = self.brightness)


        self.received_resolution = self.camera.received_resolution
        #print('Given resolution {}, received resolution {}'.format(self.resolution,self.received_resolution))

    def run(self):
        """
        Main function to run in parallel
        :return: Nothing
        """
        # Start the main process
        while True:
            ret, image = self.read()
            image = "hola"
            self.in_pipe.send((ret,image))
            time.sleep(2)

    def add_file_path(self,new_folder):
        self.known_paths.append(new_folder+'/')

    def verify_file_path(self,file_name):
        if os.path.exists(self.input_video):
            return self.input_video

        for path in self.known_paths:
            if os.path.exists(path + file_name):
                return path + file_name
        return None

    def read(self):
        """
        The most importan class tha unifies both ways of accessing the picamera and usb camera
        """
        # We look for changes every 3 seconds:
        #print('READ {}, len {}'.format(os.getenv('changed'),len(os.getenv('changed'))))
        if os.getenv('changed') == 'True':
            self.set_brightness(int(os.getenv('brightness')))
            #print('\tchanged')
            if os.getenv('gray') == True:
                self.set_grayscale()
                #print('\t\tSet gray')
            else:
                self.set_color()
                #print('\t\tSet rgb')
            os.environ['changed'] = 'False'

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
                logging.error('Problem with frame {}'.format(index), exc_info=True)
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