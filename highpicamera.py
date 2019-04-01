import os


class HighPiCamera():


    def __init__(   self,
                    width = 2560,
                    height = 1920):


        self.frame_stream = self.camera.capture_continuous( self._frame_output,
                                                                format="bgra",
                                                                use_video_port=True,
                                                                splitter_port=2,
                                                                resize=(self._width,self._height))