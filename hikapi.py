from hikvisionapi import Client

cam = Client('http://192.168.1.2','admin','DeMS2018')

response = cam.System.deviceInfo(method='get')

print(type(response))
print(response)

motion_detection_info = cam.System.Video.inputs.channels[1].motionDetection(method='get')

print(motion_detection_info)

# Get and save picture from camera            
response = cam.Streaming.channels[1].picture(method='get', type='opaque_data')
print(type(response))
print(response)
print('Here comes the iter')
with open('./screen.jpg', 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024):
        print(chunk)
        if chunk:
            f.write(chunk)    
