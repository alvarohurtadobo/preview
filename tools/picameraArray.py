# Picamera correction form array output in spliter

# Import picamera modules
import picamera
import picamera.array
from picamera.exc import PiCameraValueError

# Import numerica lib
import numpy as np



class PiRGBAArray(picamera.array.PiRGBArray):
    ''' PiCamera module doesn't have 4 byte per pixel RGBA/BGRA version equivalent, so this inherits from the 3-bpp/RGBA/BGRA version to provide it
    '''

    def flush(self):
        self.array = self.bytes_to_rgba(self.getvalue(), self.size or self.camera.resolution)

    def bytes_to_rgba(self, data, resolution):
        ''' Converts a bytes objects containing RGBA/BGRA data to a `numpy`_ array.  i.e. this is the 4 byte per pixel version.
            It's here as a class method to keep things neat - the 3-byte-per-pixel version is a module function. i.e. picamera.array.bytes_to_rgb()
        '''
        width, height = resolution
        fwidth, fheight = picamera.array.raw_resolution(resolution)
        # Workaround: output from the video splitter is rounded to 16x16 instead
        # of 32x16 (but only for RGB, and only when a resizer is not used)
        bpp = 4
        if len(data) != (fwidth * fheight * bpp):
            fwidth, fheight = picamera.array.raw_resolution(resolution, splitter=True)
            if len(data) != (fwidth * fheight * bpp):
                raise PiCameraValueError('Incorrect buffer length for resolution %dx%d' % (width, height))
        # Crop to the actual resolution
        return np.frombuffer(data, dtype=np.uint8).reshape((fheight, fwidth, bpp))[:height, :width, :]
