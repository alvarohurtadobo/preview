"""
Simple class to emulate stream from a file or folder
"""

import os
import cv2
import time
import logging

class FileStream():
    """
    Emulates stream from a file (.avi, .jpg) or folder of images ()
    """

    def __init__(self,  path_to_file,
                        fps = 30,
                        resolution = None):
        # We store the provided values
        self.path_to_file = path_to_file
        self.fps = fps
        self.period = 1/self.fps
        self.resolution = resolution

        # Fundamental Variables
        self.type = ""                                  # can Be Image, Video or Folder
        self.ret = False
        self.camera = None
        self.rgb_scale = 1

        # Auxiliar Variables
        self.frames = []
        self._last_time = time.time()
        self.original_fps = self.fps
        self._jump_frames = 1
        auxiliar_jump_frames = int(self.original_fps/self.fps)
        if auxiliar_jump_frames:
            self._jump_frames = auxiliar_jump_frames

        # Check if the file exists
        if not os.path.exists(self.path_to_file):
            raise Exception('No file or folder introduced, verify the path provided')

        # Find out what type of recording we are doing
        if os.path.isfile(self.path_to_file):
            if ".avi" in self.path_to_file or ".mp4" in self.path_to_file:
                self.type = "video"
                self.camera = cv2.VideoCapture(self.path_to_file)
                self.original_fps = self.camera.get(cv2.CAP_PROP_FPS)
                # self.ret = True       # The video may be corrupt so this value should keep to false
            elif ".jpg" in self.path_to_file or ".jpeg" in self.path_to_file or ".png" in self.path_to_file:
                self.type = "image"
                self.ret = True
            else:
                raise Exception("The file seems not to be an image nor a video, please check")
        else:
            if os.path.isdir(self.path_to_file):
                self.type = "folder"
                # self.ret = True       # The folder may be empty so this value should keep to false
                self.frames = [image for image in os.listdir(self.path_to_file) if '.jpg' in image or 'png' in image]
                self.frames = sorted(self.frames)
                if len(self.frames) == 0:
                    raise Exception("Empty folder provided")
            else:
                raise Exception("The path exists but does not fit with any format used by this class")

        self.ret, self.frame = self.read()
        self.shape = self.frame.shape

        logging.info('[INFO STREAM]: Emulating {} with size: {}'.format(self.type,self.shape))

    def read(self):
        if self.type == 'image':
            self.frame = cv2.imread(self.path_to_file,self.rgb_scale)
        elif self.type == 'video':
            # We emulate jumping frames to match the required fps:
            for i in range(self._jump_frames):
                self.ret, self.frame = self.camera.read()
            if self.rgb_scale == 0:
                self.frame = cv2.cvtColor(self.frame, cv2.BGR2GRAY)
        elif self.type == 'folder':
            # We loop in the images of the folder
            current_image_path = self.frames.pop(0)
            # We read them
            self.frame = cv2.imread(self.path_to_file+'/'+current_image_path,self.rgb_scale)
            self.frames.append(current_image_path)
            # If we receive something the read was done successful
            self.ret = False
            if self.frame.any():
                self.ret = True

        if self.resolution:
            # Normally resolution is set to None, otherwise we force the image to be set to this (w,h)
            self.frame = cv2.resize(self.frame,self.resolution)

        # We emulate the desired fps:
        while time.time() - self._last_time < self.period:
            True
        self._last_time = time.time()
        return self.ret, self.frame

    def set(self,parameter,variable):
        pass
    
    def set_brightness(self,new_brightness):
        logging.info('This feature is to be updated')

    def set_grayscale(self):
        self.rgb_scale = 0
        logging.info('Changed to read files in grayscale')

    def set_color(self):
        self.rgb_scale = 1
        logging.info('Changed to read files in rgb')

    def release(self):
        pass
