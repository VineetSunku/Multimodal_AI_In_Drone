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
        ground.send(str({'level': level, 'message': message}).encode())

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
    try:
        await uav.connect(system_address="serial:///dev/ttyAMA0:57600")
        async for state in uav.core.connection_state():
            if state.is_connected:
                log.info("Connected to UAV")
                await asyncio.sleep(2)
                break
    except Exception as e:
        log.error(f"Failed to connect to Drone: {e}")
    
def receive():
    log.info("Now receiving inputs")
    while True:
        try:
            d=eval(ground.recv(1024).decode())
            if d['messageType'] == "Controller":
                keyDir = d['message']
                if keyDir == "takeoff":
                    log.info("Initiating Takeoff sequence")
                    asyncio.run(arm_and_takeoff(uav, 2.5))
                elif keyDir =="land":
                    asyncio.run(land_uav(uav))
                elif keyDir == "ld":
                    asyncio.run(adjust_yaw(uav, "left"))
                elif keyDir == "rd":
                    asyncio.run(adjust_yaw(uav, "right"))
                elif keyDir == "ud":
                    asyncio.run(adjust_throttle(uav, 0.8))
                elif keyDir == "dod":
                    asyncio.run(adjust_throttle(uav, 0.4))
                elif keyDir == "wd":
                    asyncio.run(adjust_pitch(uav, -20))
                elif keyDir == "sd":
                    asyncio.run(adjust_pitch(uav, 20))
                elif keyDir == "ad":
                    asyncio.run(adjust_roll(uav, -20))
                elif keyDir == "dd":
                    asyncio.run(adjust_roll(uav, 20))
                else:
                    asyncio.run(stop_offboard(uav))
            elif d["messageType"] == "AI":
                gen_code = d["message"]
                exec(gen_code)       
        except Exception as e:
            print("Main Socket Connection Closed", e)
            break

def videoStream():
    log.info("Now sending video")
    try:
        while True:
            frame = camera.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            ground_video.sendall(len(frame).to_bytes(4, 'big'))
            ground_video.sendall(frame)
    except Exception as e:
        print(f"Video Socket Connection Closed: {e}")

async def telemetryStream():
    log.info("Now sending Telemetry data")
    while True:
        # try:
        global lat,lon,alt
        lat, lon, alt = await get_coord(uav)
        tel = {'lat': lat, 'lon': lon, 'alt': alt}
        byte_tel = struct.pack('>ddd', tel['lat'], tel['lon'], tel['alt'])
        # ground_tel.sendall(byte_tel)
        await asyncio.sleep(1)
        # except Exception as e:
        #     print(f"Error in Telemetry streaming: {e}")
        #     break

# def runtelemetryStream(looop: asyncio.unix_events._UnixSelectorEventLoop):
#     asyncio.run_coroutine_threadsafe(telemetryStream(), loop=looop)

async def main():
    global uav, log, ground, ground_video, camera
    uav = System()
    log = Logger()

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

    # ground_tel, addr_tel = rpi_tel.accept()
    # ground_tel.send("Telemetry Socket Established".encode())

    ######### CAMERA #########
    camera = Picamera2()
    camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    camera.start()

    #################
    
    await connect_to_uav()
    
    # teltask = asyncio.create_task(telemetryStream())
    
    t1=Thread(target=receive)
    t2 = Thread(target=videoStream)
    t1.start()
    t2.start()
    # log.info("Is this the last message?")
    # await teltask
    # log.info("or Is this the last message?")


if __name__ == "__main__":
    asyncio.run(main())
