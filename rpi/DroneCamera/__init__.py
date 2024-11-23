from picamera2 import Picamera2
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
camera.start()

def CameraObject() -> Picamera2:
    global camera
    return camera