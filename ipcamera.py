import cv2
import time
import base64
import requests
import numpy as np

"""
Examples of objects for image frame aquisition from both IP and
physically connected cameras
Requires:
 - opencv (cv2 bindings)
 - numpy
"""

class IPCamera(object):

    def __init__(self, url, user=None, password=None):
        self.url = url
        #auth_encoded = base64.encodestring('%s:%s' % (user, password))[:-1]

        self.req = requests.get(self.url,stream = True)
        #self.req.add_header('Authorization', 'Basic %s' % auth_encoded)

    def read(self):
        response = requests.urlopen(self.req)
        img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_array, 1)
        return True, frame

    def release(self):
        pass