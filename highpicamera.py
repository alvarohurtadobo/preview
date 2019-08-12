#!/usr/bin/env python3

import os
import cv2
import time
import logging

class HighPiCamera():
    """
    This class uses the standar Picamera class and emulates the standar opencv read method with no problem at hight resolutions
    Currently because of hardware limitations only 5Mp resolution is opssible
    """
    high_source = os.getenv('SOURCE_FOLDER_PATH')

    def __init__(   self,
                    width = 2560,
                    height = 1920,
                    framerate = 2,
                    emulate = None):

        # Setting the parameters:
        if width == 0 or height == 0:
            self._width = 2560
            self._height = 1920
        else:
            self._width = width
            self._height = height
        self.framerate = framerate
        self.video_port = True
        self._emulate = emulate

        # Auxiliar Variables:
        self._frame_output = None

        try:
            import picamera 
            from tools.picameraArray import PiRGBAArray
        except Exception as e:
            if (os.uname()[1][:5].lower() == 'lucam'):
                logging.info('Could not load picamera in Camera because of {}, is Pi Camera available?'.format(e))
            else:
                logging.info('Could not load picamera in computer, emulating picamera')
                self._emulate = HighPiCamera.high_source 

        # Building the objects:
        if self._emulate:
            self.camera = PiCameraEmulator(self._emulate)
            self.frame_stream = self.camera
            logging.info('Started in Emulated mode')
        else:
            self.camera = picamera.PiCamera(resolution = (self._width,self._height),
                                            framerate  = 2)

            self.camera.exposure_mode = 'sports'

            self._frame_output = PiRGBAArray(   self.camera,
                                                size = (self._width,self._height))

            self.frame_stream = self.camera.capture_continuous( self._frame_output,
                                                                format="bgra",
                                                                use_video_port=self.video_port,
                                                                splitter_port=2,
                                                                resize=(self._width,self._height))
            logging.info('Started in PiCamera Mode')

    def read(self):
        try:
            if not self._emulate:
                image_object = self.frame_stream.__next__()
                current_image = image_object.array
                # Truncate low res frame
                self._frame_output.truncate(0)
            else:
                current_image = self.frame_stream.__next__()
            ret = True
        except Exception as e:
            logging.info('Had next problem: {}'.format(e))
            ret = False
        return ret, current_image




class PiCameraEmulator():
    """
    General PICAMERA Emulator in for trials in a computer other that the raspberry pi
    """

    path_to_image_folder = os.getenv('SOURCE_FOLDER_PATH')

    def __init__(self, path_to_high_resolution_images = 'None'):
        # Private attributes:
        self._number_of_images = 0
        self._counter = 0

        # Public attributes:
        self.zoom = (0,0,0,0)
        self.exposure_mode = ""

        if path_to_high_resolution_images:
            self.change_pictures_folder(path_to_high_resolution_images)
        else:
            self.change_pictures_folder(PiCameraEmulator.path_to_image_folder)

    def change_pictures_folder(self, new_folder):
        self._list_of_images = sorted([image for image in os.listdir(new_folder) if '.jpg' in image or '.png' in image])
        self._number_of_images = len(self._list_of_images)
        self._counter = 0
        #print('Loaded: {} with {} images'.format(new_folder,self._number_of_images))

    def __next__(self):
        path_to_image = PiCameraEmulator.path_to_image_folder + '/' + self._list_of_images[self._counter%self._number_of_images]
        self._counter += 1
        image = cv2.imread(path_to_image)
        return image
