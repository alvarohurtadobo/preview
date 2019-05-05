import cv2
import argparse
from time import time
from tools.fps import FPS
from threading import Thread
from playstream import PlayStream

parser = argparse.ArgumentParser(description='Perform next options')
parser.add_argument("-i", "--video_file",   type = str,  default = None,   help = "Specify optional video file")
parser.add_argument("-s", "--show",         type = bool, default = False,  help = "Show image in screen rather than server")
parser.add_argument("-k", "--autokill",     type = int,  default = 0,      help = "Self kill parameter")
parser.add_argument("-f", "--fps",          type = int,  default = 12,     help = "Optional FPS")
parser.add_argument("-W", "--width",        type = int,  default = 320,    help = "Specify optional video width")
parser.add_argument("-H", "--height",       type = int,  default = 240,    help = "Specify optional video height")
parser.add_argument("-g", "--grayscale",    type = bool, default = False,  help = "Set grayscale mode")
parser.add_argument("-d", "--debug",        type = bool, default = False,  help = "Set logging to debug")
parser.add_argument("-b", "--brightness",   type = int,  default = 50,     help = "Specify optional brightness for the camera")
parser.add_argument("-l", "--length",       type = int,  default = 10,     help = "Lenght for historial in seconds, it is adviced not to be greater than period")
args = parser.parse_args()

class ThreadStream:
    """
    This class creates a thead to acquire images from preview class
    """
    def __init__(self,  input = None,
                        resolution = None,
                        fake_gray_scale = False,
                        brightness = 50,
                        real_time = False,
                        historial_len = 0,
                        fps = 6):
        # We create the playstream class
        self.myCamera = PlayStream( input_video = input,
                                    resolution = resolution,
                                    fake_gray_scale = fake_gray_scale,
                                    brightness = brightness,
                                    real_time = real_time,
                                    historial_len = historial_len,
                                    fps = fps)
        # The variable current_frame_number will be used to see if the current frame has changed
        self._current_frame_number = 0
        self._last_time = time()
        self.last_capture_time = 0
        self.ret, self.frame = self.myCamera.read()
        self.height, self.width, self.channels = self.frame.shape
        self._low_resolution_ratio = 10
        self._low_resolution = (int(self.width/self._low_resolution_ratio),int(self.height/self._low_resolution_ratio))
        self.frame_low = cv2.resize(self.frame,self._low_resolution)
        self.running = False

    def get_frame_info(self):
        return self._current_frame_number, self.last_capture_time

    def start(self):
        # Override the start method
        self.running = True
        Thread(target = self.update, args = ()).start()
        return self 

    def update(self):
        # We keep looping the read method
        while self.running:
            self.ret, self.frame = self.myCamera.read()
            self.frame_low = cv2.resize(self.frame,self._low_resolution)
            self._current_frame_number += 1
            current_time = time()
            self.last_capture_time = current_time - self._last_time
            self._last_time = current_time

    def read(self):
        # Just pass the current values
        return self.ret, self.frame

    def read_low(self):
        # Just pass the current values
        return self.ret, self.frame_low

    def stop(self):
        # We end the update method
        self.running = False

if __name__ == "__main__":
    # print('Out: ',args.video_file)
    myThreadedStream = ThreadStream(input = args.video_file,
                                    resolution = (args.width,args.height),
                                    historial_len = args.length*args.fps,
                                    brightness = args.brightness,
                                    fake_gray_scale = args.grayscale,
                                    fps = args.fps).start()
    fps = FPS().start()

    if args.show:
        cv2.namedWindow('Threaded frame', cv2.WINDOW_NORMAL)

    old_frame_number = 0

    while True:
        ret, frame = myThreadedStream.read_low()
        number, capture_time = myThreadedStream.get_frame_info()
        print('Last frame {0}, took {1:.2f} seg'.format(number,capture_time))
        if number != old_frame_number:
            fps.update()
            old_frame_number = number
            print('Updated')
            if args.show:
                cv2.imshow('Threaded frame', frame)
        key = cv2.waitKey(1)

        if key == ord('q'):
            myThreadedStream.stop()
            break
    fps.stop()
    print("Elasped time: {:.2f}".format(fps.elapsed()))
    print("Approx.  FPS: {:.2f}".format(fps.fps()))