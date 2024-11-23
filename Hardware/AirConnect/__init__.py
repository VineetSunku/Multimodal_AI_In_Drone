import socket
from DroneLogger import log
import os
from enum import Enum
import threading
import struct, cv2, numpy as np
from datetime import datetime

######### GLOBAL VARIABLES #########
corrected_frame = cv2.imread("./static/received_frame.jpg")

######### SOCKET MESSAGE CLASS #########
# Define Sender and Type enums
class Sender(Enum):
    GROUND = "Ground"

class GroundType(Enum):
    CONTROLLER = "Controller"
    AI = "AI"

class SocketMessage(dict):
    def __init__(self, sender: Sender, messageType: GroundType, message: str) -> None:
        # Validate the 'sender' and 'type' relationship
        if sender == Sender.GROUND and not isinstance(messageType, GroundType):
            raise TypeError("For 'Ground' sender, type must be 'Controller' or 'AI'.")

        self.sender = sender.value
        self.messageType = messageType.value
        self.message = message
        
    def __str__(self):
        """Custom string representation for readability."""
        return f"{{'sender':'{self.sender}', 'messageType':'{self.messageType}', 'message':'{self.message}'}}"

######### RPi CONNECTIONS #########

# RPI_IP = os.environ['RPI_IP2']
RPI_IP = "192.168.208.38"
camera_frame = bytes(45)

#Computer to RPi socket initialize
ground = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ground.settimeout(30)
try:
    log.debug("Connecting to RaspberryPi")
    ground.connect((RPI_IP, 4682))
    log.info("Connected to RaspberryPi. It says: " + ground.recv(1024).decode())
except (socket.timeout, ConnectionRefusedError, OSError) as e:
    log.error(f"Couldn't connect to RaspberryPi: {e}")

#Second Socket for video
ground_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    ground_video.connect((RPI_IP, 3461))
    log.info("Receiving video from Rpi: " + ground_video.recv(1024).decode())
except (socket.timeout, ConnectionRefusedError, OSError) as e:
    log.error(f"Couldn't receive video from air: {e}")

######### PRIMARY CONNECTION FUNCTIONS #########        
def SendToAir(message: SocketMessage):
    ground.send(str(message).encode())

######### RECEIVE VIDEO #########
def receiveExactBytes(sock: socket.socket, size):
    """Receive exactly `size` bytes from the socket."""
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))  # Get the remaining bytes
        data += packet
    return data

def receive_frames():
    """Generator that receives frames and yields them as JPEG data."""
    global corrected_frame
    while True:
        try:
            frame_size_data = ground_video.recv(4)

            frame_size = struct.unpack('>I', frame_size_data)[0]
            frame_data = receiveExactBytes(ground_video, frame_size)
            np_array = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            corrected_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _,buffer=cv2.imencode('.jpg',corrected_frame)
            frame_data = buffer.tobytes()
            global camera_frame
            camera_frame = (b'--frame\r\n'
                    b'Content-Type: image/jpg\r\n\r\n' + frame_data + b'\r\n')
            
        except Exception as e:
            print(f"Error receiving frame: {e}")
            break

threading.Thread(target=receive_frames, daemon=True).start()

def CameraFrame():
    global camera_frame
    while True:
        yield camera_frame

def save_screenshot():
    """Saves a screenshot of the current camera frame with a timestamp-based filename."""
    global corrected_frame
    img = corrected_frame


    # Extract the JPEG-encoded image data from the camera frame

    # Generate a filename with the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{timestamp}.jpg"

    # Save the image
    os.chdir('./logs/images')
    cv2.imwrite(filename, img)
    log.info(f"Screenshot saved as {filename}")
    os.chdir('../../')

    return "./logs/images/" + filename 