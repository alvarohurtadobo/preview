import cv2
import requests
import numpy as np

class ServerController():
    #Configs for server
    addr = 'http://localhost:5000'
    test_url = addr + '/get_images'
    content_type = 'image/jpeg'
    headers = {'content-type': content_type}


    def __init__(self):
        pass
        # self.configs_server = [False,False]

    def sendImageIfAllowed(self,imageToSend):
        try:
            _, img_encoded = cv2.imencode('.jpg', imageToSend)
            r = requests.post(ServerController.test_url, data=img_encoded.tostring(), headers=ServerController.headers)
        except Exception as e:
            print('<SERVER ERROR> Cannot send images to server, This happen, '+ str(e))
 