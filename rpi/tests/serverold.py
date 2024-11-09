import socket
from threading import Thread
from picamera2 import Picamera2
import cv2
import os
import asyncio
from DroneFunctions import *
import struct

######### LOGGING #########
class Logger:
    def __init__(self):
        pass

    def _send(self, level: str, message: str) -> None:
        """Private method to send the log message."""
        print(level + ":", message)
        # ground.send(str({'level': level, 'message': message}).encode())

    def info(self, message: str) -> None:
        self._send("INFO", message)

    def warning(self, message: str) -> None:
        self._send("WARNING", message)

    def error(self, message: str) -> None:
        self._send("ERROR", message)

    def debug(self, message: str) -> None:
        self._send("DEBUG", message)

######### UAV CONNECTIONS ######### 

async def connect_to_uav():
    await uav.connect(system_address="serial:///dev/ttyAMA0:57600")
    async for state in uav.core.connection_state():
        if state.is_connected:
            log.info("Connected to UAV")
            await asyncio.sleep(2)
        
def receive(loop):
    while True:
        try:
            d=eval(ground.recv(1024).decode())
            if d['messageType'] == "Controller":
                keyDir = d['message']
                if keyDir == "takeoff":
                    log.info("Initiating Takeoff sequence")
                    asyncio.run_coroutine_threadsafe(arm_and_takeoff(uav, 2.5), loop)
                elif keyDir =="land":
                    asyncio.run_coroutine_threadsafe(land_uav(uav), loop)
                elif keyDir == "ld":
                    asyncio.run_coroutine_threadsafe(adjust_yaw(uav, "left"), loop)
                elif keyDir == "rd":
                    asyncio.run_coroutine_threadsafe(adjust_yaw(uav, "right"), loop)
                elif keyDir == "ud":
                    asyncio.run_coroutine_threadsafe(adjust_throttle(uav, 0.8), loop)
                elif keyDir == "dod":
                    asyncio.run_coroutine_threadsafe(adjust_throttle(uav, 0.4), loop)
                elif keyDir == "wd":
                    asyncio.run_coroutine_threadsafe(adjust_pitch(uav, -20), loop)
                elif keyDir == "sd":
                    asyncio.run_coroutine_threadsafe(adjust_pitch(uav, 20), loop)
                elif keyDir == "ad":
                    asyncio.run_coroutine_threadsafe(adjust_roll(uav, -20), loop)
                elif keyDir == "dd":
                    asyncio.run_coroutine_threadsafe(adjust_roll(uav, 20), loop)
                else:
                    asyncio.run_coroutine_threadsafe(stop_offboard(uav), loop)
            elif d["messageType"] == "AI":
                gen_code = d["message"]
                exec(gen_code)       
        except Exception as e:
            print("Main Socket Connection Closed", e)
            break

def run_inloop(task):
    print("trying")
    asyncio.run_coroutine_threadsafe(task, mainLoop)

def videoStream():
    try:
        while True:
            frame = camera.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            ground_video.sendall(len(frame).to_bytes(4, 'big'))
            ground_video.sendall(frame)
    except:
        print("Video Socket Connection Closed")

async def telemetryStream():
    while True:
        global lat,lon,alt
        lat, lon, alt = await get_coord(uav)
        tel = {'lat': lat, 'lon': lon, 'alt': alt}
        byte_tel = struct.pack('>ddd', tel['lat'], tel['lon'], tel['alt'])
        ground_tel.sendall(byte_tel)
        await asyncio.sleep(1)

def run_telemetry_stream():
    try:
        asyncio.run(telemetryStream())
    except Exception as e:
        print("Telemtry Socket Connection Closed", e)
    
if __name__ == "__main__":
    uav = System()

    # RPI_IP = os.environ['RPI_IP2']
    RPI_IP = "192.168.208.38"


    rpi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rpi.bind((RPI_IP, 4682))
    rpi.listen(1)

    ground, addr = rpi.accept()
    ground.send(f'Primary link established. You are {addr}'.encode())

    rpi_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rpi_video.bind((RPI_IP, 3461))
    rpi_video.listen(1)

    ground_video, addr_video = rpi_video.accept()
    ground_video.send("Video link established".encode())

    rpi_tel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rpi_tel.bind((RPI_IP, 3441))
    rpi_tel.listen(1)

    ground_tel, addr_tel = rpi_tel.accept()
    ground_tel.send("Telemetry Socket Established".encode())

    ######### CAMERA #########
    camera = Picamera2()
    camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    camera.start()

    #################

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    t0 = Thread(target=loop.run_forever)
    t0.start()
    t1=Thread(target=receive, args=(loop,))
    t2 = Thread(target=videoStream)
    t3 = Thread(target=run_telemetry_stream)
    t1.start()
    t2.start()
    log = Logger()
    mainLoop = asyncio.new_event_loop()
    mainLoop.run_until_complete(connect_to_uav())
    t3.start()